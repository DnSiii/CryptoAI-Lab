#!/usr/bin/env python3
"""JY preregistered conditional covariance growth allocator, V98 Independent.
Pinned Clean-4 native 1h closed t, execute at t+1 actual open, 2023-24 TRAINING only.
No 2025+, external engines, contaminated holdout, Frozen, paper or live orders.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"NORMAL":.88,"STRESS":.72,"RECOVERY":.84}
PATHS=("JY_core_only","JY_full","JY_minus_opportunity","JY_minus_RV","JY_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JY_INVALID_PINNED_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=np.mean(net,axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,3),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        # Every slice ends at the already-closed t; no t+1 data.
        past=net[t-335:t+1]
        mkt=market[t-335:t+1]
        neg=np.minimum(past,0.)
        downside=np.maximum(np.sqrt(np.mean(neg*neg,axis=0)),.002)
        mom672=np.sum(net[t-671:t+1],axis=0)
        leaders=np.argsort(-(mom672/downside),kind="stable")[:2]
        core=np.zeros(4)
        inv=1./downside[leaders]
        core[leaders]=inv/inv.sum()
        experts=np.zeros((4,4))
        experts[0]=core

        # Opportunity: completed-hour quote-weighted acceleration.
        q72=q[t-71:t+1]
        weight=q72/np.maximum(q72.sum(axis=0),1.)
        acceleration=(weight*net[t-71:t+1]).sum(axis=0)-np.mean(past,axis=0)
        if np.any(acceleration>0):
            experts[1,int(np.argmax(acceleration))]=1.
        else:
            experts[1]=core

        # Relative value: market-neutral 168h excess-return dispersion.
        volatility=np.maximum(np.sqrt(np.mean(past*past,axis=0)),.002)
        excess=net[t-167:t+1]-market[t-167:t+1,None]
        rv_score=np.sum(excess,axis=0)/volatility
        best=int(np.argmax(rv_score))
        worst=int(np.argmin(rv_score))
        if best==worst:raise ValueError("JY_RV_RANK_COLLISION")
        experts[2,best]=.5
        experts[2,worst]=-.5

        market72=float(np.sum(market[t-71:t+1]))
        market24=float(np.sum(market[t-23:t+1]))
        preceding72=float(np.sum(market[t-95:t-23]))
        rms72=float(np.sqrt(np.mean(market[t-71:t+1]**2)))
        rms336=float(np.sqrt(np.mean(mkt*mkt)))
        regime=("STRESS" if market72<-.02 and rms72>rms336 else
                "RECOVERY" if market24>.01 and preceding72<0 else "NORMAL")
        if regime=="STRESS":
            negative_market=mkt<0
            if not np.any(negative_market):
                chosen=int(np.argmax(mom672/downside))
            else:
                # Lowest conditional downside co-jump exposure; seeks
                # relative growth when the common market leg is negative.
                cojump=np.mean(np.minimum(past[negative_market],0.)*
                               mkt[negative_market,None],axis=0)
                chosen=int(np.argmin(cojump))
        elif regime=="RECOVERY":
            rebound=np.sum(net[t-23:t+1],axis=0)-np.mean(net[t-167:t+1],axis=0)*24.
            chosen=int(np.argmax(rebound))
        else:
            chosen=int(np.argmax(np.sum(net[t-167:t+1],axis=0)/downside))
        experts[3,chosen]=1.

        # Ex-ante joint capital competition against Core: fixed 336h
        # mark-to-market net asset observations, not prior engine PnL.
        core_hist=past@core
        var_core=float(np.var(core_hist))
        for k in range(1,4):
            candidate=past@experts[k]
            mean_delta=float(np.mean(candidate[-168:]-core_hist[-168:]))
            var_delta=float(np.var(candidate)-var_core)
            covariance=float(np.mean((candidate-candidate.mean())*
                                     (core_hist-core_hist.mean())))
            forecasts[t,k-1]=(mean_delta-.5*var_delta+
                              .25*(var_core-covariance)-.0008/CLOCK)
        budgets=np.where(forecasts[t]>0,.12,.04)
        budgets+=np.where(forecasts[t]>.00015,.04,0.)
        if np.sum(budgets)>.48+1e-12:raise ValueError("JY_BUDGET")
        for path in range(5):
            if path==0:
                target=core.copy()
            else:
                b=budgets.copy()
                if path>=2:b[path-2]=0.
                target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if not np.isfinite(target).all() or np.sum(np.abs(target))>1.+1e-10:
                raise ValueError("JY_GROSS_OR_FINITE")
            targets[t,path]=target
        regimes[t]=regime
        valid[t]=True
        updates[t]=True
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=3000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[v.copy() for v in (c,o,h,l,q,r)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JY_FUTURE_MUTATION_"+str(i))
    if np.any(np.abs(a[0][a[1]]).sum(axis=2)>1.+1e-10):
        raise ValueError("JY_STATIC_GROSS")
    return True

if __name__=="__main__":
    assert static_check()
    print("JY_CAUSAL_CONDITIONAL_COVARIANCE_PASS")
