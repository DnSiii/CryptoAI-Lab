#!/usr/bin/env python3
"""DB protected-core, residual-capacity seven-slot causal sources. Training only."""
from __future__ import annotations
import numpy as np

WARMUP=1008
GRID=168
BUDGETS={
    "RISK_ON":np.array([1.90,.30,.40,.20]),
    "MIXED":np.array([1.50,.45,.50,.35]),
    "RISK_OFF":np.array([.65,.20,.45,.65]),
}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DB_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        ret480=lc[t]-lc[t-480]
        ret120=lc[t]-lc[t-120]
        adjusted480=ret480-native[t-479:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(adjusted480>0))
        regime=("RISK_ON" if breadth>=3 and ret120[0]>0 else
                "RISK_OFF" if breadth<=1 and ret120[0]<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        score=np.where((adjusted480>0)&(ret120>0),adjusted480*ret120,0.)
        if score.max()>0:
            signals[t,0,int(np.argmax(score))]=1.
        updates[t,0]=True
        # 10 strictly prior, non-overlapping completed 24h returns.
        baseline=np.stack([lc[t-24*(k+1)]-lc[t-24*(k+2)]
                           for k in range(10)])
        threshold=2.*np.median(np.abs(baseline),axis=0)
        shock=lc[t]-lc[t-24]
        if lc[t,0]-lc[t-48,0]>0:
            eligible=(shock< -threshold)&(threshold>1e-12)
            if eligible.any():
                severity=np.where(eligible,-shock/np.maximum(threshold,1e-12),0.)
                signals[t,1,int(np.argmax(severity))]=1.
        updates[t,1]=True
        # ETH/SOL funding carry divergence plus opposite price drift.
        f_eth=float(r[np.flatnonzero(e[:t+1,1])[-21:],1].sum())
        f_sol=float(r[np.flatnonzero(e[:t+1,3])[-21:],3].sum())
        carry_spread=f_sol-f_eth
        relative_price=(lc[t,3]-lc[t-168,3])-(lc[t,1]-lc[t-168,1])
        if carry_spread*relative_price>0:
            sign=1. if carry_spread>0 else -1.
            signals[t,2,1]=.5*sign
            signals[t,2,3]=-.5*sign
        updates[t,2]=True
        # Downside breadth stress / synchronized recovery transition.
        now=lc[t]-lc[t-48]
        before=lc[t-48]-lc[t-96]
        if (lc[t,0]-lc[t-168,0]<0 and
            int(np.count_nonzero(now<0))>=3):
            signals[t,3,0]=-1.
        elif (int(np.count_nonzero(before>0))<=1 and
              int(np.count_nonzero(now>0))>=3):
            signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DB_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DB_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("DB_BUDGET_NONFINITE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2=c.copy();o2=o.copy();h2=h.copy();l2=l.copy()
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2=q.copy();q2[3200:]*=4.
    r2=r.copy();r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    return True

if __name__=="__main__":
    assert static_check()
    print("DB_CAUSAL_SOURCE_STATIC_PASS")
