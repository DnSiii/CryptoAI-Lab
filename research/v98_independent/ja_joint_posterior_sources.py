#!/usr/bin/env python3
"""V98 JA preregistered seven-slot joint posterior portfolio, source only, no PnL."""
from __future__ import annotations
import numpy as np
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={'NORMAL':1.0,'STRESS':.85,'RECOVERY':.95}
PATHS=('JA_core_only','JA_full','JA_minus_opportunity','JA_minus_RV','JA_minus_stress')
COEFFICIENTS=np.array([.65,.15,.12,.08],dtype=float)

def _project(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError('JA_NONFINITE_OPTIMIZER')
    if np.max(np.abs(v))<1e-14:v=np.ones(4)/4.
    a=np.abs(v)
    lo,hi=0.,1.
    while np.minimum(.6,a*hi).sum()<1. and hi<1e14:hi*=2.
    for _ in range(55):
        mid=(lo+hi)/2.
        if np.minimum(.6,a*mid).sum()<1.:lo=mid
        else:hi=mid
    w=np.sign(v)*np.minimum(.6,a*hi)
    if not np.isclose(np.abs(w).sum(),1.,atol=1e-10):raise ValueError('JA_GROSS_PROJECT')
    return w

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(z,dtype=float) for z in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape or not np.isfinite(z).all() for z in (o,h,l,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError('JA_INVALID_SOURCE')
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,'NORMAL',dtype='<U10')
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.tile(np.full(4,.25),(5,1))
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x168=net[t-167:t+1]
        x48=net[t-47:t+1]
        x120=net[t-167:t-47]
        vol672=np.maximum(np.std(x672,axis=0),.002)
        vol168=np.maximum(np.std(x168,axis=0),.002)
        r168=x168.sum(axis=0)
        r48=x48.sum(axis=0)
        drawdown=np.log(c[t]/np.max(c[t-167:t+1],axis=0))
        ratio=float(np.median(vol168/vol672))
        regime=('STRESS' if np.median(r168)<0 and ratio>1.15 else
                'RECOVERY' if np.median(r48)>0 and np.median(drawdown)<-.05 else 'NORMAL')
        regimes[t]=regime
        slow=x672.sum(axis=0)
        rawcore=np.maximum(slow,0.)/vol672
        if rawcore.sum()<1e-12:rawcore=1./vol672
        core_ref=rawcore/rawcore.sum()
        f0=slow/672.
        priorq=np.mean(q[t-167:t+1],axis=0)
        q48=np.mean(q[t-47:t+1],axis=0)
        participation=np.clip(q48/np.maximum(priorq,1e-12),.5,1.5)
        f1=(r48/48.-x120.sum(axis=0)/120.)*participation
        f2=r168/168.
        downside=np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0))
        if regime=='STRESS':f3=-downside
        elif regime=='RECOVERY':f3=r48/48.-r168/168.-drawdown/168.
        else:f3=-downside
        f=np.array([f0,f1,f2,f3])
        f=np.clip(f-np.median(f,axis=1,keepdims=True),-.002,.002)
        forecasts[t]=f
        good=bool(np.all(q[t-167:t+1]>0))
        valid[t]=good
        if good:
            covariance=np.cov(x672,rowvar=False)+.0001*np.eye(4)
            a=8.*covariance+.0004*np.eye(4)
            for i in range(5):
                if i==0:
                    target=core_ref.copy()
                else:
                    coefficients=COEFFICIENTS.copy()
                    if i>=2:coefficients[i-1]=0.
                    coefficients/=coefficients.sum()
                    mu=coefficients@f
                    optimum=np.linalg.solve(a,mu)
                    proposal=.65*previous[i]+.35*optimum+.15*core_ref
                    target=_project(proposal)
                targets[t,i]=target
                previous[i]=target
        else:
            # Quarantine each asset with any invalid prior-window quote;
            # a zero-quote asset must never receive even Core fallback.
            safe=np.all(q[t-167:t+1]>0,axis=0)
            fallback=core_ref*safe
            if fallback.sum()>0:fallback/=fallback.sum()
            targets[t]=fallback
            previous[:]=fallback
        updates[t]=True
        if (not np.all(np.isfinite(targets[t])) or
            not np.allclose(np.abs(targets[t]).sum(axis=1),1. if (good or np.any(targets[t])) else 0.,atol=1e-10) or
            (np.any(np.abs(targets[t,1:])>.60000000001) and good)):
            raise ValueError('JA_TARGET_BUDGET_INVALID')
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=3600
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+.04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);r[:,2]=-.0001
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError('JA_FUTURE_MUTATION_'+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-10):
        raise ValueError('JA_GROSS_CONSERVATION')
    qgap=q.copy();qgap[700,2]=0.
    gap=bundle(o,h,l,c,r,e,qgap)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]) or np.any(gap[0][WARMUP,:,2]):
        raise ValueError('JA_QUOTE_QUARANTINE')
    return True

if __name__=='__main__':
    assert static_check()
    print('JA_CAUSAL_POSTERIOR_BUDGET_AND_QUARANTINE_PASS')
