#!/usr/bin/env python3
"""HZ preregistered quote-acceleration composed seven-slot native source; completed t close -> t+1 open."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"TREND":.72,"TRANSITION":.68,"STRESS":.58}
PRIOR={"TREND":np.array([.52,.18,.16,.14]),
       "TRANSITION":np.array([.50,.20,.16,.14]),
       "STRESS":np.array([.44,.14,.18,.24])}

def capped_simplex(raw):
    """Unique projection of a positive vector onto sum=1, 0.05<=w_i<=0.75."""
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("HZ_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(np.min(x)-1.);hi=float(np.max(x)+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        s=float(np.clip(x-mid,.05,.75).sum())
        if s>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("HZ_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HZ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n24=net(t,24);prev24=net(t-24,24)
        n72=net(t,72);prev72=net(t-72,72)
        n168=net(t,168);n336=net(t,336)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        growth=np.maximum(.20,np.exp(np.clip(n336,-5.,5.)))/semi
        signals[t,0]=growth/growth.sum()
        qnew=np.sum(q[t-23:t+1],axis=0)
        qprev=np.sum(q[t-47:t-23],axis=0)
        if np.any(qnew<=0) or np.any(qprev<=0):
            raise ValueError("HZ_ZERO_QUOTE_EPOCH")
        volratio=np.clip(qnew/qprev,.5,2.)
        opp=(n24-prev24)*volratio
        signals[t,1,int(np.argmax(opp))]=1.
        rank=np.argsort(-n168,kind="stable")
        signals[t,2,int(rank[0])]=.5
        signals[t,2,int(rank[-1])]=-.5
        stress=bool(n72[0]<-.05 or np.median(n72)<-.035)
        if stress:
            signals[t,3,int(np.argmin(n72))]=-1.
        else:
            signals[t,3,int(np.argmax(n72-prev72))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n168>0)>=3 else "TRANSITION"
        regimes[t]=regime
        expert_risk=np.maximum(np.abs(signals[t])@semi,.002)
        budgets[t]=capped_simplex(PRIOR[regime]/expert_risk)
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.75+1e-12) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.allclose(gross,1.,atol=1e-12) or
            not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("HZ_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,native_valid

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
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HZ_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HZ_EPOCH_BUDGET_CONSERVATION")
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-12):
        raise ValueError("HZ_SIGNED_SLEEVE_GROSS_CONSERVATION")
    for raw in (np.array([1.,1.,1.,1.]),np.array([1e-9,1e-9,1e-9,1e9])):
        z=capped_simplex(raw)
        if not np.isclose(z.sum(),1.,atol=1e-12) or np.any(z<.05-1e-12) or np.any(z>.75+1e-12):
            raise ValueError("HZ_SIMPLEX")
    return True

if __name__=="__main__":
    assert static_check()
    print("HZ_QUOTE_ACCELERATION_CAUSAL_SOURCE_PASS")
