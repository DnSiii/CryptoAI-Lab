#!/usr/bin/env python3
"""HA precommitted 72h breakout / post-shock recovery; completed close only, no PnL."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=72
GROSS={"TREND":1.90,"TRANSITION":1.60,"STRESS":1.70}
PRIOR=np.array([.50,.25,.15,.10],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HA_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    f=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(f[t+1]-f[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net24,net72,net168,net336=(net(t,w) for w in (24,72,168,336))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        core=np.argsort(-net336/semi,kind="stable")[:2]
        signals[t,0,core[0]]=.70
        signals[t,0,core[1]]=.30
        q72=np.mean(q[t-71:t+1],axis=0)
        qprev=np.mean(q[t-143:t-71],axis=0)
        ratio=np.clip((q72+1.)/(qprev+1.),.5,2.)
        breakout=(np.log(c[t]/np.max(h[t-336:t],axis=0))+.5*net72)*ratio
        opportunity=int(np.argmax(breakout))
        if breakout[opportunity]>0:signals[t,1,opportunity]=1.
        burden=f[t+1]-f[t-167]
        vol=np.maximum(np.std(hourly,axis=0),.002)
        signals[t,2,int(np.argmax(-burden/vol))]=1.
        prior_high=np.max(h[t-168:t],axis=0)
        q336=np.mean(q[t-335:t+1],axis=0)
        valid=(net168<0)&(net24>0)&(c[t]<=.95*prior_high)&(q72>=.5*q336)
        if np.any(valid):
            score=np.where(valid,net24,-np.inf)
            signals[t,3,int(np.argmax(score))]=1.
        breadth=int(np.count_nonzero(net336>0))
        regimes[t]="STRESS" if np.any(valid) else "TREND" if breadth>=3 else "TRANSITION"
        if t>=WARMUP+CLOCK:
            past=signals[t-CLOCK]
            elapsed=net72
            performance=past@elapsed
            multiplier=np.clip(np.exp(np.clip(2.*performance,-20.,20.)),.75,1.25)
        else:multiplier=np.ones(4)
        budgets[t]=PRIOR*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t]<=0) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12) or
            not np.isclose(signals[t,2].sum(),1.,atol=1e-12) or
            not all(signals[t,i].sum() in (0.,1.) for i in (1,3))):
            raise ValueError("HA_INVALID_EXPERT_BOOK")
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
    print("HA_CAUSAL_BREAKOUT_REVERSAL_SOURCE_PASS")
