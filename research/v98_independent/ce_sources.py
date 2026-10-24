#!/usr/bin/env python3
"""CE independent persistent BTC/ETH market premium and native funding carry signals.
Causal completed close only; no rejected candidate signals or benchmark imports.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
PERIOD_CORE=2016
PERIOD_OPP=672
PERIOD_RV=2016
PERIOD_STRESS=336
GRID=168
BUDGETS={
 "BULL":np.array([1.60,.55,.25,0.]),
 "RANGE":np.array([1.25,.35,.30,.25]),
 "CRISIS":np.array([.65,0.,.30,.60]),
}
def bundle(close,rate,event):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CE_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"RANGE",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r672=lc[t]-lc[t-672]
        r1344=lc[t]-lc[t-1344]
        dd672=1.-c[t,0]/np.max(c[t-671:t+1,0])
        regime=("CRISIS" if dd672>.25 else
                "BULL" if r1344[0]>0 and np.count_nonzero(r672>0)>=3
                else "RANGE")
        regimes[t]=regime
        age=t-WARMUP
        if age%PERIOD_CORE==0:
            signals[t,0,0]=.65
            signals[t,0,1]=.35
            updates[t,0]=True
            f2016=np.sum(r[t-2015:t+1]*e[t-2015:t+1],axis=0)
            lo=int(np.argmin(f2016));hi=int(np.argmax(f2016))
            if lo!=hi and f2016[hi]-f2016[lo]>.035:
                signals[t,2,lo]=.5
                signals[t,2,hi]=-.5
            updates[t,2]=True
        if age%PERIOD_OPP==0:
            f672=np.sum(r[t-671:t+1]*e[t-671:t+1],axis=0)
            market=.65*r672[0]+.35*r672[1]
            market_f=.65*f672[0]+.35*f672[1]
            good=[j for j in (2,3) if r672[j]-market>.08 and f672[j]<=market_f]
            if good:
                j=sorted(good,key=lambda k:(-(r672[k]-market),k))[0]
                signals[t,1,j]=1.
            updates[t,1]=True
        if age%PERIOD_STRESS==0:
            returns=np.diff(lc[t-1344:t+1,0])
            downside=np.minimum(returns,0.)**2
            short=np.sqrt(np.mean(downside[-336:]))
            long=np.sqrt(np.mean(downside))
            if dd672>.25 and short>long:
                signals[t,3,0]=-1.
            updates[t,3]=True
    if not np.all(np.sum(abs(signals),axis=2)<=1.+1e-12):
        raise ValueError("CE_GROSS_SOURCE")
    return signals,updates,regimes

def static_check():
    n=3200;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e)
    changed=c.copy();changed[2600:]*=1.9
    rates=r.copy();rates[2600:]*=-1.
    s2,m2,z2=bundle(changed,rates,e)
    assert np.array_equal(s[:2600],s2[:2600])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2600],z2[:2600])
    assert not s[:WARMUP].any()
    assert np.allclose(np.sum(s[:,2],axis=1),0.)
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("CE_INDEPENDENT_PERSISTENT_PREMIUM_CAUSAL_SOURCE_PASS")
