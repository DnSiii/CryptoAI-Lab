#!/usr/bin/env python3
"""JH preregistered capital-flow migration / dispersion / conditional recovery source, 2023-24 TRAINING only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JH_core_only","JH_full","JH_minus_opportunity","JH_minus_RV","JH_minus_stress")
PRIOR=np.array([.50,.20,.15,.15],dtype=float)

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JH_NONFINITE_TARGET")
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
        raise ValueError("JH_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x504=net[t-503:t+1]
        x168=net[t-167:t+1]
        n504=x504.sum(axis=0)
        n168=x168.sum(axis=0)
        n24=net[t-23:t+1].sum(axis=0)
        down504=np.maximum(np.sqrt(np.mean(np.minimum(x504,0.)**2,axis=0)),.002)
        raw=np.maximum(n504,0.)/down504
        if raw.sum()<1e-12:raw=1./down504
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(q[t-407:t+1]>0))
        valid[t]=good
        market=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        stress=bool(np.count_nonzero(n168<0)>=3 and market[-1]<=.92*float(np.max(market)))
        regime="STRESS" if stress else ("RECOVERY" if np.median(n24)>0 and np.count_nonzero(n168<0)>=2 else "NORMAL")
        confidence=np.zeros(4,dtype=float);confidence[0]=1.
        if good:
            # Complete quote-share history is observed before decision t.
            shares=q[t-407:t+1]/np.sum(q[t-407:t+1],axis=1)[:,None]
            prior336=np.mean(shares[:336],axis=0)
            latest72=np.mean(shares[336:],axis=0)
            shift=latest72/np.maximum(prior336,1e-9)-1.
            opportunity=n24*0. + net[t-71:t+1].sum(axis=0)*shift
            idx=int(np.argmax(np.maximum(opportunity,0.))) if np.any(opportunity>0) else int(np.argmax(opportunity))
            experts[1,idx]=1.
            confidence[1]=float(np.clip(abs(shift[idx])/.20,.25,1.))
            # Quote-share migration across two non-overlapping 168h windows.
            prior_share=np.mean(shares[72:240],axis=0)
            latest_share=np.mean(shares[240:408],axis=0)
            dispersion=np.maximum(np.std(shares[:336],axis=0),.005)
            z=np.log(np.maximum(latest_share,1e-9)/np.maximum(prior_share,1e-9))/dispersion
            rank=np.argsort(z,kind="stable")
            experts[2,int(rank[-1])]=.5
            experts[2,int(rank[0])]=-.5
            confidence[2]=float(np.clip((z[rank[-1]]-z[rank[0]])/2.,.25,1.))
            down168=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.0001)
            up168=np.sqrt(np.mean(np.maximum(x168,0.)**2,axis=0))
            if regime=="STRESS":
                score=n24/down168
                rank=np.argsort(score,kind="stable")
                if rank[0]!=rank[-1]:
                    experts[3,int(rank[-1])]=.5
                    experts[3,int(rank[0])]=-.5
                else:experts[3,int(rank[-1])]=1.
            elif regime=="RECOVERY":
                rebound=c[t]/np.min(c[t-167:t+1],axis=0)-1.
                experts[3,int(np.argmax(rebound))]=1.
            else:
                experts[3,int(np.argmax(up168/down168))]=1.
            confidence[3]=1. if regime in ("STRESS","RECOVERY") else .50
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR*confidence
        weights[0]=1.-float(weights[1:].sum())
        if weights[0]<.50-1e-12:raise ValueError("JH_CORE_FLOOR")
        for i in range(5):
            w=weights.copy()
            if i==0:w[1:]=0.
            elif i>=2:w[i-1]=0.
            w[0]=1.-float(w[1:].sum())
            targets[t,i]=_gross(w@experts)
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JH_GROSS_OR_QUARANTINE")
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
            raise ValueError("JH_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JH_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JH_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JH_CAUSAL_QUOTE_MIGRATION_QUARANTINE_PASS")
