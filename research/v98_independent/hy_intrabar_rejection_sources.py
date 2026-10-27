#!/usr/bin/env python3
"""HY preregistered native intrabar rejection composed source. Completed t close -> t+1 open."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.60}
PRIOR={"TREND":np.array([.56,.18,.16,.10]),
       "TRANSITION":np.array([.54,.20,.16,.10]),
       "STRESS":np.array([.46,.16,.16,.22])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HY_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    lower=(np.minimum(o,c)-l)/np.maximum(h-l,1e-12)
    upper=(h-np.maximum(o,c))/np.maximum(h-l,1e-12)
    if (np.any(lower< -1e-10) or np.any(upper< -1e-10) or
        np.any(lower>1+1e-10) or np.any(upper>1+1e-10)):
        raise ValueError("HY_INVALID_WICK_GEOMETRY")
    imbalance=lower-upper
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        n72,n168,n336,n672=(net(t,w) for w in (72,168,336,672))
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.60,.40]
        volume=np.sum(q[t-71:t+1],axis=0)
        if np.any(volume<=0):
            raise ValueError("HY_NO_QUOTE_FOR_WICK_EPOCH")
        wick=np.sum(q[t-71:t+1]*imbalance[t-71:t+1],axis=0)/volume
        hi=int(np.argmax(wick));lo=int(np.argmin(wick))
        if hi==lo:
            raise ValueError("HY_RV_NO_DISTINCT_ASSETS")
        signals[t,1,hi]=1.
        signals[t,2,hi]=.5
        signals[t,2,lo]=-.5
        stress=(float(np.median(n72))<-.04 or float(n72[0])<-.06)
        signals[t,3,int(np.argmax(wick if stress else n168))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<0) or not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.allclose(gross,1.,atol=1e-12) or
            not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("HY_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,native_valid

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
            raise ValueError("HY_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HY_EPOCH_BUDGET_CONSERVATION")
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-12):
        raise ValueError("HY_SIGNED_SLEEVE_GROSS_CONSERVATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("HY_INTRABAR_REJECTION_CAUSAL_SOURCE_PASS")
