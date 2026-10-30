#!/usr/bin/env python3
"""CU preregistered causal carry-adjusted breadth core, alt acceleration,
BNB/SOL residual reversion and drawdown-conditioned ETH reaction.
Only completed t-close sources; next actual t+1 open. No holdout access.
"""
from __future__ import annotations
import numpy as np

WARMUP=1008
GRID=168
BUDGETS={
    "RISK_ON":np.array([2.40,.35,.20,.10]),
    "MIXED":np.array([1.75,.30,.30,.25]),
    "RISK_OFF":np.array([.70,.20,.45,.55]),
}

def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (r,e,q)) or
        any(not np.isfinite(a).all() for a in (c,r,e,q)) or
        np.any(c<=0) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("CU_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        ret1008=lc[t]-lc[t-1008]
        ret336=lc[t]-lc[t-336]
        ret72=lc[t]-lc[t-72]
        prior72=lc[t-72]-lc[t-144]
        breadth=int(np.count_nonzero(ret336>0))
        regime=("RISK_ON" if breadth>=3 and ret336[0]>0 else
                "RISK_OFF" if breadth<=1 and ret336[0]<0 else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%336==0:
            native=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            score=ret1008-6.*native
            eligible=[j for j in range(4) if ret1008[j]>0 and ret336[j]>0]
            ranked=sorted(eligible,key=lambda j:(-score[j],j))[:2]
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)==2:
                signals[t,0,ranked[0]]=.7
                signals[t,0,ranked[1]]=.3
            updates[t,0]=True
        candidates=[]
        for j in (2,3):
            recent=float(q[t-71:t+1,j].sum())
            previous=float(q[t-143:t-71,j].sum())
            if (ret72[j]>0 and ret72[j]-prior72[j]>.015 and
                recent>=.8*previous):
                candidates.append(j)
        if candidates:
            best=sorted(candidates,key=lambda j:(-(ret72[j]-prior72[j]),j))[0]
            signals[t,1,best]=1.
        updates[t,1]=True
        residual=ret72[[2,3]]-ret72[0]
        diff=float(residual[0]-residual[1])
        if abs(diff)>.025:
            under=2 if diff<0 else 3
            over=3 if under==2 else 2
            signals[t,2,under]=.5
            signals[t,2,over]=-.5
        updates[t,2]=True
        drawdown=1.-c[t,0]/float(np.max(c[t-335:t+1,0]))
        if drawdown>=.10:
            if ret72[0]>.015:
                signals[t,3,1]=1.
            elif ret72[0]<-.015:
                signals[t,3,1]=-1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CU_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CU_RV_NOT_DOLLAR_NEUTRAL")
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
    print("CU_CAUSAL_SOURCE_STATIC_PASS")
