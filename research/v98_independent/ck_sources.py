#!/usr/bin/env python3
"""CK preregistered structural growth, lead-lag catch-up, native carry spread, market-wide recovery."""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
    "RISK_ON":np.array([1.70,.55,.20,.10]),
    "MIXED":np.array([1.20,.45,.35,.30]),
    "RISK_OFF":np.array([.50,.25,.40,.55]),
}

def bundle(close,rate,event):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CK_SOURCE_INPUT")
    n=len(c)
    lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72]
        r504=lc[t]-lc[t-504]
        breadth=int(np.count_nonzero(r336>0))
        dd=float(1.-c[t,0]/np.max(c[t-335:t+1,0]))
        regime=("RISK_ON" if breadth>=3 and dd<.12 else
                "RISK_OFF" if breadth<=1 and dd>.20 else "MIXED")
        regimes[t]=regime
        age=t-WARMUP
        if age%336==0:
            signals[t,0]=[.60,.25,0.,.15]
            updates[t,0]=True
        # BTC-to-alt lagged catch-up, positive long-horizon alt filter.
        candidates=[j for j in (2,3) if r72[0]>0 and r504[j]>0
                    and r72[0]-r72[j]>.02]
        if candidates:
            j=sorted(candidates,key=lambda j:(-(r72[0]-r72[j]),j))[0]
            signals[t,1,j]=1.
        updates[t,1]=True
        # Native signed funding rates, completed events only.
        native=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        low=int(np.argmin(native))
        high=int(np.argmax(native))
        if low!=high and native[high]>native[low]:
            signals[t,2,low]=.5
            signals[t,2,high]=-.5
        updates[t,2]=True
        # Broad-market drawdown continuation or recovery.
        if int(np.count_nonzero(r168<0))>=3:
            market24=float(np.mean(lc[t]-lc[t-24]))
            if market24>0:signals[t,3,0]=1.
            elif market24<0:signals[t,3,0]=-1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CK_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CK_RV_NOT_DOLLAR_NEUTRAL")
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
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CK_CAUSAL_STRUCTURAL_GROWTH_NATIVE_CARRY_SOURCE_PASS")
