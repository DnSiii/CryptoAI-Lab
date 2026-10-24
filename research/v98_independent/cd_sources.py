#!/usr/bin/env python3
"""CD independent slow structural seven-slot signals; training 2022-24 only.
All signals at completed close t, with no future input and no rejected alpha imports.
"""
from __future__ import annotations
import numpy as np

WARMUP=2160
PERIOD_CORE=1008
PERIOD_OPP=1008
PERIOD_RV=504
PERIOD_STRESS=168
BUDGETS={
    "BULL":np.array([1.60,.50,.25,0.00]),
    "RANGE":np.array([1.10,.30,.25,.25]),
    "CRISIS":np.array([.30,0.00,.20,.60]),
}

def bundle(close,rate,event):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all()
        or not np.isfinite(r).all() or not np.isfinite(e).all()
        or np.any(c<=0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CD_SOURCE_INPUT")
    n=len(c);log=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"RANGE",dtype="<U8")
    for t in range(WARMUP,n,PERIOD_STRESS):
        x=log[t-2160:t+1]
        now=x[-1]
        r72=now-x[-73]
        r168=now-x[-169]
        r720=now-x[-721]
        r2160=now-x[0]
        dd504=1.-c[t,0]/np.max(c[t-503:t+1,0])
        btc_geo=np.mean(log[t-2015:t+1,0])
        alt_geo=np.mean(log[t-1007:t+1],axis=0)
        regime=("CRISIS" if dd504>.18 and np.count_nonzero(r168<0)>=3 else
                "BULL" if log[t,0]>btc_geo and np.count_nonzero(now>alt_geo)>=3
                else "RANGE")
        regimes[t]=regime
        age=t-WARMUP
        if age%PERIOD_CORE==0:
            steps=np.diff(log[t-504:t+1],axis=0)
            downside=np.sqrt(np.mean(np.minimum(steps,0.)**2,axis=0))
            eligible=np.flatnonzero((r2160>0)&(r720>0))
            ranked=sorted(eligible,key=lambda j:(-r2160[j]/max(downside[j],.004),j))[:3]
            if ranked:
                inv=1./np.maximum(downside[ranked],.004)
                signals[t,0,ranked]=inv/inv.sum()
            updates[t,0]=True
            prior_high=np.max(c[t-504:t],axis=0)
            excess=c[t]/prior_high-1.
            funding=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
            eligible=np.flatnonzero((excess>.01)&(funding<np.median(funding)))
            if len(eligible):
                winner=sorted(eligible,key=lambda j:(-excess[j],j))[0]
                signals[t,1,winner]=1.
            updates[t,1]=True
        if age%PERIOD_RV==0:
            ratios=log[t-1008:t+1,1:]-log[t-1008:t+1,[0]]
            mean=ratios.mean(axis=0)
            std=ratios.std(axis=0)
            z=(ratios[-1]-mean)/np.maximum(std,.000001)
            cheap=int(np.argmin(z))
            rich=int(np.argmax(z))
            if cheap!=rich and z[rich]-z[cheap]>2.0:
                signals[t,2,cheap+1]=.5
                signals[t,2,rich+1]=-.5
            updates[t,2]=True
        if dd504>.18 and r168[0]<-.06:
            signals[t,3,0]=-1.
        elif dd504>.10 and r72[0]>.04:
            signals[t,3,0]=1.
        updates[t,3]=True
    if not np.all(np.sum(abs(signals),axis=2)<=1.+1e-12):
        raise ValueError("CD_GROSS_SOURCE")
    return signals,updates,regimes

def static_check():
    n=3100
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.04*np.sin(t[:,None]/73.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e)
    d=c.copy();d[2600:]*=2.
    r2=r.copy();r2[2600:]*=-1.
    s2,m2,z2=bundle(d,r2,e)
    assert np.array_equal(s[:2600],s2[:2600])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2600],z2[:2600])
    assert not s[:WARMUP].any()
    assert np.allclose(s[:,2].sum(axis=1),0.)
    assert not s[:,2,0].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("CD_INDEPENDENT_CAUSAL_SEVEN_SLOT_SOURCE_PASS")
