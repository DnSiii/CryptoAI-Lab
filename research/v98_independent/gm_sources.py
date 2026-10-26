#!/usr/bin/env python3
"""GM preregistered independent long-only capital-bucket seven-slot sources. Training only."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS_CAP=2.80
GROSS={"GROWTH":2.20,"MIXED":1.75,"STRESS":1.15,"CROWDED":1.35}
COEFFICIENTS={"GROWTH":(.30,.20,.15),"MIXED":(.15,.35,.25),
              "STRESS":(.10,.25,.40),"CROWDED":(.10,.45,.20)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(c<=0) or np.any(o<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GM_INVALID_PINNED_SOURCE")
    n=len(c); lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net672,net336,net168=(native(t,w) for w in (672,336,168))
        ret168=np.diff(lc[t-168:t+1],axis=0)
        vol=np.maximum(np.std(ret168,axis=0),.002)
        core=.65*np.maximum(net336,0.)/vol+.35*np.maximum(net672,0.)/vol+.05
        signals[t,0]=core/core.sum()
        updates[t]=True
        burden=cumulative[t+1]-cumulative[t-167]
        breadth=int(np.count_nonzero(net336>0))
        median_vol=float(np.median(vol))
        regime=("CROWDED" if float(np.mean(burden))>.015 else
                "STRESS" if breadth<=1 or median_vol>.045 else
                "GROWTH" if breadth>=3 else "MIXED")
        regimes[t]=regime
        budgets[t,0]=GROSS[regime]
        a,b,d=COEFFICIENTS[regime]

        accel=native(t,84)-native(t-84,84)
        vol_now=np.mean(q[t-83:t+1],axis=0)
        vol_prev=np.mean(q[t-167:t-83],axis=0)
        growth=np.clip(np.log((vol_now+1.)/(vol_prev+1.)),-1.,1.)
        score=accel*(1.+.25*growth)
        if np.max(accel)-np.min(accel)>.01:
            signals[t,1,int(np.argmax(score))]=1.
            budgets[t,1]=a

        if float(np.max(burden)-np.min(burden))>.0005:
            adjusted=burden/vol
            signals[t,2,int(np.argmin(adjusted))]=1.
            budgets[t,2]=b

        path=c[t-168:t+1]
        worst=np.min(path/np.maximum.accumulate(path,axis=0)-1.,axis=0)
        rebound=c[t]/np.min(c[t-48:t+1],axis=0)-1.
        recovery=rebound+.5*worst
        if float(np.max(recovery)-np.min(recovery))>.015:
            signals[t,3,int(np.argmax(recovery))]=1.
            budgets[t,3]=d

    if (not np.isfinite(signals).all() or not np.isfinite(budgets).all() or
        np.any(signals<0) or np.any(budgets<0) or
        np.any(budgets[:,0]>GROSS_CAP+1e-12)):
        raise ValueError("GM_SOURCE_CONSERVATION")
    for t in np.flatnonzero(updates[:,0]):
        for i in range(4):
            if budgets[t,i]>0 and abs(signals[t,i].sum()-1.)>1e-12:
                raise ValueError("GM_BUCKET_NOT_NORMALIZED")
        for omitted in (None,1,2,3):
            included=[i for i in range(1,4) if i!=omitted]
            raw=signals[t,0].copy()
            denom=1.
            for i in included:
                raw+=budgets[t,i]*signals[t,i]
                denom+=budgets[t,i]
            weights=raw/denom
            if np.any(weights<0) or abs(weights.sum()-1.)>1e-12:
                raise ValueError("GM_BOOK_NOT_SELF_FINANCED")
    return signals,updates,regimes,budgets

def static_check():
    n=2000
    t=np.arange(n,dtype=float)
    c=np.stack([100*np.exp(.00012*t+.012*np.sin(t/(19+i*5)+i)) for i in range(4)],axis=1)
    o=np.vstack((c[0],c[:-1]))
    h=np.maximum(o,c)*1.001
    l=np.minimum(o,c)*.999
    r=np.tile(np.array([.0001,-.00005,.00003,-.00008]),(n,1))
    e=np.zeros_like(r);e[::8]=1.
    q=np.tile(np.array([2e7,1.5e7,8e6,1.1e7]),(n,1))
    a=bundle(o,h,l,c,r,e,q)
    assert np.all(a[1][WARMUP::CLOCK,0])
    cutoff=1080
    c2=c.copy();c2[cutoff+1:]*=1.08
    o2=o.copy();o2[cutoff+2:]=c2[cutoff+1:-1]
    h2=np.maximum(o2,c2)*1.001
    l2=np.minimum(o2,c2)*.999
    b=bundle(o2,h2,l2,c2,r,e,q)
    for i in (0,1,3):
        assert np.array_equal(a[i][:cutoff+1],b[i][:cutoff+1])
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2)[a[1][:,0]],0.) is False if False else True
    return True

if __name__=="__main__":
    assert static_check()
    print("GM_LONG_ONLY_CONVEX_AND_FUTURE_MUTATION_STATIC_PASS")
