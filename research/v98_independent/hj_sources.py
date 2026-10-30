#!/usr/bin/env python3
"""HJ preregistered 96h online positive drift and rolling expert wealth allocation; causal completed-close only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=96
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.65}
PRIOR=np.array([.50,.20,.20,.10],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HJ_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    f=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(f[t+1]-f[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net24,net96,net168,net336,net672=(net(t,w) for w in (24,96,168,336,672))
        hourly168=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly168,0.)**2,axis=0)),.002)
        vol168=np.maximum(np.std(hourly168,axis=0),.002)
        core=np.argsort(-net672/semi,kind="stable")[:2]
        signals[t,0,core[0]]=.65
        signals[t,0,core[1]]=.35
        # Eight nonoverlapping fully elapsed 96h epoch native-net returns.
        if t>=8*CLOCK:
            epoch=np.stack([net(t-k*CLOCK,CLOCK) for k in range(8)])
            lower=epoch.mean(axis=0)-epoch.std(axis=0,ddof=1)/np.sqrt(8.)
            winner=int(np.argmax(lower))
            if lower[winner]>0.:
                signals[t,1,winner]=1.
        # Native signed funding efficiency is a separate independently ablated expert.
        burden=f[t+1]-f[t-167]
        signals[t,2,int(np.argmax(-burden/vol168))]=1.
        # Relative survivor under a broad 168h native-net drawdown.
        stress=float(np.median(net168))<0.
        if stress:
            relative=net24-float(np.mean(net24))
            signals[t,3,int(np.argmax(relative))]=1.
        breadth=int(np.count_nonzero(net336>0.))
        regimes[t]="STRESS" if stress else "TREND" if breadth>=3 else "TRANSITION"
        # Online causal expert wealth: only nonoverlapping completed past epochs.
        prior_epochs=min(4,(t-WARMUP)//CLOCK)
        history=np.zeros(4,dtype=float)
        for k in range(1,prior_epochs+1):
            past=signals[t-k*CLOCK]
            realized=net(t-(k-1)*CLOCK,CLOCK)
            history+=past@realized
        multiplier=np.clip(np.exp(np.clip(1.5*history,-20.,20.)),.50,2.0)
        budgets[t]=PRIOR*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t]<=0) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12) or
            not np.isclose(signals[t,2].sum(),1.,atol=1e-12) or
            not all(np.isclose(signals[t,i].sum(),0.) or np.isclose(signals[t,i].sum(),1.) for i in (1,3))):
            raise ValueError("HJ_INVALID_EXPERT_BOOK")
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
    print("HJ_CAUSAL_ONLINE_EXPERT_DRIFT_SOURCE_PASS")
