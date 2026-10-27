#!/usr/bin/env python3
"""IA preregistered conditional carry dislocation and quote breakout seven-slot source.
Completed t close -> next t+1 actual open; no holdout or benchmarks.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"TREND":.72,"TRANSITION":.68,"STRESS":.58}
PRIOR={"TREND":np.array([.62,.14,.10,.14]),
       "TRANSITION":np.array([.72,.12,.08,.08]),
       "STRESS":np.array([.82,.06,.06,.06])}

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IA_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.80).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.80)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IA_BUDGET_PROJECTION")
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
        raise ValueError("IA_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signed_funding=r*e
    cum=np.vstack((np.zeros((1,4)),np.cumsum(signed_funding,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(cum[t+1]-cum[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n24=net(t,24);n72=net(t,72);n168=net(t,168);n336=net(t,336)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        growth=np.maximum(.10,np.exp(np.clip(n336,-2.,2.)))/semi
        signals[t,0]=growth/growth.sum()
        qnew=q[t-23:t+1].sum(axis=0)
        qprev=q[t-47:t-23].sum(axis=0)
        if np.any(qnew<=0) or np.any(qprev<=0):
            raise ValueError("IA_ZERO_QUOTE_EPOCH")
        valid_opp=(n72>.025)&(qnew>=1.10*qprev)
        if np.any(valid_opp):
            ix=int(np.argmax(np.where(valid_opp,n72,-np.inf)))
            signals[t,1,ix]=1.
        funding_168=cum[t+1]-cum[t-167]
        cheap=int(np.argmin(funding_168))
        expensive=int(np.argmax(funding_168))
        if (cheap!=expensive and funding_168[expensive]-funding_168[cheap]>.0015
            and n72[cheap]-n72[expensive]>=.005):
            signals[t,2,cheap]=.5
            signals[t,2,expensive]=-.5
        stress=bool(n72[0]<-.05 or np.median(n72)<-.035)
        if (not stress and np.count_nonzero(n168>0)>=3
            and np.median(n24)>.005):
            signals[t,3,int(np.argmax(n72))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n168>0)>=3 else "TRANSITION"
        regimes[t]=regime
        risk=np.maximum(np.abs(signals[t])@semi,.002)
        # Inactive optional sleeves keep their preregistered reserve until
        # their full allocation is transferred to Core at the next execution.
        risk=np.where(np.abs(signals[t]).sum(axis=1)>0,risk,.02)
        budgets[t]=capped_simplex(PRIOR[regime]/risk)
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.80+1e-12)
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12))
            or not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("IA_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

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
            raise ValueError("IA_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IA_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IA_OPTIONAL_SLEEVE_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IA_CORE_GROSS_CONSERVATION")
    for raw in (np.array([1.,1.,1.,1.]),np.array([1e-9,1e-9,1e-9,1e9])):
        z=capped_simplex(raw)
        if not np.isclose(z.sum(),1.,atol=1e-12) or np.any(z<.05-1e-12) or np.any(z>.80+1e-12):
            raise ValueError("IA_SIMPLEX")
    return True

if __name__=="__main__":
    assert static_check()
    print("IA_CONDITIONAL_CARRY_CAUSAL_SOURCE_PASS")
