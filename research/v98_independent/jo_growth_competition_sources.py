#!/usr/bin/env python3
"""JO complete seven-slot causal growth-capital competition. Precommitted, training-only."""
from __future__ import annotations
import numpy as np
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JO_core_only","JO_full","JO_minus_opportunity","JO_minus_RV","JO_minus_stress")
CAPS=np.array([.18,.18,.18],dtype=float)
INERTIA=.50

def _unit(w):
    w=np.asarray(w,dtype=float)
    if not np.isfinite(w).all():raise ValueError("JO_NONFINITE")
    gross=float(np.abs(w).sum())
    return w/gross if gross>1e-12 else np.zeros(4,dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(v.shape!=c.shape for v in (o,h,l,r,e,q))
        or any(not np.isfinite(v).all() for v in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JO_INVALID_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    clv=np.clip((2*c-h-l)/np.maximum(h-l,1e-12),-1.,1.)
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
        x72=net[t-71:t+1]
        x24=net[t-23:t+1]
        down336=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.001)
        down168=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.001)
        trend=.5*x336.sum(axis=0)+.5*x72.sum(axis=0)
        raw=np.maximum(trend,0.)/down336
        if raw.sum()<1e-12:raw=1./down336
        core=_unit(raw)
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        market72=float(np.mean(x72,axis=1).sum())
        market24=float(np.mean(x24,axis=1).sum())
        market168=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        drawdown=1.-float(market168[-1])/max(float(market168.max()),1e-12)
        regime=("STRESS" if market72<-.035 or drawdown>.12 else
                "RECOVERY" if market24>.012 and drawdown>.05 else "NORMAL")
        regimes[t]=regime
        if good:
            participation=np.mean(q[t-71:t+1],axis=0)/np.maximum(
                np.mean(q[t-239:t-71],axis=0),1e-12)
            clv72=np.mean(clv[t-71:t+1],axis=0)
            clv24=np.mean(clv[t-23:t+1],axis=0)
            drift72=np.sum(x72,axis=0)
            auction=np.where((drift72>0)&(clv24>0),
                             drift72*np.maximum(clv72,0.)*participation,0.)
            if np.any(auction>0):experts[1,int(np.argmax(auction))]=1.
            drift168=np.sum(x168,axis=0)
            rvscore=(drift168-np.mean(drift168))/down168
            if np.any(rvscore>0):experts[2,int(np.argmax(rvscore))]=1.
            if regime in ("STRESS","RECOVERY"):
                asset_dd=1.-c[t]/np.maximum(np.max(c[t-167:t+1],axis=0),1e-12)
                recovery=np.where((asset_dd>.04)&(clv24>0)&
                                  (np.sum(x24,axis=0)>0)&(participation>.9),
                                  clv24*np.sum(x24,axis=0)*participation,0.)
                if np.any(recovery>0):experts[3,int(np.argmax(recovery))]=1.
        forecasts[t]=experts
        # Prior-only mean/variance and signed native funding proxy: expected
        # marginal log wealth relative to a competing, independently financed Core.
        r168=ret[t-167:t+1]
        f168=(r*e)[t-167:t+1]
        expected=np.mean(r168,axis=0)-np.mean(f168,axis=0)
        covariance=np.cov(r168,rowvar=False,ddof=1)
        def proxy(w):
            return 168.*(float(w@expected)-.5*float(w@covariance@w))
        base_proxy=proxy(core)
        advantages=np.zeros(3,dtype=float)
        if good:
            for k in range(3):
                if np.abs(experts[k+1]).sum()>1e-12:
                    advantages[k]=proxy(experts[k+1])-base_proxy-(
                        .0009*np.abs(experts[k+1]-core).sum())
        for i in range(5):
            if i==0 or not good:
                proposed=core.copy()
            else:
                budgets=CAPS*np.minimum(1.,np.maximum(advantages,0.)/.04)
                if i>=2:budgets[i-2]=0.
                if budgets.sum()>.45:budgets*=.45/budgets.sum()
                proposed=_unit((1.-budgets.sum())*core+budgets@experts[1:])
                if not first:proposed=_unit(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.+1e-10)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JO_GROSS_OR_QUARANTINE")
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
            raise ValueError("JO_FUTURE_MUTATION_"+str(i))
    gap=q.copy();gap[700,2]=0.
    b=bundle(o,h,l,c,r,e,gap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JO_CAUSAL_GROWTH_COMPETITION_SOURCE_PASS")
