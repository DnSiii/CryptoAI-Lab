#!/usr/bin/env python3
"""IH preregistered breadth-dispersion-stress complete seven-slot causal signals.
Pre-result contract: ih_breadth_dispersion_prereg_20261027.md.
2022-12 warmup and 2023-24 only; no benchmark, holdout or live execution.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.60,"EXPANSION":.82,"TRANSITION":.72}
PRIOR={"STRESS":np.array([.65,.10,.10,.15]),
       "EXPANSION":np.array([.50,.20,.20,.10]),
       "TRANSITION":np.array([.60,.15,.15,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IH_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n72=net(t,72);n168=net(t,168);n672=net(t,672)
        hourly=np.diff(lc[t-168:t+1],axis=0)
        semivol=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        core=np.exp(np.clip((.6*n672+.4*n168)/(np.sqrt(672.)*semivol),-2.,2.))
        signals[t,0]=core/core.sum()
        quote_window=q[t-335:t+1]
        range_window=np.log(h[t-335:t+1]/l[t-335:t+1])
        valid=bool(np.all(quote_window>0) and np.all(range_window>0)
                   and np.isfinite(range_window).all())
        validity[t,1:]=valid
        breadth=int(np.count_nonzero(n72>0))
        med=float(np.median(n72))
        regime="STRESS" if breadth<=1 else "EXPANSION" if breadth>=3 else "TRANSITION"
        if valid:
            if breadth>=2 and float(np.max(n72))>=.02:
                idx=int(np.argmax(n72+.5*n168))
                signals[t,1,idx]=1.
            if float(np.max(n168)-np.min(n168))>=.04 and float(np.max(n168))>0:
                score=n168-np.median(n168)+.25*n672
                signals[t,2,int(np.argmax(score))]=1.
            if breadth<=1:
                signals[t,3,int(np.argmin(n72))]=-1.
            elif med>=0:
                signals[t,3,int(np.argmax(n72-.5*n168))]=1.
            else:
                signals[t,3,0]=1.
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
            raise ValueError("IH_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IH_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IH_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IH_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IH_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IH_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IH_BREADTH_DISPERSION_CAUSAL_AND_QUARANTINE_PASS")
