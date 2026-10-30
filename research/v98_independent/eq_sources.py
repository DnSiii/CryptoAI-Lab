#!/usr/bin/env python3
"""EQ preregistered long-only three growth-sleeve complete V98 portfolio, 2023/24 only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=120
CORE={"TREND":2.6,"MIXED":2.2,"STRESS":1.6}
SLEEVES=np.array([.11,.11,.13])
GROSS_CAP=3.0

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EQ_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    qcum=np.cumsum(q,axis=0)
    q48=qcum.copy();q48[48:]-=qcum[:-48]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        net336=lc[t]-lc[t-336]-np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        breadth=int(np.count_nonzero(net336>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        down=np.sqrt(np.mean(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
        confirm=lc[t]-lc[t-72]
        score=np.where(confirm>0,np.maximum(net336,0.),0.)/np.maximum(down,1e-7)
        w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.20*np.full(4,.25)+.80*w
        net48=lc[t]-lc[t-48]-np.sum(r[t-47:t+1]*e[t-47:t+1],axis=0)
        alt=1+int(np.argmax(net48[1:]))
        if net48[alt]>0 and q48[t,alt]>np.median(q48[t-240:t,alt]):
            signals[t,1,alt]=1.
        carry=np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
        cheapest=int(np.argmin(carry))
        net120=lc[t]-lc[t-120]-np.sum(r[t-119:t+1]*e[t-119:t+1],axis=0)
        if np.median(carry)-carry[cheapest]>=.0003 and net120[cheapest]>0:
            signals[t,2,cheapest]=1.
        ret120=lc[t]-lc[t-120]
        ret24=lc[t]-lc[t-24]
        if np.mean(ret120)<0 and np.mean(ret24)>0 and np.count_nonzero(ret24>0)>=2:
            signals[t,3,int(np.argmax(ret24))]=1.
        requested=np.array([CORE[regime],*(
            SLEEVES[i-1] if np.any(signals[t,i]) else 0. for i in (1,2,3))])
        remaining=GROSS_CAP
        for i in range(4):
            budgets[t,i]=min(requested[i],remaining)
            remaining=max(0.,remaining-budgets[t,i])
        updates[t]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EQ_SOURCE_GROSS")
    if np.any(budgets<0) or not np.isfinite(budgets).all():
        raise ValueError("EQ_INVALID_BUDGET")
    if np.any(np.sum(budgets,axis=1)>GROSS_CAP+1e-12):
        raise ValueError("EQ_HIDDEN_GROSS")
    if np.any(signals<0):
        raise ValueError("EQ_LONG_ONLY_INVARIANT")
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
    print("EQ_LONG_ONLY_GROWTH_SEVENSLOT_CAUSAL_STATIC_PASS")
