#!/usr/bin/env python3
"""GL preregistered trend efficiency, signed funding and payoff asymmetry 7-slot engine."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS_CAP=2.80
CORE={"GROWTH":2.30,"MIXED":1.85,"STRESS":1.20,"CROWDED":1.40}
COEFFICIENTS={"GROWTH":(.80,.55,.45),"MIXED":(.60,.75,.65),
              "STRESS":(.35,.85,.95),"CROWDED":(.50,.90,.80)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("GL_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net672,net336,net168=(native(t,w) for w in (672,336,168))
        ret168=np.diff(lc[t-168:t+1],axis=0)
        ret336=np.diff(lc[t-336:t+1],axis=0)
        vol168=np.maximum(np.std(ret168,axis=0),.002)
        score=(np.maximum(net336,0.)+.35*np.maximum(net672,0.))/vol168+.04
        signals[t,0]=score/score.sum()
        updates[t]=True

        funding168=cumulative[t+1]-cumulative[t-167]
        breadth=int(np.count_nonzero(net336>0))
        regime=("CROWDED" if float(np.mean(funding168))>.015
                else "GROWTH" if breadth>=3
                else "STRESS" if breadth<=1 else "MIXED")
        regimes[t]=regime
        budgets[t,0]=CORE[regime]
        a,b,d=COEFFICIENTS[regime]

        efficiency=net168/np.maximum(np.sum(np.abs(ret168),axis=0),.01)
        winner=int(np.argmax(efficiency));loser=int(np.argmin(efficiency))
        if winner!=loser and efficiency[winner]-efficiency[loser]>.08:
            signals[t,1,winner]=.24
            signals[t,1,loser]=-.24
            budgets[t,1]=a

        lowfund=int(np.argmin(funding168));highfund=int(np.argmax(funding168))
        if lowfund!=highfund and funding168[highfund]-funding168[lowfund]>.0005:
            signals[t,2,lowfund]=.18
            signals[t,2,highfund]=-.18
            budgets[t,2]=b

        positive=np.sum(np.maximum(ret336,0.),axis=0)
        negative=np.sum(-np.minimum(ret336,0.),axis=0)
        quality=np.log((positive+.01)/(negative+.01))
        receiver=int(np.argmax(quality));donor=int(np.argmin(quality))
        if receiver!=donor and quality[receiver]-quality[donor]>.10:
            signals[t,3,receiver]=.20
            signals[t,3,donor]=-.20
            budgets[t,3]=d

    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.abs(np.sum(signals[:,0,:],axis=1)[updates[:,0]]-1.)>1e-12) or
        np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(budgets[:,0]>GROSS_CAP+1e-12)):
        raise ValueError("GL_SCORE_OR_GROSS_INVARIANT")
    for t in np.flatnonzero(updates[:,0]):
        for omitted in (None,1,2,3):
            score=signals[t,0].copy()
            for i in (1,2,3):
                if i!=omitted:score+=signals[t,i]*budgets[t,i]
            score=np.maximum(score,0.)
            if not np.isfinite(score).all() or score.sum()<=0:
                raise ValueError("GL_SCORE_NONPOSITIVE")
            weights=score/score.sum()
            if (np.any(weights<0) or abs(weights.sum()-1.)>1e-12 or
                budgets[t,0]*weights.sum()>GROSS_CAP+1e-12):
                raise ValueError("GL_SINGLE_BOOK_CONSERVATION")
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
    print("GL_CAUSAL_STATIC_PASS")
