#!/usr/bin/env python3
"""ER complete causal 7-slot online-compounding candidate; authenticated 2023/24 training only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=48
CORE={"TREND":2.25,"MIXED":2.0,"STRESS":1.65}
SLEEVES=np.array([.13,.12,.15])
GROSS_CAP=2.8

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("ER_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    qc=np.cumsum(q,axis=0)
    q24=qc.copy();q24[24:]-=qc[:-24]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    history=[[] for _ in range(3)]
    for t in range(WARMUP,n,CLOCK):
        # The prior epoch was known at t-CLOCK; its return and funding settle by close t.
        if t>=WARMUP+CLOCK:
            previous=t-CLOCK
            net_episode=lc[t]-lc[previous]-np.sum(r[previous+1:t+1]*e[previous+1:t+1],axis=0)
            for k in range(3):
                if np.any(signals[previous,k+1]):
                    realized=float(signals[previous,k+1]@net_episode)-.0004
                    history[k].append(realized)
                    if len(history[k])>12:history[k].pop(0)
        net504=lc[t]-lc[t-504]-np.sum(r[t-503:t+1]*e[t-503:t+1],axis=0)
        breadth=int(np.count_nonzero(net504>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        down=np.sqrt(np.mean(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
        confirm=lc[t]-lc[t-168]
        score=np.where(confirm>0,np.maximum(net504,0.),0.)/np.maximum(down,1e-7)
        w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.15*np.full(4,.25)+.85*w
        net96=lc[t]-lc[t-96]-np.sum(r[t-95:t+1]*e[t-95:t+1],axis=0)
        prior_hi=np.max(h[t-168:t],axis=0)
        prior_lo=np.min(l[t-168:t],axis=0)
        range_pos=(c[t]-prior_lo)/np.maximum(prior_hi-prior_lo,1e-12)
        eligible=(net96[1:]>0)&(range_pos[1:]>.75)&(q24[t,1:]>np.median(q24[t-168:t,1:],axis=0))
        if eligible.any():
            ranked=np.where(eligible,net96[1:]*np.maximum(range_pos[1:],0.),-np.inf)
            signals[t,1,1+int(np.argmax(ranked))]=1.
        net168=lc[t]-lc[t-168]-np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net72=lc[t]-lc[t-72]-np.sum(r[t-71:t+1]*e[t-71:t+1],axis=0)
        carry=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        residual=net168-np.median(net168)
        eligible=(residual>0)&(net72>0)&(carry<=np.median(carry))
        if eligible.any():
            signals[t,2,int(np.argmax(np.where(eligible,residual,-np.inf)))]=1.
        ret168=lc[t]-lc[t-168];ret24=lc[t]-lc[t-24]
        if np.mean(ret168)<0 and np.mean(ret24)>0 and np.count_nonzero(ret24>0)>=2:
            signals[t,3,int(np.argmax(ret24))]=1.
        requested=np.zeros(4)
        requested[0]=CORE[regime]
        for k in range(3):
            if np.any(signals[t,k+1]):
                mean=float(np.mean(history[k])) if history[k] else 0.
                mult=float(np.clip(np.exp(np.clip(5.*mean,-10.,10.)),.50,1.40))
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
        raise ValueError("ER_GROSS_OR_SOURCE_INVARIANT")
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
    print("ER_PREQUENTIAL_CONVEX_GROWTH_CAUSAL_STATIC_PASS")
