#!/usr/bin/env python3
"""JI preregistered range efficiency / wick rejection / liquidity shock, 2023-24 TRAINING ONLY."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JI_core_only","JI_full","JI_minus_opportunity","JI_minus_RV","JI_minus_stress")
PRIOR=np.array([.55,.20,.125,.125],dtype=float)
INERTIA=.65

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JI_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JI_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.zeros((5,4),dtype=float)
    first=True
    for t in range(WARMUP,n,CLOCK):
        x336=net[t-335:t+1]
        x168=net[t-167:t+1]
        n336=x336.sum(axis=0)
        n168=x168.sum(axis=0)
        n24=net[t-23:t+1].sum(axis=0)
        down336=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.002)
        efficiency=np.abs(n336)/np.maximum(np.sum(np.abs(x336),axis=0),1e-12)
        raw=np.maximum(n336,0.)*efficiency/down336
        if raw.sum()<1e-12:raw=1./down336
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        range24=(h[t-23:t+1]-l[t-23:t+1])/np.maximum(c[t-23:t+1],1e-12)
        range168=(h[t-167:t+1]-l[t-167:t+1])/np.maximum(c[t-167:t+1],1e-12)
        shock=float(np.median(range24))/max(float(np.median(range168)),1e-9)
        stress=bool(np.count_nonzero(n168<0)>=3 and shock>=1.5)
        regime="STRESS" if stress else ("RECOVERY" if np.median(n24)>0 and np.count_nonzero(n168<0)>=2 else "NORMAL")
        confidence=np.zeros(4,dtype=float);confidence[0]=1.
        if good:
            # Opportunity: accepted range highs supported by accelerated native quote flow.
            prior_high=np.max(h[t-335:t-47],axis=0)
            prior_low=np.min(l[t-335:t-47],axis=0)
            close_loc=(c[t]-prior_low)/np.maximum(prior_high-prior_low,1e-9)
            vol_new=np.mean(q[t-47:t+1],axis=0)
            vol_old=np.mean(q[t-335:t-47],axis=0)
            accel=vol_new/np.maximum(vol_old,1e-9)-1.
            trend48=net[t-47:t+1].sum(axis=0)
            score=np.maximum(close_loc-.55,0.)*np.maximum(accel,0.)*np.maximum(trend48,0.)
            if np.any(score>0):
                idx=int(np.argmax(score))
                experts[1,idx]=1.
                confidence[1]=float(np.clip(score[idx]/.20,.25,1.))
            # Relative value: independent quote-weighted upper-vs-lower wick rejection.
            bars=np.maximum(h[t-167:t+1]-l[t-167:t+1],1e-9)
            upper=np.maximum(h[t-167:t+1]-np.maximum(o[t-167:t+1],c[t-167:t+1]),0.)
            lower=np.maximum(np.minimum(o[t-167:t+1],c[t-167:t+1])-l[t-167:t+1],0.)
            wick=(upper-lower)/bars
            q168=q[t-167:t+1]
            imbalance=np.sum(wick*q168,axis=0)/np.maximum(np.sum(q168,axis=0),1e-9)
            rank=np.argsort(imbalance,kind="stable")
            experts[2,int(rank[0])]=.5
            experts[2,int(rank[-1])]=-.5
            confidence[2]=float(np.clip((imbalance[rank[-1]]-imbalance[rank[0]])/.50,.25,1.))
            # Stress and recovery: downside semivol and realized close-location rebound.
            down168=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.0001)
            if regime=="STRESS":
                experts[3,int(np.argmin(down168))]=1.
            elif regime=="RECOVERY":
                low168=np.min(l[t-167:t+1],axis=0)
                rebound=(c[t]-low168)/np.maximum(np.max(h[t-167:t+1],axis=0)-low168,1e-9)
                experts[3,int(np.argmax(rebound))]=1.
            else:
                rank=np.argsort(down168,kind="stable")
                experts[3,int(rank[0])]=.5
                experts[3,int(rank[-1])]=-.5
            confidence[3]=1. if regime in ("STRESS","RECOVERY") else .5
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR*confidence
        weights[0]=1.-float(weights[1:].sum())
        if weights[0]<.55-1e-12:raise ValueError("JI_CORE_FLOOR")
        for i in range(5):
            w=weights.copy()
            if i==0:w[1:]=0.
            elif i>=2:w[i-1]=0.
            w[0]=1.-float(w[1:].sum())
            proposed=_gross(w@experts)
            # Zero-quote quarantine overrides target inertia; no stale optional exposure.
            if not good:proposed=_gross(core)
            elif not first:proposed=_gross(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JI_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JI_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JI_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JI_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JI_CAUSAL_RANGE_WICK_LIQUIDITY_QUARANTINE_PASS")
