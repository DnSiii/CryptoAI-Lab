#!/usr/bin/env python3
"""CT independent two-leader growth, volume-confirmed breakout, BTC/ETH relative drift and asymmetric BTC stress."""
from __future__ import annotations
import numpy as np
WARMUP=744
GRID=168
BUDGETS={
 "RISK_ON":np.array([2.15,.35,.30,.10]),
 "MIXED":np.array([1.60,.40,.40,.25]),
 "RISK_OFF":np.array([.70,.20,.45,.65]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float);q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,r,e,q)) or
        np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CT_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        prev168=lc[t-168]-lc[t-336]
        breadth=int(np.count_nonzero(r168>0))
        regimes[t]=("RISK_ON" if r336[0]>0 and breadth>=3 else
                    "RISK_OFF" if r336[0]<0 and breadth<=1 else "MIXED")
        if (t-WARMUP)%336==0:
            winners=sorted((j for j in range(4) if r336[j]>0),
                           key=lambda j:(-r336[j],j))[:2]
            if len(winners)==2:
                signals[t,0,winners[0]]=.7
                signals[t,0,winners[1]]=.3
            elif len(winners)==1:
                signals[t,0,winners[0]]=1.
            updates[t,0]=True
        eligible=[]
        for j in (2,3):
            history=c[t-336:t,j]
            qrecent=float(q[t-167:t+1,j].sum())
            qprior=float(q[t-335:t-167,j].sum())
            if (c[t,j]>float(np.quantile(history,.75)) and
                r168[j]>0 and qrecent>qprior):
                eligible.append(j)
        if eligible:
            best=sorted(eligible,key=lambda j:(-c[t,j]/float(np.median(c[t-336:t,j])),j))[0]
            signals[t,1,best]=1.
        updates[t,1]=True
        diff=float(r336[0]-r336[1])
        if abs(diff)>.015:
            stronger=0 if diff>0 else 1
            signals[t,2,stronger]=.5
            signals[t,2,1-stronger]=-.5
        updates[t,2]=True
        r72=float(lc[t,0]-lc[t-72,0])
        if r336[0]<0 and r168[0]<0 and r72<0:
            signals[t,3,0]=-1.
        elif r168[0]<0 and r72>0 and prev168[0]<0:
            signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CT_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CT_RV_NOT_DOLLAR_NEUTRAL")
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
    print("CT_CAUSAL_TWO_LEADER_RELATIVE_DRIFT_SOURCE_PASS")
