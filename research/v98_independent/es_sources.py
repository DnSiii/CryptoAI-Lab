#!/usr/bin/env python3
"""ES independent multi-timescale complete 7-slot growth portfolio, TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=72
CORE={"TREND":2.15,"MIXED":1.85,"STRESS":1.40}
SLEEVES=np.array([.22,.20,.16])
GROSS_CAP=2.80

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("ES_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    qsum=np.cumsum(q,axis=0)
    q24=qsum.copy();q24[24:]-=qsum[:-24]
    mkt=np.mean(hourly,axis=1)
    v72=np.sqrt(np.convolve(mkt*mkt,np.ones(72)/72,mode="full")[:n])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        carry720=np.sum(r[t-719:t+1]*e[t-719:t+1],axis=0)
        carry240=np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
        net720=lc[t]-lc[t-720]-carry720
        net240=lc[t]-lc[t-240]-carry240
        net72=lc[t]-lc[t-72]-np.sum(r[t-71:t+1]*e[t-71:t+1],axis=0)
        net48=lc[t]-lc[t-48]-np.sum(r[t-47:t+1]*e[t-47:t+1],axis=0)
        net24=lc[t]-lc[t-24]-np.sum(r[t-23:t+1]*e[t-23:t+1],axis=0)
        vol240=np.sqrt(np.mean(hourly[t-239:t+1]**2,axis=0))
        regime="TREND" if np.count_nonzero(net720>0)>=3 else "STRESS" if np.count_nonzero(net720>0)<=1 else "MIXED"
        regimes[t]=regime
        core_score=np.where((net720>0)&(net240>0),np.maximum(net240,0),0)/np.maximum(vol240,1e-7)
        core_w=core_score/core_score.sum() if core_score.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.10*np.full(4,.25)+.90*core_w
        opp=(net240[1:]>0)&(net72[1:]>0)&(net24[1:]>0)&(q24[t,1:]>np.median(q24[t-96:t,1:],axis=0))
        if opp.any():
            j=1+int(np.argmax(np.where(opp,net72[1:],-np.inf)))
            signals[t,1,j]=1.
        relative=net240[1:]-net240[0]
        rv=(relative>0)&(net72[1:]>0)&(carry240[1:]<=np.median(carry240))
        if rv.any():
            j=1+int(np.argmax(np.where(rv,relative,-np.inf)))
            signals[t,2,j]=1.
        recovery=(v72[t]>np.median(v72[t-240:t]) and
                  float(np.mean(net48))>0 and np.count_nonzero(net48>0)>=2)
        if recovery:
            j=int(np.argmax(net48))
            if net48[j]>0:signals[t,3,j]=1.
        requested=np.zeros(4)
        requested[0]=CORE[regime]
        medvol=float(np.median(vol240))
        for k in range(3):
            if np.any(signals[t,k+1]):
                j=int(np.argmax(signals[t,k+1]))
                mult=float(np.clip(medvol/max(float(vol240[j]),1e-7),.70,1.20))
                requested[k+1]=SLEEVES[k]*mult
        remaining=GROSS_CAP
        for i in range(4):
            budgets[t,i]=min(requested[i],remaining)
            remaining=max(0.,remaining-budgets[t,i])
        updates[t]=True
    if (np.any(np.sum(abs(signals),axis=2)>1.+1e-12) or
        np.any(signals<0) or np.any(budgets<0) or
        not np.isfinite(budgets).all() or
        np.any(np.sum(budgets,axis=1)>GROSS_CAP+1e-12)):
        raise ValueError("ES_GROSS_OR_SOURCE_INVARIANT")
    return signals,updates,regimes,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
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
    assert np.all(np.isfinite(a[3]))
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    return True
if __name__=="__main__":
    assert static_check()
    print("ES_MULTI_TIMESCALE_CAUSAL_STATIC_PASS")
