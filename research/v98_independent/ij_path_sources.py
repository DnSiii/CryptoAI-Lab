#!/usr/bin/env python3
"""IJ pre-registered realized-path efficiency / downside asymmetry seven-slot causal source.
Contract: ij_path_efficiency_prereg_20261027.md. No 2025+, benchmarks, paper or live orders.
"""
from __future__ import annotations
import numpy as np
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.68,"RECOVERY":.92,"NORMAL":.84}
PRIOR={"STRESS":np.array([.62,.08,.10,.20]),
       "RECOVERY":np.array([.48,.22,.15,.15]),
       "NORMAL":np.array([.55,.20,.15,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IJ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n72=net(t,72);n168=net(t,168);n336=net(t,336);n672=net(t,672)
        returns=np.diff(lc[t-336:t+1],axis=0)
        efficiency=np.clip(np.abs(n336)/(np.abs(returns).sum(axis=0)+1e-12),0.,1.)
        raw=np.exp(np.clip(4.*np.sign(n336)*efficiency+.5*n672,-2.,2.))
        signals[t,0]=raw/raw.sum()
        ranges=np.log(h[t-335:t+1]/l[t-335:t+1])
        quote_window=q[t-335:t+1]
        valid=bool(np.all(quote_window>0) and np.all(ranges>0) and
                   np.isfinite(ranges).all())
        validity[t,1:]=valid
        compression=np.clip(ranges[-72:].mean(axis=0)/
                            ranges[:-72].mean(axis=0),.25,4.)
        down72=np.maximum(np.sqrt(np.mean(np.minimum(returns[-72:],0.)**2,axis=0)),.0001)
        downprev=np.maximum(np.sqrt(np.mean(np.minimum(returns[:-72],0.)**2,axis=0)),.0001)
        up72=np.sqrt(np.mean(np.maximum(returns[-72:],0.)**2,axis=0))
        stress=bool(float(np.median(down72)/np.median(downprev))>1.4)
        regime="STRESS" if stress else ("RECOVERY" if
             float(np.median(n72))>0 and float(np.median(n168))<0 else "NORMAL")
        if valid:
            eligible=(n72>0)&(compression<1.25)
            if eligible.any():
                score=np.where(eligible,n72/(.25+compression),-np.inf)
                signals[t,1,int(np.argmax(score))]=1.
            if int(np.count_nonzero(n336>0))>=2:
                score=np.where(n336>0,efficiency,-np.inf)
                signals[t,2,int(np.argmax(score))]=1.
            if stress:
                signals[t,3,int(np.argmin(down72))]=1.
            else:
                signals[t,3,int(np.argmax(up72/(down72+.0001)))]=1.
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12)):
            raise ValueError("IJ_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IJ_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IJ_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IJ_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IJ_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IJ_ZERO_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("IJ_PATH_EFFICIENCY_CAUSAL_AND_QUARANTINE_PASS")
