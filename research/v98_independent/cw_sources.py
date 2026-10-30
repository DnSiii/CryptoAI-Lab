#!/usr/bin/env python3
"""CW causal dual-average BTC/ETH core, alt rotation, volume-lead RV,
negative-trend BTC state response. Training only, no rejected source imports.
"""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BUDGETS={
    "RISK_ON":np.array([2.10,.40,.25,.10]),
    "MIXED":np.array([1.60,.30,.30,.30]),
    "RISK_OFF":np.array([.55,.20,.35,.60]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (r,e,q)) or
        any(not np.isfinite(a).all() for a in (c,r,e,q)) or
        np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CW_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        ret504=lc[t]-lc[t-504]
        ret168=lc[t]-lc[t-168]
        ret24=lc[t]-lc[t-24]
        breadth=int(np.count_nonzero(ret168>0))
        regimes[t]=("RISK_ON" if ret504[0]>0 and breadth>=3 else
                    "RISK_OFF" if ret504[0]<0 and breadth<=1 else "MIXED")
        if (t-WARMUP)%336==0:
            active=[]
            for j in (0,1):
                short=float(np.mean(lc[t-167:t+1,j]))
                long=float(np.mean(lc[t-671:t-167,j]))
                if short>long:active.append(j)
            if len(active)==2:
                signals[t,0,0]=.6
                signals[t,0,1]=.4
            elif len(active)==1:
                signals[t,0,active[0]]=1.
            updates[t,0]=True
        alt=(2,3)
        strongest=sorted(alt,key=lambda j:(-ret168[j],j))[0]
        weakest=sorted(alt,key=lambda j:(ret168[j],j))[0]
        if ret168[strongest]>0:
            signals[t,1,strongest]=1.
        else:
            signals[t,1,weakest]=-1.
        updates[t,1]=True
        vrecent=np.maximum(1.,np.sum(q[t-167:t+1,2:4],axis=0))
        vprior=np.maximum(1.,np.sum(q[t-335:t-167,2:4],axis=0))
        lead=np.log(vrecent/vprior)
        spread=float(lead[0]-lead[1])
        if abs(spread)>.05:
            winner=2 if spread>0 else 3
            loser=3 if winner==2 else 2
            signals[t,2,winner]=.5
            signals[t,2,loser]=-.5
        updates[t,2]=True
        if ret168[0]<0:
            if ret24[0]<0:
                signals[t,3,0]=-1.
            elif ret24[0]>0:
                signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CW_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CW_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes
def static_check():
    n=4000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c)
    e[::8]=1.
    s,m,z=bundle(c,r,e,q)
    changed=c.copy()
    changed[2900:]*=1.9
    rates=r.copy()
    rates[2900:]*=-1.
    volumes=q.copy()
    volumes[2900:]*=4.
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
    print("CW_CAUSAL_SOURCE_STATIC_PASS")
