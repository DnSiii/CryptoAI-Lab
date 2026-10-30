#!/usr/bin/env python3
"""GJ preregistered multiplicative seven-slot cross-sectional compounding, 2023-2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS_CAP=2.80
CORE={"TREND":2.25,"TRANSITION":1.85,"PANIC":1.30}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("GJ_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net504,net168=(native(t,w) for w in (504,168))
        ret168=np.diff(lc[t-168:t+1],axis=0)
        vol=np.maximum(np.std(ret168,axis=0),.002)
        core=np.maximum(.5*net504+.5*net168,0.)/vol+.05
        signals[t,0]=core/core.sum()
        updates[t]=True

        corr=np.corrcoef(ret168,rowvar=False)
        if not np.isfinite(corr).all():
            corr=np.eye(4)
        offdiag=float((corr.sum()-np.trace(corr))/12.)
        breadth=int(np.count_nonzero(net168>0))
        regime=("TREND" if breadth>=3 and offdiag<.90
                else "PANIC" if breadth<=1 or offdiag>.95 else "TRANSITION")
        regimes[t]=regime;budgets[t,0]=CORE[regime]

        residual=net168-float(np.mean(net168))
        leader=int(np.argmax(residual));laggard=int(np.argmin(residual))
        if leader!=laggard and residual[leader]-residual[laggard]>.02:
            signals[t,1,leader]=.40
            signals[t,1,laggard]=-.40
            budgets[t,1]=.85

        funding168=cumulative[t+1]-cumulative[t-167]
        lowest=int(np.argmin(funding168));highest=int(np.argmax(funding168))
        if lowest!=highest and funding168[highest]-funding168[lowest]>.0005:
            signals[t,2,lowest]=.28
            signals[t,2,highest]=-.28
            budgets[t,2]=1.00

        trough=np.min(l[t-71:t+1],axis=0)
        peak=np.max(h[t-335:t+1],axis=0)
        quality=np.log(c[t]/trough)-.5*np.maximum(0.,np.log(peak/c[t]))
        receiver=int(np.argmax(quality));donor=int(np.argmin(quality))
        if receiver!=donor and quality[receiver]-quality[donor]>.015:
            signals[t,3,receiver]=.35
            signals[t,3,donor]=-.35
            budgets[t,3]=.75

    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.abs(np.sum(signals[:,0,:],axis=1)[updates[:,0]]-1.)>1e-12) or
        np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(budgets[:,0]>GROSS_CAP+1e-12)):
        raise ValueError("GJ_SCORE_OR_GROSS_INVARIANT")
    for t in np.flatnonzero(updates[:,0]):
        for omitted in (None,1,2,3):
            logits=np.log(signals[t,0].copy())
            for i in (1,2,3):
                if i!=omitted:logits+=signals[t,i]*budgets[t,i]
            weights=np.exp(logits-np.max(logits))
            weights/=weights.sum()
            if (not np.isfinite(weights).all() or np.any(weights<0) or
                abs(weights.sum()-1.)>1e-12 or
                budgets[t,0]*weights.sum()>GROSS_CAP+1e-12):
                raise ValueError("GJ_SINGLE_BOOK_CONSERVATION")
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
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2),0.,atol=1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("GJ_CAUSAL_STATIC_PASS")
