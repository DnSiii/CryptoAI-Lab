#!/usr/bin/env python3
"""JF: precommitted quote-pressure / funding dispersion / crash-beta causal seven-slot source, 2023-24 only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JF_core_only","JF_full","JF_minus_opportunity","JF_minus_RV","JF_minus_stress")
PRIOR=np.array([.55,.20,.15,.10],dtype=float)

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JF_NONFINITE_TARGET")
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
        raise ValueError("JF_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
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
        down672=np.maximum(np.sqrt(np.mean(np.minimum(x672,0.)**2,axis=0)),.002)
        raw=np.maximum(n672,0.)/down672
        if raw.sum()<1e-12:raw=1./down672
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(q[t-167:t+1]>0))
        valid[t]=good
        # All state classification uses only completed t and earlier observations.
        market=c[t-167:t+1]/c[t-167]
        mkt=np.mean(market,axis=1)
        stress=bool(np.count_nonzero(n168<0)>=3 or mkt[-1]<.90*float(np.max(mkt)))
        regime="STRESS" if stress else ("RECOVERY" if np.median(n48)>0 and np.median(n168)<0 else "NORMAL")
        if good:
            # Opportunity: 24h acceleration confirmed by causal quote-volume pressure.
            last24=net[t-23:t+1].sum(axis=0)
            prior144=net[t-167:t-23].mean(axis=0)*24.
            accel=last24-prior144
            qratio=np.mean(q[t-23:t+1],axis=0)/np.mean(q[t-167:t-23],axis=0)
            pressure=np.maximum(accel,0.)*np.clip(qratio,.5,2.)
            ix=int(np.argmax(pressure)) if np.any(pressure>0) else int(np.argmax(accel))
            experts[1,ix]=1.
            # RV: 168h signed native funding carry, scaled by native-net volatility.
            carry=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            vol=np.maximum(np.std(x168,axis=0),.002)
            scores=carry/vol
            ordered=np.argsort(scores,kind="stable")
            experts[2,int(ordered[0])]=.5
            experts[2,int(ordered[-1])]=-.5
            # Stress: beta-neutralized crash hedge; recovery: rebound; normal: low-downside long.
            if regime=="STRESS":
                market_net=np.mean(np.expm1(x168),axis=1)
                market_var=max(float(np.var(market_net)),1e-8)
                betas=np.mean((np.expm1(x168)-np.mean(np.expm1(x168),axis=0))*
                              (market_net[:,None]-np.mean(market_net)),axis=0)/market_var
                ixlo=int(np.argmin(betas));ixhi=int(np.argmax(betas))
                if ixlo!=ixhi:
                    experts[3,ixlo]=.5;experts[3,ixhi]=-.5
                else:
                    experts[3,ixlo]=1.
            elif regime=="RECOVERY":
                rebound=n48-n168/3.
                experts[3,int(np.argmax(rebound))]=1.
            else:
                down168=np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0))
                experts[3,int(np.argmin(down168))]=1.
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR.copy()
        if not good:weights[1:]=0.
        else:
            core_norm=max(float(np.linalg.norm(core)),1e-12)
            for j in range(1,4):
                en=float(np.linalg.norm(experts[j]))
                if en<1e-12:weights[j]=0.;continue
                cosine=abs(float(np.dot(core,experts[j])))/(core_norm*en)
                weights[j]*=1.-.5*np.clip(cosine,0.,1.)
        weights[0]=1.-float(weights[1:].sum())
        if weights[0]<.55-1e-12:raise ValueError("JF_CORE_FLOOR")
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
            raise ValueError("JF_GROSS_OR_QUARANTINE")
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
            raise ValueError("JF_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JF_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JF_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JF_CAUSAL_QUOTE_FUNDING_BETA_QUARANTINE_PASS")
