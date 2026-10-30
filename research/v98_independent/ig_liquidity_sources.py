#!/usr/bin/env python3
"""IG preregistered native quote-impact composed seven-slot causal source.

No IF/other rejected signal import, no 2025+, no paper or live execution.
Completed t close -> actual t+1 open. Pre-PnL contract:
ig_liquidity_impact_prereg_20261027.md.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"CAPITULATION":.62,"ACCUMULATION":.74,"NORMAL":.70}
PRIOR={"CAPITULATION":np.array([.56,.12,.14,.18]),
       "ACCUMULATION":np.array([.50,.20,.18,.12]),
       "NORMAL":np.array([.58,.16,.14,.12])}

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IG_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.75).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IG_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IG_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U14")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n72=net(t,72);n672=net(t,672)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        core=np.exp(np.clip(n672/(np.sqrt(672.)*semi),-2.,2.))
        signals[t,0]=core/core.sum()
        quote_window=q[t-335:t+1]
        ranges=np.log(h[t-335:t+1]/l[t-335:t+1])
        valid=bool(np.isfinite(quote_window).all() and
                   np.all(quote_window>0) and
                   np.isfinite(ranges).all() and np.all(ranges>0))
        validity[t,1:]=valid
        regime="NORMAL"
        if valid:
            quote_recent=quote_window[-72:].mean(axis=0)
            quote_prior=quote_window[:-72].mean(axis=0)
            range_recent=ranges[-72:].mean(axis=0)
            range_prior=ranges[:-72].mean(axis=0)
            quote_ratio=np.clip(quote_recent/quote_prior,.25,4.)
            range_ratio=np.clip(range_recent/range_prior,.25,4.)
            absorption=np.log(quote_ratio)-np.log(range_ratio)
            ratio=np.clip(quote_window[-72:]/quote_window.mean(axis=0),.25,4.)
            impact=(np.log(c[t-71:t+1]/o[t-71:t+1])/np.sqrt(ratio)).mean(axis=0)
            capitulation=bool(np.count_nonzero(n72<0)>=3 and
                              np.median(quote_ratio)>1.25)
            if capitulation:regime="CAPITULATION"
            elif np.count_nonzero(n72>0)>=3 and np.median(absorption)>0:
                regime="ACCUMULATION"
            opportunity=absorption+.25*n72
            signals[t,1,int(np.argmax(opportunity))]=1.
            loidx=int(np.argmin(impact))
            hiidx=int(np.argmax(np.where(np.arange(4)==loidx,-np.inf,impact)))
            signals[t,2,loidx]=.5
            signals[t,2,hiidx]=-.5
            if capitulation:
                signals[t,3,int(np.argmin(impact))]=-1.
            else:
                signals[t,3,int(np.argmax(absorption))]=1.
        regimes[t]=regime
        # Prior-only, smooth joint marginal log utility; this is an allocation
        # estimate, NOT a physical executable backtest or reported PnL.
        previous_net=(lc[t-167:t+1]-lc[t-168:t]-
                      r[t-167:t+1]*e[t-167:t+1])
        multiplier=np.ones(4)
        for i in (1,2,3):
            if np.any(signals[t,i]):
                difference=signals[t,i]-signals[t,0]
                d=previous_net@difference
                penalty=.0016*np.abs(difference).sum()/336.
                utility=float(d.mean()-.5*d.var()-penalty)
                multiplier[i]=np.exp(np.clip(336.*utility,-.5,.5))
        budgets[t]=capped_simplex(PRIOR[regime]*multiplier)
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.75+1e-12)
            or not np.all(np.isclose(gross,0.,atol=1e-12)|
                          np.isclose(gross,1.,atol=1e-12))
            or not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("IG_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IG_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IG_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IG_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IG_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IG_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IG_LIQUIDITY_IMPACT_CAUSAL_AND_QUARANTINE_PASS")
