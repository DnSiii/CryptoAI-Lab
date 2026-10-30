#!/usr/bin/env python3
"""CR causal persistent inverse-vol trend, sign-symmetric alt momentum,
cross-sectional dollar-neutral dispersion and BTC defensive trend.
Completed close t; earliest t+1 open; native funding handled by settlement.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.90,.45,.25,.15]),
 "MIXED":np.array([1.40,.35,.35,.30]),
 "RISK_OFF":np.array([.55,.25,.50,.65]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e,q))
        or len(c)<=WARMUP or any(not np.isfinite(x).all() for x in (c,r,e,q))
        or np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CR_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        breadth=int(np.count_nonzero(r168>0))
        regimes[t]=("RISK_ON" if r168[0]>0 and breadth>=3 else
                    "RISK_OFF" if r168[0]<0 and breadth<=1 else "MIXED")
        if (t-WARMUP)%336==0:
            vol=np.std(np.diff(lc[t-672:t+1],axis=0),axis=0)
            eligible=[j for j in range(4) if r336[j]>0]
            if eligible:
                inverse=np.array([1./max(float(vol[j]),1e-12) for j in eligible])
                inverse/=inverse.sum()
                for j,w in zip(eligible,inverse):
                    signals[t,0,j]=float(w)
            updates[t,0]=True
        r72=lc[t]-lc[t-72]
        vol72=np.std(np.diff(lc[t-72:t+1],axis=0),axis=0)
        score=r72/np.maximum(vol72,1e-12)
        best=sorted((2,3),key=lambda j:(-score[j],j))[0]
        worst=sorted((2,3),key=lambda j:(score[j],j))[0]
        if score[best]>0:
            signals[t,1,best]=1.
        else:
            signals[t,1,worst]=-1.
        updates[t,1]=True
        ranked=sorted(range(4),key=lambda j:(-r168[j],j))
        signals[t,2,ranked[0]]=.5
        signals[t,2,ranked[-1]]=-.5
        updates[t,2]=True
        signals[t,3,0]=1. if r336[0]>=0 else -1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CR_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CR_RV_NOT_DOLLAR_NEUTRAL")
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
    print("CR_CAUSAL_PERSISTENT_MULTISCALE_SOURCE_PASS")
