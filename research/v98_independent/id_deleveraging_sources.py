#!/usr/bin/env python3
"""ID preregistered inventory-absorption / native-funding-carry seven-slot source.
Signals only from completed t; execution at next actual open t+1.
2023-2024 Clean4 training; authenticated OI missing-day quarantine.
"""
from __future__ import annotations
import numpy as np
from ic_oi_crowding_sources import load_oi, ASSETS, HOURS, WARMUP, CLOCK

GROSS={"DELEVERAGING":.76,"LEVERAGED":.72,"BALANCED":.70}
PRIOR={"DELEVERAGING":np.array([.56,.20,.12,.12]),
       "LEVERAGED":np.array([.54,.12,.18,.16]),
       "BALANCED":np.array([.62,.14,.12,.12])}

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("ID_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.75).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.75)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("ID_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote,oi):
    o,h,l,c,r,e,q,v=[np.asarray(x,dtype=float) for x in
                     (opening,high,low,close,rate,event,quote,oi)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,v)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("ID_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"BALANCED",dtype="<U16")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        n24=net(t,24);n72=net(t,72);n336=net(t,336)
        returns=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(returns,0.)**2,axis=0)),.002)
        core=np.exp(np.clip(n336/semi,-1.,1.))
        signals[t,0]=core/core.sum()
        valid=bool(np.isfinite(v[t-168:t+1]).all())
        validity[t,1:]=valid
        regime="BALANCED"
        if valid:
            oi72=np.log(v[t]/v[t-72])
            med_oi=float(np.median(oi72))
            if med_oi<-.02:regime="DELEVERAGING"
            elif np.count_nonzero(oi72>0)>=3 and np.median(n72)>0:
                regime="LEVERAGED"
            # Inventory absorption: OI liquidation plus recent positive price drift.
            eligible=(oi72<0)&(n24>0)
            if np.any(eligible):
                score=-oi72+2.*n24
                signals[t,1,int(np.argmax(np.where(eligible,score,-np.inf)))]=1.
            # Native funding cash-flow transfer: short highest paid funding,
            # long lowest. Trailing 168h event-weighted funding, no price rank.
            carry=np.mean(r[t-167:t+1]*e[t-167:t+1],axis=0)
            rank=np.argsort(carry,kind="stable")
            signals[t,2,int(rank[0])]=.5
            signals[t,2,int(rank[-1])]=-.5
            # Systemic inventory fragility: short most crowded during OI build
            # and falling prices; otherwise long greatest deleveraging asset.
            fragility=bool(med_oi>0 and np.median(n72)<0)
            ix=int(np.argmax(oi72)) if fragility else int(np.argmin(oi72))
            signals[t,3,ix]=-1. if fragility else 1.
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
            raise ValueError("ID_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    c2,o2,h2,l2,q2,r2,v2=[x.copy() for x in (c,o,h,l,q,r,v)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.;v2[3200:]*=2.
    b=bundle(o2,h2,l2,c2,r2,e,q2,v2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("ID_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("ID_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("ID_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("ID_CORE_GROSS_CONSERVATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("ID_INVENTORY_ABSORPTION_CAUSAL_SOURCE_PASS")
