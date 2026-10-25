#!/usr/bin/env python3
"""CX preregistered seven-slot causal source and prior-only shadow utility router.
Training-only; no prior rejected engine signals or benchmarks imported.
"""
from __future__ import annotations
import numpy as np

WARMUP=1008
GRID=168
BASE_BUDGETS={
    "RISK_ON":np.array([2.25,.45,.35,.20],dtype=float),
    "MIXED":np.array([1.65,.40,.40,.40],dtype=float),
    "RISK_OFF":np.array([.65,.30,.45,.70],dtype=float),
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
        raise ValueError("CX_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    hourly=np.zeros_like(c)
    hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4),dtype=float)
    shadow=np.zeros((n,4),dtype=float)
    prev=np.zeros((4,4),dtype=float)
    pending=np.zeros(4,dtype=float)
    for t in range(1,n):
        shadow[t]=prev@hourly[t] - (prev@(r[t]*e[t])) - pending
        pending[:]=0.
        if t<WARMUP or (t-WARMUP)%GRID!=0:
            continue
        ret168=lc[t]-lc[t-168]
        ret336=lc[t]-lc[t-336]
        breadth=int(np.count_nonzero(ret168>0))
        regime=("RISK_ON" if ret336[0]>0 and breadth>=3 else
                "RISK_OFF" if ret336[0]<0 and breadth<=1 else "MIXED")
        regimes[t]=regime
        score=shadow[t-503:t+1].sum(axis=0) if t>=WARMUP+504 else None
        scale=np.ones(4) if score is None else np.where(score>0.,1.3,.55)
        budgets[t]=BASE_BUDGETS[regime]*scale
        if (t-WARMUP)%336==0:
            d=hourly[t-719:t+1,[0,1,3]]
            downside=np.sqrt(np.mean(np.minimum(d,0.)**2,axis=0))
            drift=lc[t,[0,1,3]]-lc[t-720,[0,1,3]]
            strength=np.maximum(drift,0.)/np.maximum(downside,.0005)
            if strength.sum()>0:
                signals[t,0,[0,1,3]]=strength/strength.sum()
            updates[t,0]=True
        ratios=[]
        for j in (2,3):
            recent=max(1.,float(q[t-71:t+1,j].sum()/72.))
            prior=max(1.,float(q[t-287:t-71,j].sum()/216.))
            ratios.append(float((lc[t,j]-lc[t-72,j])*np.sqrt(recent/prior)))
        chosen=2+int(np.argmax(np.abs(ratios)))
        signals[t,1,chosen]=1. if ratios[chosen-2]>=0 else -1.
        updates[t,1]=True
        asym=[]
        for j in (2,3):
            tail=np.sort(hourly[t-335:t+1,j])
            asym.append(float(tail[-34:].mean()+tail[:34].mean()))
        if asym[0]!=asym[1]:
            higher=2+int(asym[1]>asym[0])
            lower=3 if higher==2 else 2
            signals[t,2,higher]=.5
            signals[t,2,lower]=-.5
        updates[t,2]=True
        b72=int(np.count_nonzero((lc[t]-lc[t-72])>0))
        if b72<=1 or (b72>=3 and ret336[0]<0):
            d=np.sqrt(np.mean(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
            if b72<=1:
                j=int(np.argmax(d));signals[t,3,j]=-1.
            else:
                j=int(np.argmin(d));signals[t,3,j]=1.
        updates[t,3]=True
        for i in np.flatnonzero(updates[t]):
            pending[i]=.0015*np.sum(np.abs(signals[t,i]-prev[i]))
            prev[i]=signals[t,i].copy()
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CX_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CX_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("CX_BUDGET_NAN")
    return signals,updates,regimes,budgets

def static_check():
    n=4300
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(c,r,e,q)
    c2=c.copy();c2[3200:]*=1.8
    q2=q.copy();q2[3200:]*=4.
    r2=r.copy();r2[3200:]*=-1.
    b=bundle(c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    assert set(np.unique(a[2])).issubset(set(BASE_BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CX_CAUSAL_SOURCE_STATIC_PASS")
