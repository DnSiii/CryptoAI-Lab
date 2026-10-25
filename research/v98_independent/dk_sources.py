#!/usr/bin/env python3
"""DK factor-compounding and BTC/ETH ratio-reversion complete seven-slot source; training only."""
from __future__ import annotations
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={
    "RISK_ON":np.array([3.6,.35,.25,.15],dtype=float),
    "MIXED":np.array([2.4,.45,.45,.35],dtype=float),
    "RISK_OFF":np.array([.8,.25,.50,.55],dtype=float),
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
        raise ValueError("DK_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    ratio=lc[:,0]-lc[:,1]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,GRID):
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        r48=lc[t]-lc[t-48]
        r24=lc[t]-lc[t-24]
        prev48=lc[t-48]-lc[t-96]
        increments=np.diff(lc[t-336:t+1],axis=0)
        sigma=np.std(increments,axis=0)*np.sqrt(336.)
        score=r336/np.maximum(sigma,1e-8)
        eligible=[j for j in range(4) if r336[j]>0]
        selected=sorted(eligible,key=lambda j:(-float(score[j]),j))[:2]
        if selected:signals[t,0,selected]=1./len(selected)
        acceleration=r48-prev48
        opportunity=[j for j in range(4)
                     if acceleration[j]>.015 and r336[j]>0]
        if opportunity:
            j=sorted(opportunity,key=lambda j:(-float(acceleration[j]),j))[0]
            signals[t,1,j]=1.
        prior=ratio[t-336:t]
        std=float(np.std(prior))
        z=float((ratio[t]-np.mean(prior))/std) if std>1e-10 else 0.
        if z>1.2:
            signals[t,2,0]=-.5;signals[t,2,1]=.5
        elif z< -1.2:
            signals[t,2,0]=.5;signals[t,2,1]=-.5
        prior_peak=np.max(c[t-168:t],axis=0)
        drawdown=c[t]/prior_peak-1.
        if np.median(drawdown)<-.08:
            direction=1. if np.median(r24)>0 else (-1. if np.median(r24)<0 else 0.)
            if direction:
                signals[t,3,0]=.5*direction
                signals[t,3,3]=.5*direction
        regime=("RISK_ON" if r336[0]>0 and np.count_nonzero(r168>0)>=3 else
                "RISK_OFF" if r336[0]<0 and np.count_nonzero(r168<0)>=3 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        updates[t]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DK_GROSS_SOURCE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
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
    return True

if __name__=="__main__":
    assert static_check()
    print("DK_CAUSAL_FACTOR_RATIO_SOURCE_STATIC_PASS")
