#!/usr/bin/env python3
"""CN independent persistence, volume breakout, long-only relative value, recovery.
Completed close t; next actual open t+1. Historical training only.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=24
BUDGETS={
 "RISK_ON":np.array([1.65,.45,.40,.25]),
 "MIXED":np.array([1.25,.40,.50,.40]),
 "RISK_OFF":np.array([.75,.25,.25,.60]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e,q))
        or len(c)<=WARMUP or any(not np.isfinite(x).all() for x in (c,r,e,q))
        or np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CN_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r12=lc[t]-lc[t-12]
        r72=lc[t]-lc[t-72]
        r96=lc[t]-lc[t-96]
        r240=lc[t]-lc[t-240]
        r720=lc[t]-lc[t-720]
        breadth=int(np.count_nonzero(r240>0))
        regime=("RISK_ON" if breadth>=3 else "RISK_OFF" if breadth<=1 else "MIXED")
        regimes[t]=regime
        age=t-WARMUP
        if age%360==0:
            persistence=np.mean(lc[t-672:t+1]-lc[t-720:t-47]>0,axis=0)
            eligible=[j for j in range(4) if r720[j]>0 and persistence[j]>.55]
            ranked=sorted(eligible,key=lambda j:(-persistence[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.70
                signals[t,0,ranked[1]]=.30
            updates[t,0]=True
        candidates=[]
        for j in (2,3):
            prior=q[t-503:t-23,j].reshape(20,24).sum(axis=1)
            current=float(q[t-23:t+1,j].sum())
            ratio=current/max(float(np.median(prior)),1e-12)
            if (c[t,j]>float(np.max(c[t-144:t,j])) and ratio>1.2
                and r240[j]>0):
                candidates.append((ratio,j))
        if candidates:
            j=sorted(candidates,key=lambda x:(-x[0],x[1]))[0][1]
            signals[t,1,j]=1.
        updates[t,1]=True
        if age%72==0:
            excess96=r96-float(np.mean(r96))
            excess240=r240-float(np.mean(r240))
            ranked=sorted(range(4),key=lambda j:(-excess96[j],j))
            j=ranked[0]
            if excess96[j]>0 and excess240[j]>0 and r240[j]>0:
                signals[t,2,j]=1.
            updates[t,2]=True
        if int(np.count_nonzero(r72<0))>=3 and float(np.mean(r12))>0:
            ranked=sorted((0,1),key=lambda j:(-r12[j],j))
            if r12[ranked[0]]>0:
                signals[t,3,ranked[0]]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CN_GROSS_SOURCE")
    if np.any(signals<0):
        raise ValueError("CN_LONG_ONLY_SOURCE")
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
    assert np.all(s>=0)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CN_CAUSAL_PERSISTENCE_RELATIVE_VALUE_SOURCE_PASS")
