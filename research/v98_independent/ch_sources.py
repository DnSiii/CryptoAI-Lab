#!/usr/bin/env python3
"""CH independent, preregistered multi-horizon seven-slot source. 2023-24 TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.60,.60,.30,.10]),
 "MIXED":np.array([1.25,.45,.35,.35]),
 "RISK_OFF":np.array([.45,.15,.40,.70]),
}
def bundle(close,rate,event):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CH_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r672=lc[t]-lc[t-672]
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        r48=lc[t]-lc[t-48]
        breadth=int(np.count_nonzero(r336>0))
        regime="RISK_ON" if breadth>=3 else "RISK_OFF" if breadth<=1 else "MIXED"
        regimes[t]=regime
        age=t-WARMUP
        if age%336==0:
            vol=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0,ddof=1)*np.sqrt(336.)
            score=r336/np.maximum(vol,.02)
            eligible=[j for j in range(4) if r336[j]>0]
            ranked=sorted(eligible,key=lambda j:(-score[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.65
                signals[t,0,ranked[1]]=.35
            updates[t,0]=True
        eligible=[j for j in (2,3) if r672[j]>0]
        if eligible:
            winner=sorted(eligible,key=lambda j:(-r48[j],j))[0]
            signals[t,1,winner]=1.
        updates[t,1]=True
        relative=r168[0]-r168[1]
        if relative>0:
            signals[t,2,0]=-.5
            signals[t,2,1]=.5
        elif relative<0:
            signals[t,2,0]=.5
            signals[t,2,1]=-.5
        updates[t,2]=True
        if r168[0]<0:
            signals[t,3,0]=-1.
        elif r168[0]>0 and r672[0]<0:
            signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CH_GROSS_SOURCE")
    if not np.allclose(np.sum(signals[:,2],axis=1),0.):
        raise ValueError("CH_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
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
    print("CH_CAUSAL_MULTI_HORIZON_SOURCE_PASS")
