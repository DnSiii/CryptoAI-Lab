#!/usr/bin/env python3
"""GK causal online convex expert-mix seven-slot system; historical training 2023-2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS_CAP=2.80
CORE={"TREND":2.25,"ROTATION":1.85,"PANIC":1.30}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("GK_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"ROTATION",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    edges=np.zeros(4,dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    def expert(core,tilt):
        logits=np.log(core)+tilt
        p=np.exp(logits-np.max(logits))
        return p/p.sum()
    for t in range(WARMUP,n,CLOCK):
        net672,net168,net72=(native(t,w) for w in (672,168,72))
        ret168=np.diff(lc[t-168:t+1],axis=0)
        ret72=np.diff(lc[t-72:t+1],axis=0)
        vol168=np.maximum(np.std(ret168,axis=0),.002)
        vol72=np.maximum(np.std(ret72,axis=0),.002)
        score=np.maximum(net672,0.)/vol168+.05
        core=score/score.sum()
        signals[t,0]=core
        updates[t]=True
        breadth=int(np.count_nonzero(net672>0))
        regime="TREND" if breadth>=3 else "PANIC" if breadth<=1 else "ROTATION"
        regimes[t]=regime
        budgets[t,0]=CORE[regime]

        # Prior-epoch realized net returns update the expert edges at t close.
        if t>=WARMUP+CLOCK:
            realized=native(t,CLOCK)
            for i in (1,2,3):
                prev=signals[t-CLOCK,i]
                edge_gain=float(prev@realized-.001*np.sum(np.abs(prev)))
                edges[i]=.75*edges[i]+.25*edge_gain

        opportunity=net72/vol72
        winner=int(np.argmax(opportunity));loser=int(np.argmin(opportunity))
        if winner!=loser:
            tilt=np.zeros(4);tilt[winner]=.60;tilt[loser]=-.60
            signals[t,1]=expert(core,tilt)-core

        funding168=cumulative[t+1]-cumulative[t-167]
        lowfund=int(np.argmin(funding168));highfund=int(np.argmax(funding168))
        if lowfund!=highfund and funding168[highfund]-funding168[lowfund]>.0005:
            tilt=np.zeros(4);tilt[lowfund]=.50;tilt[highfund]=-.50
            signals[t,2]=expert(core,tilt)-core

        ret336=np.diff(lc[t-336:t+1],axis=0)
        downside=np.minimum(ret336,0.)
        basket_down=np.minimum(np.mean(ret336,axis=1),0.)
        beta=(np.sum(downside*basket_down[:,None],axis=0)/
              max(float(np.sum(basket_down**2)),1e-9))
        safe=int(np.argmin(beta));vulnerable=int(np.argmax(beta))
        if safe!=vulnerable and beta[vulnerable]-beta[safe]>.10:
            tilt=np.zeros(4);tilt[safe]=.50;tilt[vulnerable]=-.50
            signals[t,3]=expert(core,tilt)-core

        for i in (1,2,3):
            if np.any(np.abs(signals[t,i])>1e-12):
                z=np.clip(edges[i]/.02,-30.,30.)
                budgets[t,i]=.05+.15/(1.+np.exp(-z))

    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.abs(np.sum(signals[:,0,:],axis=1)[updates[:,0]]-1.)>1e-12) or
        np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(budgets[:,0]>GROSS_CAP+1e-12) or
        np.any(np.sum(budgets[:,1:],axis=1)>.60+1e-12)):
        raise ValueError("GK_SCORE_OR_CONVEX_BUDGET_INVARIANT")
    for t in np.flatnonzero(updates[:,0]):
        for omitted in (None,1,2,3):
            weights=signals[t,0].copy()
            for i in (1,2,3):
                if i!=omitted:weights+=signals[t,i]*budgets[t,i]
            if (not np.isfinite(weights).all() or np.min(weights)<-1e-12 or
                abs(weights.sum()-1.)>1e-12 or
                budgets[t,0]*weights.sum()>GROSS_CAP+1e-12):
                raise ValueError("GK_SINGLE_BOOK_CONSERVATION")
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
    print("GK_CAUSAL_STATIC_PASS")
