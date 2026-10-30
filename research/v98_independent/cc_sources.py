#!/usr/bin/env python3
"""CC independent synchronized causal source signals; no rejected alpha imports."""
from __future__ import annotations
import numpy as np
WARMUP=2160
PERIOD_CORE=672
PERIOD_OPP=336
PERIOD_RV=336
PERIOD_STRESS=168
BUDGETS={
    "BULL":np.array([1.80,.35,.40,0.]),
    "RANGE":np.array([1.40,.20,.50,.20]),
    "CRISIS":np.array([.80,0.,.60,.50]),
}

def bundle(close):
    c=np.asarray(close,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or not np.isfinite(c).all()
        or np.any(c<=0) or len(c)<=WARMUP):
        raise ValueError("CC_SOURCE_INPUT")
    n=len(c);log=np.log(c)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"RANGE",dtype="<U8")
    for t in range(WARMUP,n,PERIOD_STRESS):
        x=log[t-1008:t+1]
        r72=x[-1]-x[-73]
        r168=x[-1]-x[-169]
        r336=x[-1]-x[-337]
        r1008=x[-1]-x[0]
        hourly=np.diff(x,axis=0)
        v168=np.sqrt(np.mean(hourly[-168:]**2,axis=0))
        v336=np.sqrt(np.mean(hourly[-336:]**2,axis=0))
        v1008=np.sqrt(np.mean(hourly**2,axis=0))
        regime=("CRISIS" if np.count_nonzero(r72<0)>=3 else
                "BULL" if np.count_nonzero(r336>0)>=3 else "RANGE")
        regimes[t]=regime
        age=t-WARMUP
        if age%PERIOD_CORE==0:
            good=[j for j in range(4) if r1008[j]>0]
            ranked=sorted(good,key=lambda j:(-r1008[j]/max(v336[j],.005),j))[:2]
            if ranked:
                inv=1./np.maximum(v336[ranked],.005)
                signals[t,0,ranked]=inv/inv.sum()
            updates[t,0]=True
        if age%PERIOD_OPP==0:
            previous=x[-169]-x[-337]
            acceleration=r168-previous
            if np.count_nonzero(r336>0)>=2:
                good=[j for j in range(4) if acceleration[j]>0]
                if good:
                    j=sorted(good,key=lambda k:(-acceleration[k],k))[0]
                    signals[t,1,j]=1.
            updates[t,1]=True
            residual=r168-np.mean(r168)
            span=np.max(residual)-np.min(residual)
            if (span>.06 and np.ptp(r72)<np.ptp(r168)):
                low=int(np.argmin(residual));high=int(np.argmax(residual))
                signals[t,2,low]=.5
                signals[t,2,high]=-.5
            updates[t,2]=True
        if np.median(v168)>np.median(v1008):
            signals[t,3,0]=(-1. if np.median(r72)<0 else 1.)
        updates[t,3]=True
    return signals,updates,regimes

def static_check():
    n=3000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0002,.0004,.0001]])
                 +.04*np.sin(t[:,None]/100.+np.arange(4)))
    s,m,r=bundle(c)
    d=c.copy();d[2600:]*=2.
    a,b,z=bundle(d)
    assert np.array_equal(s[:2600],a[:2600])
    assert np.array_equal(m,b)
    assert np.array_equal(r[:2600],z[:2600])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(np.abs(s),axis=2)<=1.+1e-10)
    assert np.allclose(np.sum(s[:,2],axis=1),0.)
    return True

if __name__=="__main__":
    assert static_check()
    print("CC_CAUSAL_SEVEN_SLOT_SOURCE_STATIC_PASS")
