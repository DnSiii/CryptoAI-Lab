#!/usr/bin/env python3
"""IF independent joint OI/taker positioning-flow convexity seven-slot causal source.
Preregistered before implementation: if_joint_flow_positioning_prereg_20261027.md.
All features completed close t; execution next actual open t+1; 2023-24 only.
"""
from __future__ import annotations
import numpy as np
from ic_oi_crowding_sources import load_oi,ASSETS,HOURS,WARMUP,CLOCK
from ie_taker_sources import load_taker

GROSS={"SQUEEZE":.76,"CROWD":.60,"BALANCED":.70}
PRIOR={"SQUEEZE":np.array([.54,.20,.14,.12]),
       "CROWD":np.array([.62,.12,.12,.14]),
       "BALANCED":np.array([.60,.16,.12,.12])}

def load_joint():
    oi,sha_oi=load_oi()
    taker,sha_taker=load_taker()
    if sha_oi!=sha_taker:
        raise ValueError("IF_JOINT_NATIVE_ARTIFACT_SHA_MISMATCH")
    return np.stack((oi,taker),axis=-1),sha_oi

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IF_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.75).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IF_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote,joint):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    v=np.asarray(joint,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        v.shape!=(*c.shape,2) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("IF_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"BALANCED",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n72=net(t,72);n336=net(t,336)
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        core=np.exp(np.clip(n336/(np.sqrt(336.)*semi),-2.,2.))
        signals[t,0]=core/core.sum()
        valid=bool(np.isfinite(v[t-168:t+1]).all() and
                   np.all(v[t-168:t+1]>0))
        validity[t,1:]=valid
        regime="BALANCED"
        if valid:
            oi72=np.log(v[t,:,0]/v[t-72,:,0])
            lr=np.clip(np.log(v[t-71:t+1,:,1]),-np.log(10.),np.log(10.))
            buy24=lr[-24:].mean(axis=0)
            buy72=lr.mean(axis=0)
            if np.median(oi72)<0 and np.count_nonzero(buy24>0)>=3:
                regime="SQUEEZE"
            elif np.median(oi72)>0 and np.median(n72)<0:
                regime="CROWD"
            opportunity=(-oi72)*np.maximum(buy24,0.)+.5*buy24
            signals[t,1,int(np.argmax(opportunity))]=1.
            disagreement=buy72-oi72
            rank=np.argsort(disagreement,kind="stable")
            signals[t,2,int(rank[-1])]=.5
            signals[t,2,int(rank[0])]=-.5
            stress=bool(np.count_nonzero(n72<0)>=3 and np.median(oi72)>0)
            if stress:
                fragility=oi72*np.maximum(-buy24,0.)
                signals[t,3,int(np.argmax(fragility))]=-1.
            else:
                recovery=(-oi72)*np.maximum(buy24,0.)
                signals[t,3,int(np.argmax(recovery))]=1.
        regimes[t]=regime
        risk=np.maximum(np.abs(signals[t])@semi,.002)
        risk=np.where(np.abs(signals[t]).sum(axis=1)>0,risk,.02)
        budgets[t]=capped_simplex(PRIOR[regime]/risk)
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.75+1e-12)
            or not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12))
            or not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("IF_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    oi=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    taker=np.exp(.25*np.sin(t[:,None]/79.+np.arange(4)))
    v=np.stack((oi,taker),axis=-1)
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    c2,o2,h2,l2,q2,r2,v2=[x.copy() for x in (c,o,h,l,q,r,v)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.;v2[3200:]*=2.
    b=bundle(o2,h2,l2,c2,r2,e,q2,v2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IF_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IF_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IF_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IF_CORE_GROSS_CONSERVATION")
    vgap=v.copy();vgap[700:711,2,1]=np.nan
    g=bundle(o,h,l,c,r,e,q,vgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IF_MISSING_JOINT_GAP_QUARANTINE")
    vzero=v.copy();vzero[700,1,1]=0.
    z=bundle(o,h,l,c,r,e,q,vzero)
    if np.any(z[0][WARMUP,1:]) or z[4][WARMUP,1:].any():
        raise ValueError("IF_ZERO_TAKER_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IF_JOINT_FLOW_POSITIONING_CAUSAL_AND_QUARANTINE_PASS")
