#!/usr/bin/env python3
"""FD preregistered single-book risk-budget score tilts, seven slots. TRAINING ONLY."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=240
GROSS_CAP=2.80
CORE={"TREND":2.25,"MIXED":1.85,"STRESS":1.30}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("FD_INVALID_PINNED_SOURCE")
    n=len(c)
    lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net504,net336,net168,net72,net24=(native(t,w) for w in (504,336,168,72,24))
        breadth=int(np.count_nonzero(net504>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        raw=np.maximum(net504,0.)+.02
        signals[t,0]=raw/raw.sum()
        budgets[t,0]=CORE[regime]
        updates[t]=True

        accel=net72-.5*net336
        j=int(np.argmax(accel))
        if int(np.count_nonzero(net168>0))>=2 and accel[j]>0 and net72[j]>0:
            signals[t,1,:]=-.20/3.
            signals[t,1,j]=.20
            budgets[t,1]=1.

        vol=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0)*np.sqrt(336.)+1e-6
        rank=net336/vol
        hi=int(np.argmax(rank))
        lo=int(np.argmin(rank))
        if hi!=lo:
            signals[t,2,hi]=.12
            signals[t,2,lo]=-.12
            budgets[t,2]=1.

        basket168=float(np.mean(net168))
        if basket168<0:
            lo=int(np.argmin(net168))
            if lo!=0:
                signals[t,3,0]=.15
                signals[t,3,lo]=-.15
                budgets[t,3]=1.
        elif float(np.mean(net24))>0 and basket168<.03:
            hi=int(np.argmax(net24))
            lo=int(np.argmin(net168))
            if hi!=lo:
                signals[t,3,hi]=.15
                signals[t,3,lo]=-.15
                budgets[t,3]=1.

    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.abs(np.sum(signals[:,0,:],axis=1)[updates[:,0]]-1.)>1e-12) or
        np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(budgets[:,0]>GROSS_CAP+1e-12)):
        raise ValueError("FD_SCORE_OR_GROSS_INVARIANT")
    # All ablations must independently normalize a single long-only physical book.
    for t in np.flatnonzero(updates[:,0]):
        for omitted in (None,1,2,3):
            score=signals[t,0].copy()
            for i in (1,2,3):
                if i!=omitted:score+=signals[t,i]*budgets[t,i]
            score=np.maximum(score,0.)
            if not np.isfinite(score).all() or score.sum()<=0:
                raise ValueError("FD_SCORE_NONPOSITIVE")
            weights=score/score.sum()
            if (np.any(weights<0) or abs(weights.sum()-1.)>1e-12 or
                budgets[t,0]*weights.sum()>GROSS_CAP+1e-12):
                raise ValueError("FD_SINGLE_BOOK_CONSERVATION")
    return signals,updates,regimes,budgets

def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2),0.,atol=1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("FD_CAUSAL_STATIC_PASS")
