#!/usr/bin/env python3
"""JL preregistered native carry / liquidity / log-utility composed engine, TRAIN 2023-24."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JL_core_only","JL_full","JL_minus_opportunity","JL_minus_RV","JL_minus_stress")
PRIOR=np.array([.56,.18,.14,.12],dtype=float)
UTILITY_GAIN=100.
CORE_FLOOR=.50
INERTIA=.45

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JL_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def _allocation(experts,mean,cov,previous,disabled):
    # One frozen, causal mean-variance log-growth proxy for the COMPLETE portfolio.
    # Expert means, covariance and turnover estimates use completed history only.
    score=np.array([float(v@mean-.5*v@cov@v-.0005*np.abs(v-previous).sum())
                    for v in experts])
    unnorm=PRIOR*np.exp(np.clip(UTILITY_GAIN*score,-2.,2.))
    if disabled is not None:unnorm[disabled]=0.
    if unnorm.sum()<=0:raise ValueError("JL_ZERO_ALLOCATOR")
    w=unnorm/unnorm.sum()
    if w[0]<CORE_FLOOR:
        w[1:]*=(1.-CORE_FLOOR)/w[1:].sum()
        w[0]=CORE_FLOOR
    return w

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JL_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.zeros((5,4),dtype=float)
    first=True
    for t in range(WARMUP,n,CLOCK):
        x504=net[t-503:t+1]
        x336=net[t-335:t+1]
        x168=net[t-167:t+1]
        x96=net[t-95:t+1]
        x72=net[t-71:t+1]
        drift504=x504.sum(axis=0)
        drift168=x168.sum(axis=0)
        drift96=x96.sum(axis=0)
        vol504=np.maximum(np.std(x504,axis=0),.002)
        core_raw=np.maximum(drift504,0.)*np.maximum(drift168,0.)/vol504
        if core_raw.sum()<1e-12:core_raw=1./vol504
        core=core_raw/core_raw.sum()
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        index=np.mean(c[t-335:t+1]/c[t-335],axis=1)
        drawdown=1.-float(index[-1])/max(float(np.max(index)),1e-12)
        market72=float(x72.mean(axis=1).sum())
        marketvol=float(np.std(x168.mean(axis=1)))
        regime=("STRESS" if market72<-.07 and drawdown>.09 else
                "RECOVERY" if market72>.035 and drawdown>.07 else "NORMAL")
        regimes[t]=regime
        if good:
            funding336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
            quote96=np.mean(q[t-95:t+1],axis=0)
            quote336=np.mean(q[t-335:t+1],axis=0)
            capacity=np.minimum(quote96/np.maximum(quote336,1e-9),2.)
            # Opportunity: short crowd pays us negative signed native funding.
            opportunity=np.maximum(-funding336,0.)*np.maximum(drift96,0.)*capacity
            if np.any(opportunity>0):
                experts[1,int(np.argmax(opportunity))]=1.
            # RV: signed-funding-adjusted beta-residual, dollar neutral.
            market=x168.mean(axis=1)
            beta=np.mean((x168-x168.mean(axis=0))*
                         (market-market.mean())[:,None],axis=0)/max(float(np.var(market)),1e-10)
            residual=np.sum(x168-beta[None,:]*market[:,None],axis=0)
            rvscore=residual-funding336
            rank=np.argsort(rvscore,kind="stable")
            experts[2,int(rank[-1])]=.5
            experts[2,int(rank[0])]=-.5
            if regime=="STRESS":
                downside=np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0))
                rank=np.argsort(downside,kind="stable")
                experts[3,int(rank[0])]=.5
                experts[3,int(rank[-1])]=-.5
            elif regime=="RECOVERY":
                trough=np.min(l[t-335:t+1],axis=0)
                recovery=(c[t]-trough)/np.maximum(c[t],1e-9)
                eligible=np.where(drift96>0,recovery,-np.inf)
                if np.any(np.isfinite(eligible)):
                    experts[3,int(np.argmax(eligible))]=1.
            else:
                downside=np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0))
                # Distinct from RV: price downside-variance defensive spread.
                rank=np.argsort(downside,kind="stable")
                experts[3,int(rank[0])]=.5
                experts[3,int(rank[-1])]=-.5
        forecasts[t]=experts
        mean=x168.mean(axis=0)
        cov=np.cov(x336,rowvar=False)
        if cov.shape!=(4,4) or not np.isfinite(cov).all():
            raise ValueError("JL_BAD_COVARIANCE")
        for i in range(5):
            disabled=(None if i==1 else (1,2,3)[i-2] if i>=2 else None)
            w=_allocation(experts,mean,cov,previous[i],disabled)
            if i==0:
                w=np.array([1.,0.,0.,0.])
            proposed=_gross(w@experts)
            if not good:proposed=_gross(core)
            elif not first:proposed=_gross(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JL_GROSS_OR_QUARANTINE")
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
            raise ValueError("JL_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JL_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JL_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JL_CAUSAL_NATIVE_CARRY_JOINT_LOGGROWTH_QUARANTINE_PASS")
