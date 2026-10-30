#!/usr/bin/env python3
"""JG immutable range-compression, lagged residual and tail-asymmetry seven-slot source; training 2023-24."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JG_core_only","JG_full","JG_minus_opportunity","JG_minus_RV","JG_minus_stress")
PRIOR=np.array([.50,.20,.15,.15],dtype=float)

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JG_NONFINITE_TARGET")
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
        raise ValueError("JG_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    prev=np.vstack((c[:1],c[:-1]))
    tr=np.maximum.reduce((h-l,np.abs(h-prev),np.abs(l-prev)))/prev
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x168=net[t-167:t+1]
        prior168=net[t-335:t-167]
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
        mkt=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        stress=bool(np.count_nonzero(n168<0)>=3 or mkt[-1]<.90*float(np.max(mkt)))
        regime="STRESS" if stress else ("RECOVERY" if np.median(n48)>0 and np.median(n168)<0 else "NORMAL")
        if good:
            # Opportunity: lagged compression vs completed 24h impulse.
            impulse=net[t-23:t+1].sum(axis=0)-24.*net[t-167:t-23].mean(axis=0)
            prior_range=np.mean(tr[t-167:t-23],axis=0)
            recent_range=np.maximum(np.mean(tr[t-23:t+1],axis=0),1e-8)
            compression=np.clip(prior_range/recent_range,.5,2.)
            score=impulse*compression
            ix=int(np.argmax(np.maximum(score,0.))) if np.any(score>0) else int(np.argmax(score))
            experts[1,ix]=1.
            # RV: beta estimated only on PRECEDING 168h; no same-window fitting.
            prior_market=prior168.mean(axis=1)
            pmvar=max(float(np.var(prior_market)),1e-8)
            beta=np.mean((prior168-prior168.mean(axis=0))*
                         (prior_market[:,None]-prior_market.mean()),axis=0)/pmvar
            residual=n168-beta*float(np.mean(x168,axis=1).sum())
            order=np.argsort(residual,kind="stable")
            experts[2,int(order[0])]=.5
            experts[2,int(order[-1])]=-.5
            # Tail asymmetry is conditional on prior-only market regime.
            downside=np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0))
            if regime=="STRESS":
                lo=int(np.argmin(downside));hi=int(np.argmax(downside))
                if lo!=hi:
                    experts[3,lo]=.5;experts[3,hi]=-.5
                else:experts[3,lo]=1.
            elif regime=="RECOVERY":
                experts[3,int(np.argmax(n48-n168/3.))]=1.
            else:
                experts[3,int(np.argmin(downside))]=1.
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR.copy()
        if not good:weights[1:]=0.
        else:
            # Pairwise optional-expert crowding penalty; no historical PnL.
            for j in range(1,4):
                den=max(float(np.linalg.norm(experts[j])),1e-12)
                crowd=0.
                for k in range(1,4):
                    if k==j:continue
                    dk=max(float(np.linalg.norm(experts[k])),1e-12)
                    crowd+=abs(float(np.dot(experts[j],experts[k])))/(den*dk)
                weights[j]/=1.+crowd
        weights[0]=1.-float(weights[1:].sum())
        if weights[0]<.50-1e-12:raise ValueError("JG_CORE_FLOOR")
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
            raise ValueError("JG_GROSS_OR_QUARANTINE")
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
            raise ValueError("JG_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JG_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JG_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JG_CAUSAL_RANGE_RESIDUAL_TAIL_QUARANTINE_PASS")
