#!/usr/bin/env python3
"""HF preregistered 96h beta-residual leadership and native-funding-assisted recovery, causal t close only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=96
GROSS={"TREND":2.0,"TRANSITION":1.6,"STRESS":1.8}
PRIOR=np.array([.45,.25,.15,.15],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HF_INVALID_PINNED_SOURCE")
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
        core=np.argsort(-net504/semi,kind="stable")[:2]
        signals[t,0,core[0]]=.70
        signals[t,0,core[1]]=.30
        # Opportunity: quote-volume-weighted close-location, using only completed bars.
        spread=np.maximum(h[t-47:t+1]-l[t-47:t+1],1e-10)
        clv=np.clip((c[t-47:t+1]-l[t-47:t+1])/spread,0.,1.)
        q48=np.mean(q[t-47:t+1],axis=0)
        qprev96=np.mean(q[t-143:t-47],axis=0)
        pressure=np.sum(clv*q[t-47:t+1],axis=0)/np.maximum(
            np.sum(q[t-47:t+1],axis=0),1e-10)
        hourly168=np.diff(lc[t-168:t+1],axis=0)
        vol168=np.maximum(np.std(hourly168,axis=0),.002)
        eligible=(pressure>.55)&(net96>0)&(q48>qprev96)
        if np.any(eligible):
            score=np.where(eligible,(pressure-.5)*net96/vol168,-np.inf)
            signals[t,1,int(np.argmax(score))]=1.
        # Relative Value: long the cheapest signed-funding burden per risk.
        burden=f[t+1]-f[t-167]
        signals[t,2,int(np.argmax(-burden/vol168))]=1.
        # Recovery: cross-market short-horizon reversal while long-horizon stressed.
        market_stress=float(np.median(net168))<0.
        market_recovery=market_stress and float(np.median(net24))>0.
        if market_recovery:
            score=np.where(net24>0,net24/semi,-np.inf)
            if np.any(np.isfinite(score)):
                signals[t,3,int(np.argmax(score))]=1.
        breadth=int(np.count_nonzero(net336>0))
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
            raise ValueError("HF_INVALID_EXPERT_BOOK")
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
    print("HF_CAUSAL_BETA_RESIDUAL_FUNDING_RECOVERY_SOURCE_PASS")
