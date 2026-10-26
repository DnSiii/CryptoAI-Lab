#!/usr/bin/env python3
"""GY independent daily OHLC liquidation-wick absorption and wealth allocation.
Completed close t only; actual next-open execution belongs to gy_30cell.
"""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=24
GROSS={"TREND":2.00,"TRANSITION":1.80,"STRESS":1.50}
PRIOR=np.array([.55,.25,.20,0.],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GY_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net6,net24,net336,net672=(native(t,w) for w in (6,24,336,672))
        vol=np.maximum(np.std(np.diff(lc[t-168:t+1],axis=0),axis=0),.002)
        rank=np.argsort(-net672/vol,kind="stable")[:2]
        signals[t,0,rank[0]]=.60
        signals[t,0,rank[1]]=.40
        prevhigh=np.max(h[t-96:t],axis=0)
        native_funding24=funding[t+1]-funding[t-23]
        breakout=(c[t]/prevhigh-1.-native_funding24)/vol
        signals[t,1,int(np.argmax(breakout))]=1.
        burden=funding[t+1]-funding[t-167]
        signals[t,2,int(np.argmax(-burden/vol))]=1.
        # Positive lower wick: price rejected its intrabar low.
        lower=np.minimum(o[t-23:t+1],c[t-23:t+1])-l[t-23:t+1]
        span=h[t-23:t+1]-l[t-23:t+1]
        wick=np.mean(np.divide(lower,span,out=np.zeros_like(lower),
                               where=span>0),axis=0)
        recent_q=np.mean(q[t-23:t+1],axis=0)
        prior_q=np.mean(q[t-47:t-23],axis=0)
        ratio=np.clip((recent_q+1.)/(prior_q+1.),.5,2.)
        eligible=(wick>.30)&(net6>0)
        if float(np.median(net24))<-.015 and np.any(eligible):
            score=np.where(eligible,wick*ratio,-np.inf)
            signals[t,3,int(np.argmax(score))]=1.
        breadth=int(np.count_nonzero(net336>0))
        regimes[t]=("STRESS" if float(np.median(net24))<-.015 or breadth<=1 else
                    "TREND" if breadth>=3 else "TRANSITION")
        if t>=WARMUP+CLOCK:
            elapsed=native(t,168)
            prior_signal=signals[t-CLOCK,:3]
            returns=np.einsum("ij,j->i",prior_signal,elapsed)
            multiplier=np.clip(np.exp(np.clip(2.*returns,-20.,20.)),.75,1.25)
        else:
            multiplier=np.ones(3)
        budgets[t,:3]=PRIOR[:3]*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t,:3]<=0) or
            not np.allclose(signals[t,:3].sum(axis=1),1.,atol=1e-12) or
            signals[t,3].sum() not in (0.,1.)):
            raise ValueError("GY_INVALID_FINANCED_BOOK")
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
    assert np.allclose(a[0][ix,:3].sum(axis=2),1.)
    assert np.all(a[3][ix,:3]>0)
    return True
if __name__=="__main__":
    assert static_check()
    print("GY_CAUSAL_DAILY_WICK_ABSORPTION_STATIC_PASS")
