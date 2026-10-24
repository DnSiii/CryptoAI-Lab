#!/usr/bin/env python3
"""CO slow path-efficiency growth, weekly volume surprise, ETH/BTC paired RV,
and volatility-recovery long sleeve. Completed t -> earliest t+1 open.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.85,.35,.30,.25]),
 "MIXED":np.array([1.40,.35,.40,.35]),
 "RISK_OFF":np.array([.70,.20,.50,.45]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e,q))
        or len(c)<=WARMUP or any(not np.isfinite(x).all() for x in (c,r,e,q))
        or np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CO_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    spread=lc[:,1]-lc[:,0]
    for t in range(WARMUP,n,GRID):
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        breadth=int(np.count_nonzero(r336>0))
        regime=("RISK_ON" if r336[0]>0 and breadth>=2 else
                "RISK_OFF" if r336[0]<0 and breadth<=1 else "MIXED")
        regimes[t]=regime
        age=t-WARMUP
        if age%336==0:
            increments=np.diff(lc[t-1008:t+1],axis=0)
            efficiency=r1008/np.maximum(np.sum(np.abs(increments),axis=0),1e-12)
            eligible=[j for j in range(4) if r1008[j]>0 and efficiency[j]>.02]
            ranked=sorted(eligible,key=lambda j:(-efficiency[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.65
                signals[t,0,ranked[1]]=.35
            updates[t,0]=True
        candidates=[]
        for j in (2,3):
            recent=float(np.mean(q[t-167:t+1,j]))
            previous=float(np.mean(q[t-839:t-167,j]))
            if (r336[j]>0 and r168[j]>0
                and recent>1.15*max(previous,1e-12)):
                candidates.append(j)
        if candidates:
            j=sorted(candidates,key=lambda j:(-r168[j],j))[0]
            signals[t,1,j]=1.
        updates[t,1]=True
        history=spread[t-1008:t]
        mean=float(np.mean(history))
        std=float(np.std(history))
        z=(float(spread[t])-mean)/max(std,1e-12)
        if z>1.:
            signals[t,2,0]=.5;signals[t,2,1]=-.5
        elif z< -1.:
            signals[t,2,0]=-.5;signals[t,2,1]=.5
        updates[t,2]=True
        hourly=np.diff(lc[t-1176:t+1],axis=0)
        recent_vol=float(np.mean(np.std(hourly[-168:],axis=0)))
        prior_vol=float(np.mean(np.std(hourly[:-168],axis=0)))
        if recent_vol>1.25*max(prior_vol,1e-12) and float(np.mean(r72))>0:
            signals[t,3,0]=.5;signals[t,3,1]=.5
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CO_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CO_PAIR_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e,q)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    volumes=q.copy();volumes[2900:]*=4.
    s2,m2,z2=bundle(changed,rates,e,volumes)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CO_CAUSAL_SLOW_EFFICIENCY_PAIR_SOURCE_PASS")
