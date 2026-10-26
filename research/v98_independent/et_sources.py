#!/usr/bin/env python3
"""ET independent asynchronous seven-slot engine: causal TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=744
GROSS_CAP=2.80
CLOCKS=(168,72,120,48)
CORE={"TREND":1.95,"MIXED":1.70,"STRESS":1.45}
SLEEVES=(.24,.22,.18)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("ET_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    # Trailing completed 24h quote turnover, never future hours.
    cq=np.cumsum(q,axis=0)
    q24=cq.copy();q24[24:]-=cq[:-24]
    for t in range(WARMUP,n,24):
        due=[(t-WARMUP)%clock==0 for clock in CLOCKS]
        if not any(due):continue
        def net(window):
            debit=np.sum(r[t-window+1:t+1]*e[t-window+1:t+1],axis=0)
            return lc[t]-lc[t-window]-debit
        n336,n168,n96,n72,n48,n24=(net(w) for w in (336,168,96,72,48,24))
        vol=np.sqrt(np.mean(hourly[t-167:t+1]**2,axis=0))
        breadth=int(np.count_nonzero(n336>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        if due[0]:
            score=np.where((n336>0)&(n168>0),np.maximum(n168,0)/np.maximum(vol,1e-7),0.)
            weights=score/score.sum() if score.sum()>1e-12 else np.array([1.,0.,0.,0.])
            signals[t,0]=.15*np.array([1.,0.,0.,0.])+.85*weights
            budgets[t,0]=CORE[regime];updates[t,0]=True
        if due[1]:
            # Quote turnover median uses only completed prior 24h windows.
            eligible=(n168[1:]>0)&(n48[1:]>0)&(n24[1:]>0)&(
                q24[t,1:]>np.median(q24[t-168:t,1:],axis=0))
            if eligible.any():
                score=np.where(eligible,n48[1:]/np.maximum(vol[1:],1e-7),-np.inf)
                signals[t,1,1+int(np.argmax(score))]=1.
                budgets[t,1]=SLEEVES[0]
            updates[t,1]=True
        if due[2]:
            # Pure carry-cost quality within trend-confirmed assets; no return ranking.
            debit=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            eligible=(n336>0)&(n72>0)
            if eligible.any():
                j=int(np.argmin(np.where(eligible,debit,np.inf)))
                signals[t,2,j]=1.;budgets[t,2]=SLEEVES[1]
            updates[t,2]=True
        if due[3]:
            if (float(np.mean(n96))<0 and float(np.mean(n24))>0 and
                np.count_nonzero(n24>0)>=2):
                j=int(np.argmax(n24))
                if n24[j]>0:
                    signals[t,3,j]=1.;budgets[t,3]=SLEEVES[2]
            updates[t,3]=True
    if (np.any(np.sum(abs(signals),axis=2)>1.+1e-12) or
        np.any(signals<0) or np.any(budgets<0) or
        not np.isfinite(budgets).all() or
        sum([max(CORE.values()),*SLEEVES])>GROSS_CAP or
        np.any(np.sum(budgets,axis=1)>GROSS_CAP+1e-12)):
        raise ValueError("ET_GROSS_OR_SOURCE_INVARIANT")
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
    for i,clock in enumerate(CLOCKS):
        assert np.all(a[1][np.arange(WARMUP,n,clock),i])
    return True
if __name__=="__main__":
    assert static_check()
    print("ET_ASYNCHRONOUS_CAUSAL_STATIC_PASS")
