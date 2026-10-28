#!/usr/bin/env python3
"""JE continuous spot-leading perp basis seven-slot causal source, 2023-2024 training only."""
from __future__ import annotations
import numpy as np
from hw_spot_perp_basis_loader import load_spot

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JE_core_only","JE_full","JE_minus_opportunity","JE_minus_RV","JE_minus_stress")
PRIOR=np.array([.60,.16,.14,.10],dtype=float)

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JE_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote,spot_close,spot_valid):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    spot=np.asarray(spot_close,dtype=float)
    mask=np.asarray(spot_valid,dtype=bool)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q,spot,mask))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))
        or not np.isfinite(spot[mask]).all() or np.any(spot[mask]<=0)):
        raise ValueError("JE_INVALID_NATIVE_OR_SPOT_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    logspot=np.log(np.where(mask,spot,1.))
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x168=net[t-167:t+1]
        n672=x672.sum(axis=0)
        n168=x168.sum(axis=0)
        n48=net[t-47:t+1].sum(axis=0)
        downside=np.maximum(np.sqrt(np.mean(np.minimum(x672,0.)**2,axis=0)),.002)
        raw=np.maximum(n672,0.)/downside
        if raw.sum()<1e-12:raw=1./downside
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(mask[t-168:t+1]) and np.all(q[t-168:t+1]>0))
        valid[t]=good
        regime="STRESS" if np.count_nonzero(n168<0)>=3 else "NORMAL"
        if good:
            s48=logspot[t]-logspot[t-48]
            lead=np.maximum(s48-n48,0.)*np.maximum(s48,0.)
            if np.any(lead>0):experts[1,int(np.argmax(lead))]=1.
            basis=np.log(c[t-167:t+1])-logspot[t-167:t+1]
            med=np.median(basis,axis=0)
            mad=np.median(np.abs(basis-med),axis=0)
            z=(basis[-1]-med)/np.maximum(1.4826*mad,.0005)
            experts[2,int(np.argmin(z))]=1.
            if regime!="STRESS" and np.count_nonzero(s48>0)>=2 and np.median(basis[-1]-basis[-49])<0:
                regime="RECOVERY"
            if regime=="STRESS":
                ix=int(np.argmax(s48-n48))
            else:
                ix=0
            experts[3,ix]=1.
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR.copy()
        cr=max(float(np.sqrt(np.mean(np.minimum(np.expm1(x168)@core,0.)**2))),.002)
        for j in range(1,4):
            if np.abs(experts[j]).sum()<1e-12:
                weights[j]=0.
            else:
                sr=max(float(np.sqrt(np.mean(np.minimum(np.expm1(x168)@experts[j],0.)**2))),.002)
                weights[j]*=np.clip(cr/sr,.5,1.5)
        opt=weights[1:].sum()
        if opt>.40:weights[1:]*=.40/opt
        weights[0]=1.-weights[1:].sum()
        if weights[0]<.60-1e-12:raise ValueError("JE_CORE_FLOOR")
        for i in range(5):
            w=weights.copy()
            if i==0:w[1:]=0.
            elif i>=2:w[i-1]=0.
            w[0]=1.-w[1:].sum()
            targets[t,i]=_gross(w@experts)
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or not np.allclose(np.abs(targets[t]).sum(axis=1),1.,atol=1e-10)
            or np.any(np.abs(targets[t])>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JE_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    s=c*(1.+.003*np.sin(t[:,None]/21.+np.arange(4)))
    valid=np.ones_like(c,dtype=bool);valid[2000:2002]=False;s[~valid]=np.nan
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,s,valid)
    cc,oo,hh,ll,qq,rr,ss=[z.copy() for z in (c,o,h,l,q,r,s)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;ss[3200:]*=.8
    b=bundle(oo,hh,ll,cc,rr,e,qq,ss,valid)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JE_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-10):
        raise ValueError("JE_GROSS_CONSERVATION")
    gap=valid.copy();gap[700,2]=False
    sg=s.copy();sg[700,2]=np.nan
    b=bundle(o,h,l,c,r,e,q,sg,gap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JE_SPOT_QUARANTINE")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap,s,valid)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JE_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JE_CAUSAL_SPOT_BASIS_QUARANTINE_PASS")
