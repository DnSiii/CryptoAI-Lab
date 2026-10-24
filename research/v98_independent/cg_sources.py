#!/usr/bin/env python3
"""CG independent seven-slot source: causal cross-sectional net-carry momentum,
alt breakout, BTC/ETH paired trend and broad-market bear sleeve. TRAINING ONLY.
No rejected CF alpha signals, no 2025, no external benchmark.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
PERIOD_CORE=504
PERIOD_OPP=336
PERIOD_RV=672
PERIOD_STRESS=336
BUDGETS={
 "RISK_ON":np.array([1.70,.55,.25,0.]),
 "MIXED":np.array([1.10,.45,.35,.25]),
 "RISK_OFF":np.array([.25,.10,.40,.70]),
}
def bundle(close,rate,event):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CG_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r672=lc[t]-lc[t-672]
        r504=lc[t]-lc[t-504]
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        carry672=np.sum(r[t-671:t+1]*e[t-671:t+1],axis=0)
        breadth672=int(np.count_nonzero(r672>0))
        regime=("RISK_ON" if breadth672>=3 else
                "RISK_OFF" if breadth672<=1 else "MIXED")
        regimes[t]=regime
        age=t-WARMUP
        if age%PERIOD_CORE==0:
            score=r672-carry672
            eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0]
            ranked=sorted(eligible,key=lambda j:(-score[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.70
                signals[t,0,ranked[1]]=.30
            updates[t,0]=True
        if age%PERIOD_OPP==0:
            carry336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
            eligible=[j for j in (2,3) if c[t,j]>np.max(c[t-168:t,j])
                      and r336[j]>0 and carry336[j]<=.03]
            if eligible:
                winner=sorted(eligible,key=lambda j:(-r336[j],j))[0]
                signals[t,1,winner]=1.
            updates[t,1]=True
        if age%PERIOD_RV==0:
            carry504=np.sum(r[t-503:t+1]*e[t-503:t+1],axis=0)
            net=r504-carry504
            hi=0 if net[0]>=net[1] else 1
            lo=1-hi
            if net[hi]-net[lo]>.15 and r168[lo]<0:
                signals[t,2,hi]=.5
                signals[t,2,lo]=-.5
            updates[t,2]=True
        if age%PERIOD_STRESS==0:
            breadth168=int(np.count_nonzero(r168>0))
            if (c[t,0]<np.mean(c[t-671:t+1,0])
                and r168[0]<0 and breadth168<=1):
                signals[t,3,0]=-1.
            updates[t,3]=True
    if not np.all(np.sum(abs(signals),axis=2)<=1.+1e-12):
        raise ValueError("CG_GROSS_SOURCE")
    return signals,updates,regimes

def static_check():
    n=3400;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    s2,m2,z2=bundle(changed,rates,e)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.allclose(np.sum(s[:,2],axis=1),0.)
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True

if __name__=="__main__":
    assert static_check()
    print("CG_INDEPENDENT_CAUSAL_SEVEN_SLOT_SOURCE_PASS")
