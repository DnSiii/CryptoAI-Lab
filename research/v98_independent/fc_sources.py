#!/usr/bin/env python3
"""FC preregistered asynchronous four-clock growth/opportunity/RV/stress composition. TRAINING ONLY."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=24
GROSS_CAP=2.80
CORE={"TREND":2.20,"MIXED":1.70,"STRESS":1.20}
OPPORTUNITY=.07
RV=.06
STRESS=.06

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("FC_INVALID_PINNED_SOURCE")
    n=len(c)
    lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net672,net336,net168,net72,net24=(native(t,w) for w in (672,336,168,72,24))
        elapsed=t-WARMUP
        if elapsed%240==0:
            breadth=int(np.count_nonzero(net672>0))
            regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
            regimes[t]=regime
            vol=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0)+1e-6
            raw=np.maximum(net672,0.)/vol
            if raw.sum()>0:
                signals[t,0]=raw/raw.sum()
            else:
                signals[t,0,0]=.5
                signals[t,0,1]=.5
            budgets[t,0]=CORE[regime]
            updates[t,0]=True
        if elapsed%48==0:
            breadth168=int(np.count_nonzero(net168>0))
            accel=net24-.25*net168
            j=int(np.argmax(accel))
            if net24[j]>0 and breadth168>=2:
                signals[t,1,j]=1.
                budgets[t,1]=OPPORTUNITY
            updates[t,1]=True
        if elapsed%72==0:
            high_idx=int(np.argmax(net336))
            low_idx=int(np.argmin(net336))
            if high_idx!=low_idx and net336[high_idx]-net336[low_idx]>.04:
                signals[t,2,high_idx]=1.
                signals[t,2,low_idx]=-1.
                budgets[t,2]=RV
            updates[t,2]=True
        if float(np.mean(net72))<0.:
            j=int(np.argmin(net72))
            signals[t,3,j]=-1.
            budgets[t,3]=STRESS
        elif float(np.mean(net24))>0.:
            j=int(np.argmax(net24))
            signals[t,3,j]=1.
            budgets[t,3]=STRESS
        updates[t,3]=True
    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals[:,0,:]),axis=1)>1.+1e-12) or
        np.any(np.abs(np.sum(signals[:,2,:],axis=1))>1e-12) or
        np.any(np.sum(abs(signals[:,1:,:]),axis=2)>2.+1e-12) or
        np.any(np.sum(abs(signals)*budgets[:,:,None],axis=(1,2))>GROSS_CAP+1e-12)):
        raise ValueError("FC_GROSS_OR_SIGNED_FINANCING_INVARIANT")
    return signals,updates,regimes,budgets

def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.array_equal(a[1][WARMUP],np.ones(4,dtype=bool))
    assert int(a[1][:,0].sum())<int(a[1][:,1].sum())<int(a[1][:,3].sum())
    assert np.allclose(np.sum(a[0][:,2,:],axis=1),0.,atol=1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("FC_CAUSAL_STATIC_PASS")
