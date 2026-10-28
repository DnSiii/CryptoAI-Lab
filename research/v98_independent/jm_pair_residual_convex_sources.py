#!/usr/bin/env python3
"""JM precommitted seven-slot state-conditioned pair-residual/convex-crash source; 2023-24 only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JM_core_only","JM_full","JM_minus_opportunity","JM_minus_RV","JM_minus_stress")
BUDGET={"NORMAL":(.24,.16,.0),"STRESS":(.04,.10,.28),"RECOVERY":(.10,.12,.22)}
INERTIA=.25

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JM_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4,dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JM_INVALID_NATIVE_SOURCE")
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
        x336=net[t-335:t+1]
        x168=net[t-167:t+1]
        x96=net[t-95:t+1]
        x72=net[t-71:t+1]
        x24=net[t-23:t+1]
        drift336=x336.sum(axis=0)
        drift96=x96.sum(axis=0)
        drift72=x72.sum(axis=0)
        drift24=x24.sum(axis=0)
        downside=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.001)
        core_raw=np.maximum(drift336,0.)*np.maximum(drift96,0.)/downside
        if core_raw.sum()<1e-12:core_raw=1./downside
        core=core_raw/core_raw.sum()
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        market336=x336.mean(axis=1)
        market168=x168.mean(axis=1)
        volratio=float(np.std(market168)/max(np.std(market336),1e-7))
        market72=float(x72.mean(axis=1).sum())
        market24=float(x24.mean(axis=1).sum())
        market_prices=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        drawdown=1.-float(market_prices[-1])/max(float(market_prices.max()),1e-12)
        regime=("STRESS" if market72<-.025 and volratio>1.05 else
                "RECOVERY" if market24>.015 and drawdown>.06 else "NORMAL")
        regimes[t]=regime
        if good:
            # Volatility-contraction breakout: lagged close above 75th percentile
            # of preceding 168 completed hourly highs; no future bar.
            vol168=np.std(x168,axis=0)
            vol336=np.std(x336,axis=0)
            past_high_quantile=np.quantile(h[t-167:t],.75,axis=0)
            breakout=np.maximum(c[t]/past_high_quantile-1.,0.)
            opportunity_score=np.where(
                (vol168<vol336)&(drift72>0),drift72*breakout,0.)
            if np.any(opportunity_score>0):
                experts[1,int(np.argmax(opportunity_score))]=1.
            # Relative log-price ratio to contemporaneous equal-weight
            # market, using only t-335..t and signed native funding cost.
            logp=np.log(c[t-335:t+1])
            residual=logp-logp.mean(axis=1,keepdims=True)
            mu=residual.mean(axis=0)
            sd=np.maximum(residual.std(axis=0),.002)
            z=(residual[-1]-mu)/sd
            signed_funding=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
            value_score=-z-35.*signed_funding
            rank=np.argsort(value_score,kind="stable")
            experts[2,int(rank[-1])]=.5
            experts[2,int(rank[0])]=-.5
            # Conditional crash acceleration short or recovery long.
            if regime=="STRESS":
                acceleration=drift24-drift72/3.
                experts[3,int(np.argmin(acceleration))]=-1.
            elif regime=="RECOVERY":
                trough=np.min(l[t-167:t+1],axis=0)
                bounce=(c[t]-trough)/np.maximum(trough,1e-9)
                eligible=np.where(drift24>0,bounce,-np.inf)
                if np.any(np.isfinite(eligible)):
                    experts[3,int(np.argmax(eligible))]=1.
        forecasts[t]=experts
        for i in range(5):
            if i==0 or not good:
                proposed=core.copy()
            else:
                budgets=np.array(BUDGET[regime],dtype=float)
                if i>=2:budgets[i-2]=0.
                for k in range(3):
                    if np.abs(experts[k+1]).sum()<1e-12:budgets[k]=0.
                core_weight=1.-float(budgets.sum())
                if core_weight<.58-1e-12:raise ValueError("JM_CORE_FLOOR")
                proposed=_gross(core_weight*core+budgets@experts[1:])
                if not first:proposed=_gross(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JM_GROSS_OR_QUARANTINE")
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
            raise ValueError("JM_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JM_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JM_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JM_CAUSAL_PAIR_RESIDUAL_CONVEX_CRASH_QUARANTINE_PASS")
