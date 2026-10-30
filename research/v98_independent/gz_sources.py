#!/usr/bin/env python3
"""GZ preregistered weekly cash-option portfolio source; only completed close t."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":2.00,"TRANSITION":1.70,"STRESS":1.30}
PRIOR=np.array([.60,.20,.20,0.],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GZ_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net168,net336,net672=(native(t,w) for w in (168,336,672))
        previous168=(lc[t-168]-lc[t-336])-(funding[t-167]-funding[t-335])
        returns168=np.diff(lc[t-168:t+1],axis=0)
        returns672=np.diff(lc[t-672:t+1],axis=0)
        semivol168=np.maximum(np.sqrt(np.mean(np.minimum(returns168,0.)**2,axis=0)),.002)
        semivol672=np.maximum(np.sqrt(np.mean(np.minimum(returns672,0.)**2,axis=0)),.002)
        core=np.argsort(-net672/semivol168,kind="stable")[:2]
        signals[t,0,core[0]]=.70
        signals[t,0,core[1]]=.30
        recent_q=np.mean(q[t-167:t+1],axis=0)
        prior_q=np.mean(q[t-335:t-167],axis=0)
        ratio=np.clip((recent_q+1.)/(prior_q+1.),.5,2.)
        acceleration=(net168-previous168)*ratio
        signals[t,1,int(np.argmax(acceleration))]=1.
        burden=funding[t+1]-funding[t-167]
        vol=np.maximum(np.std(returns168,axis=0),.002)
        signals[t,2,int(np.argmax(-burden/vol))]=1.
        breadth=int(np.count_nonzero(net336>0))
        stress=((breadth<=2 and float(np.median(net168))<0.) or
                float(np.median(semivol168))>1.25*float(np.median(semivol672)))
        if stress:signals[t,3,0]=1. # flag ONLY, cash has no asset units
        regimes[t]="STRESS" if stress else "TREND" if breadth>=3 else "TRANSITION"
        if t>=WARMUP+CLOCK:
            past=signals[t-CLOCK,:3]
            elapsed=native(t,168)
            performance=np.einsum("ij,j->i",past,elapsed)
            multiplier=np.clip(np.exp(np.clip(2.*performance,-20.,20.)),.75,1.25)
        else:multiplier=np.ones(3)
        budgets[t,:3]=PRIOR[:3]*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t,:3]<=0) or
            not np.allclose(signals[t,:3].sum(axis=1),1.,atol=1e-12) or
            signals[t,3].sum() not in (0.,1.)):
            raise ValueError("GZ_INVALID_FINANCED_BOOK")
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
    print("GZ_WEEKLY_CASH_OPTION_CAUSAL_SOURCE_PASS")
