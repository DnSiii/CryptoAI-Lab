#!/usr/bin/env python3
"""JD OI deleveraging breadth: preregistered complete seven-slot causal sources, 2023-2024 TRAINING only."""
from __future__ import annotations
import numpy as np
from ic_oi_crowding_sources import load_oi

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.0,"STRESS":.80,"RECOVERY":.95}
PATHS=("JD_core_only","JD_full","JD_minus_opportunity","JD_minus_RV","JD_minus_stress")
PRIOR=np.array([.65,.14,.11,.10],dtype=float)

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JD_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote,oi):
    o,h,l,c,r,e,q,v=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote,oi)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q,v))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))
        or np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("JD_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x168=net[t-167:t+1]
        x48=net[t-47:t+1]
        n672=x672.sum(axis=0)
        n168=x168.sum(axis=0)
        n48=x48.sum(axis=0)
        downside=np.maximum(np.sqrt(np.mean(np.minimum(x672,0.)**2,axis=0)),.002)
        semi168=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.002)
        raw=np.maximum(n672,0.)/downside
        if raw.sum()<1e-12:raw=1./downside
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        # Any missing OI or zero quote in a 169h decision window invalidates all optional sleeves.
        good=bool(np.isfinite(v[t-168:t+1]).all() and np.all(q[t-168:t+1]>0))
        valid[t]=good
        regime="STRESS" if np.count_nonzero(n168<0)>=3 else "NORMAL"
        if good:
            oi48=np.log(v[t]/v[t-48])
            if np.count_nonzero(n48>0)>=2 and np.median(oi48)<0 and regime!="STRESS":
                regime="RECOVERY"
            opportunity=np.maximum(-oi48,0.)*np.maximum(n48,0.)
            if np.any(opportunity>0):
                experts[1,int(np.argmax(opportunity))]=1.
            catchup=(n48-(48./168.)*n168)-.5*oi48
            if np.any(catchup>0):
                experts[2,int(np.argmax(catchup))]=1.
            if regime=="STRESS":
                eligible=np.where(n48>0)[0]
                ix=int(eligible[np.argmin(semi168[eligible])]) if len(eligible) else 0
            elif regime=="RECOVERY":
                ix=int(np.argmax(opportunity)) if np.any(opportunity>0) else 0
            else:
                ix=0
            experts[3,ix]=1.
        regimes[t]=regime
        forecasts[t]=experts
        # Fixed prior risk budgets, prior-only downside-risk transfer, Core floor .65.
        weights=PRIOR.copy()
        for j in range(1,4):
            if np.abs(experts[j]).sum()<1e-12:
                weights[j]=0.
            else:
                sr=np.maximum(np.sqrt(np.mean(np.minimum(np.expm1(x168)@experts[j],0.)**2)),.002)
                cr=np.maximum(np.sqrt(np.mean(np.minimum(np.expm1(x168)@core,0.)**2)),.002)
                weights[j]*=np.clip(cr/sr,.5,1.5)
        optional=weights[1:].sum()
        if optional>.35:weights[1:]*=.35/optional
        weights[0]=1.-weights[1:].sum()
        if weights[0]<.65-1e-12:raise ValueError("JD_CORE_FLOOR")
        for i in range(5):
            w=weights.copy()
            if i==0:w[1:]=0.
            elif i>=2:w[i-1]=0.
            w[0]=1.-w[1:].sum()
            targets[t,i]=_gross(w@experts)
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or not np.all(np.isclose(np.abs(targets[t]).sum(axis=1),1.,atol=1e-10))
            or np.any(np.abs(targets[t])>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JD_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    cc,oo,hh,ll,qq,rr,vv=[z.copy() for z in (c,o,h,l,q,r,v)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;vv[3200:]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,vv)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JD_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-10):
        raise ValueError("JD_GROSS_CONSERVATION")
    bad=v.copy();bad[700,2]=np.nan
    gap=bundle(o,h,l,c,r,e,q,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("JD_OI_QUARANTINE")
    qbad=q.copy();qbad[700,2]=0.
    gap2=bundle(o,h,l,c,r,e,qbad,v)
    if gap2[3][WARMUP] or not np.allclose(gap2[0][WARMUP],gap2[0][WARMUP,0]):
        raise ValueError("JD_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JD_CAUSAL_OI_BREADTH_QUARANTINE_PASS")
