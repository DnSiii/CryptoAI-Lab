#!/usr/bin/env python3
"""CS prospective seven-slot source; no training beyond Dec 2024. Close t -> open t+1."""
from __future__ import annotations
import numpy as np
WARMUP=744
GRID=168
BUDGETS={
 "RISK_ON":np.array([2.10,.45,.30,.10]),
 "MIXED":np.array([1.55,.35,.40,.35]),
 "RISK_OFF":np.array([.55,.15,.50,.70]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float);q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,r,e,q)) or
        np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CS_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        rprev=lc[t-168]-lc[t-336]
        breadth=int(np.count_nonzero(r168>0))
        regimes[t]=("RISK_ON" if r168[0]>0 and breadth>=3 else
                    "RISK_OFF" if r168[0]<0 and breadth<=1 else "MIXED")
        if (t-WARMUP)%336==0:
            r504=lc[t]-lc[t-504]
            vol=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0)
            raw=np.where(r504>0,r504/np.maximum(vol,1e-12),0.)
            if raw.sum()>0:signals[t,0]=raw/raw.sum()
            updates[t,0]=True
        acceleration=r168-rprev
        candidates=[]
        for j in (2,3):
            recent=float(q[t-167:t+1,j].sum())
            previous=float(q[t-335:t-167,j].sum())
            if r168[j]>0 and acceleration[j]>0 and recent>=.80*previous:
                candidates.append(j)
        if candidates:
            best=sorted(candidates,key=lambda j:(-acceleration[j],j))[0]
            signals[t,1,best]=1.
        updates[t,1]=True
        # Signed funding paid by long: long lower cumulative funding, short higher.
        f=(r[t-167:t+1,:2]*e[t-167:t+1,:2]).sum(axis=0)
        if abs(float(f[0]-f[1]))>=.0015:
            lo=int(np.argmin(f));hi=1-lo
            signals[t,2,lo]=.5;signals[t,2,hi]=-.5
        updates[t,2]=True
        r72=float(lc[t,0]-lc[t-72,0])
        if r168[0]<0 and rprev[0]<0:
            signals[t,3,0]=1. if r72>0 else -1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CS_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CS_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3600;t=np.arange(n,dtype=float)
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
    print("CS_CAUSAL_ASYMMETRIC_FUNDING_SOURCE_PASS")
