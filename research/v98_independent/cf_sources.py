#!/usr/bin/env python3
"""CF independent 7-slot source: 1344h directional persistence, native funding rebate,
volatility-dispersion relative value and crash recovery. No rejected alpha import.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
PERIOD_CORE=672
PERIOD_OPP=1008
PERIOD_RV=1008
PERIOD_STRESS=504
BUDGETS={
 "BULL":np.array([1.80,.40,.20,0.]),
 "RANGE":np.array([1.00,.20,.25,.25]),
 "CRISIS":np.array([.30,0.,.15,.60]),
}
def bundle(close,rate,event):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CF_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"RANGE",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r1344=lc[t]-lc[t-1344]
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        dd336=1.-c[t,0]/np.max(c[t-335:t+1,0])
        regime=("CRISIS" if dd336>.20 else
                "BULL" if r1344[0]>0 else "RANGE")
        regimes[t]=regime
        age=t-WARMUP
        if age%PERIOD_CORE==0:
            eligible=[j for j in (0,1) if r1344[j]>0]
            if eligible:
                signals[t,0,eligible]=1./len(eligible)
            updates[t,0]=True
        if age%PERIOD_OPP==0:
            funding=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
            good=[j for j in (2,3) if r336[j]>0 and funding[j]<0]
            if good:
                winner=sorted(good,key=lambda j:(funding[j],j))[0]
                signals[t,1,winner]=1.
            updates[t,1]=True
            steps=np.diff(lc[t-672:t+1],axis=0)
            vol=np.sqrt(np.mean(steps**2,axis=0))
            lo=int(np.argmin(vol));hi=int(np.argmax(vol))
            if lo!=hi and vol[hi]/max(vol[lo],.001)>2.0:
                signals[t,2,lo]=.5
                signals[t,2,hi]=-.5
            updates[t,2]=True
        if age%PERIOD_STRESS==0:
            if dd336>.20 and r168[0]>0:
                signals[t,3,0]=1.
            updates[t,3]=True
    if not np.all(np.sum(abs(signals),axis=2)<=1.+1e-12):
        raise ValueError("CF_GROSS_SOURCE")
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
    print("CF_INDEPENDENT_CAUSAL_SEVEN_SLOT_SOURCE_PASS")
