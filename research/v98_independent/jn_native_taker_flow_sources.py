#!/usr/bin/env python3
"""JN precommitted seven-slot native aggressive-taker-flow source, 2023-24 TRAINING ONLY."""
from __future__ import annotations
import numpy as np
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JN_core_only","JN_full","JN_minus_opportunity","JN_minus_RV","JN_minus_stress")
BUDGET={"NORMAL":(.16,.12,.10),"STRESS":(.06,.10,.26),"RECOVERY":(.14,.12,.16)}
INERTIA=.60

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JN_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote,taker):
    o,h,l,c,r,e,q,z=[np.asarray(x,dtype=float) for x in
                     (opening,high,low,close,rate,event,quote,taker)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(v.shape!=c.shape for v in (o,h,l,r,e,q,z))
        or any(not np.isfinite(v).all() for v in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))
        or np.any((q>0)&(~np.isfinite(z)|(z<0)|(z>1.+1e-8)))):
        raise ValueError("JN_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    flow=np.where(np.isfinite(z),2.*z-1.,0.)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.zeros((5,4),dtype=float)
    first=True
    for t in range(WARMUP,n,CLOCK):
        x504=net[t-503:t+1];x336=net[t-335:t+1]
        x168=net[t-167:t+1];x72=net[t-71:t+1];x24=net[t-23:t+1]
        drift504=x504.sum(axis=0);drift168=x168.sum(axis=0)
        drift72=x72.sum(axis=0)
        downside=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.001)
        core_raw=np.maximum(drift504,0.)*np.maximum(drift168,0.)/downside
        if core_raw.sum()<1e-12:core_raw=1./downside
        core=core_raw/core_raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0) and np.all(np.isfinite(z[t-335:t+1]))
                  and np.all((z[t-335:t+1]>=0)&(z[t-335:t+1]<=1.+1e-8)))
        valid[t]=good
        mkt72=float(x72.mean(axis=1).sum())
        mkt24=float(x24.mean(axis=1).sum())
        mkt_flow168=float(np.mean(flow[t-167:t+1]))
        mktprice=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        drawdown=1.-float(mktprice[-1])/max(float(mktprice.max()),1e-12)
        regime=("STRESS" if mkt72<-.035 or mkt_flow168<-.06 else
                "RECOVERY" if mkt24>.012 and drawdown>.06 else "NORMAL")
        regimes[t]=regime
        if good:
            flow168=np.mean(flow[t-167:t+1],axis=0)
            flowprev168=np.mean(flow[t-335:t-167],axis=0)
            flow72=np.mean(flow[t-71:t+1],axis=0)
            flowprev72=np.mean(flow[t-143:t-71],axis=0)
            flow24=np.mean(flow[t-23:t+1],axis=0)
            # Opportunity: aggressive buy pressure confirmed by native-net drift.
            opportunity=np.where((flow168>0)&(drift72>0),flow168*drift72,0.)
            if np.any(opportunity>0):experts[1,int(np.argmax(opportunity))]=1.
            # RV: fixed flow-continuation direction with actual signed funding cost.
            funding168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            rvscore=(flow168-flowprev168)-8.*funding168
            order=np.argsort(rvscore,kind="stable")
            experts[2,int(order[-1])]=.5
            experts[2,int(order[0])]=-.5
            # State-specific native aggressive-order-flow tail/recovery response.
            if regime=="STRESS":
                experts[3,int(np.argmin(flow72))]=-1.
            elif regime=="RECOVERY":
                flip=flow24-flow72
                if np.any(flip>0):experts[3,int(np.argmax(flip))]=1.
            else:
                accel=flow72-flowprev72
                if np.any(accel>0):experts[3,int(np.argmax(accel))]=1.
        forecasts[t]=experts
        for i in range(5):
            if i==0 or not good:proposed=core.copy()
            else:
                budgets=np.array(BUDGET[regime],dtype=float)
                if i>=2:budgets[i-2]=0.
                for k in range(3):
                    if np.abs(experts[k+1]).sum()<1e-12:budgets[k]=0.
                cw=1.-float(budgets.sum())
                if cw<.58-1e-12:raise ValueError("JN_CORE_FLOOR")
                proposed=_gross(cw*core+budgets@experts[1:])
                if not first:proposed=_gross(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy();first=False;updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JN_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    z=np.clip(.50+.15*np.sin(t[:,None]/113.+np.arange(4)),.001,.999)
    a=bundle(o,h,l,c,r,e,q,z)
    cc,oo,hh,ll,qq,rr,zz=[v.copy() for v in (c,o,h,l,q,r,z)]
    for v in (cc,oo,hh,ll):v[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;zz[3200:]=1.-zz[3200:]
    b=bundle(oo,hh,ll,cc,rr,e,qq,zz)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JN_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JN_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    zbad=z.copy();zbad[700,2]=np.nan
    b=bundle(o,h,l,c,r,e,qgap,zbad)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JN_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JN_CAUSAL_NATIVE_TAKER_FLOW_QUARANTINE_PASS")
