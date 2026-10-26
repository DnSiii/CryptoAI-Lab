#!/usr/bin/env python3
"""HC preregistered 96h funding-dislocation momentum and breadth-led recovery, causal t close only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=96
GROSS={"TREND":2.0,"TRANSITION":1.6,"STRESS":1.8}
PRIOR=np.array([.50,.20,.15,.15],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HC_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    f=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(f[t+1]-f[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net24,net96,net168,net336,net504=(net(t,w) for w in (24,96,168,336,504))
        hourly168=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly168,0.)**2,axis=0)),.002)
        core=np.argsort(-net336/semi,kind="stable")[:2]
        signals[t,0,core[0]]=.65
        signals[t,0,core[1]]=.35
        q96=np.mean(q[t-95:t+1],axis=0)
        qprior=np.mean(q[t-191:t-95],axis=0)
        funding96=f[t+1]-f[t-95]
        eligible=(net96>0)&(net96>np.median(net96))&(funding96<np.median(funding96))&(q96>qprior)
        if np.any(eligible):
            scores=np.where(eligible,net96,-np.inf)
            signals[t,1,int(np.argmax(scores))]=1.
        burden=f[t+1]-f[t-335]
        vol168=np.maximum(np.std(hourly168,axis=0),.002)
        signals[t,2,int(np.argmax(-burden/vol168))]=1.
        market_stress=float(np.median(net336))<0.
        positive=np.flatnonzero(net24>0)
        if market_stress and len(positive)>=2:
            best=positive[np.argsort(-net24[positive],kind="stable")[:2]]
            signals[t,3,best]=.5
        breadth=int(np.count_nonzero(net168>0))
        regimes[t]="STRESS" if market_stress else "TREND" if breadth>=3 else "TRANSITION"
        if t>=WARMUP+CLOCK:
            past=signals[t-CLOCK]
            elapsed=net96
            performance=past@elapsed
            multiplier=np.clip(np.exp(np.clip(2.*performance,-20.,20.)),.80,1.20)
        else:multiplier=np.ones(4)
        budgets[t]=PRIOR*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t]<=0) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12) or
            not np.isclose(signals[t,2].sum(),1.,atol=1e-12) or
            not all(np.isclose(signals[t,i].sum(),0.) or np.isclose(signals[t,i].sum(),1.) for i in (1,3))):
            raise ValueError("HC_INVALID_EXPERT_BOOK")
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
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    ix=np.arange(WARMUP,n,CLOCK)
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][ix].all(axis=1))
    assert np.allclose(a[0][ix,0].sum(axis=1),1.)
    assert np.allclose(a[0][ix,2].sum(axis=1),1.)
    assert np.all(a[3][ix]>0)
    return True
if __name__=="__main__":
    assert static_check()
    print("HC_CAUSAL_FUNDING_DISLOCATION_BREADTH_SOURCE_PASS")
