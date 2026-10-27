#!/usr/bin/env python3
"""IN preregistered native funding-conditioned trend/crowding seven-slot source.
2023-2024 TRAINING only; see in_funding_trend_prereg_20261027.md.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"STRESS":.78,"RECOVERY":.92,"NORMAL":.90}
PRIOR={"STRESS":np.array([.48,.12,.16,.24]),
       "RECOVERY":np.array([.42,.22,.12,.24]),
       "NORMAL":np.array([.52,.20,.12,.16])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IN_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signed=r*e
    prefix=np.vstack((np.zeros((1,4)),np.cumsum(signed,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(prefix[t+1]-prefix[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        quote336=q[t-335:t+1]
        ret=np.diff(lc[t-168:t+1],axis=0)
        sigma=np.maximum(np.sqrt(np.sum(ret**2,axis=0)),.001)
        core=np.sqrt(np.maximum(quote336.mean(axis=0),1e-12))/sigma
        signals[t,0]=core/core.sum()
        valid=bool(np.all(quote336>0))
        validity[t,1:]=valid
        n72=net(t,72);n168=net(t,168)
        regime=("STRESS" if np.median(n72)<0 and np.median(n168)<0 else
                "RECOVERY" if np.median(n72)>0 and np.median(n168)<0 else
                "NORMAL")
        if valid:
            funding168=prefix[t+1]-prefix[t-167]
            discount=funding168-np.median(funding168)
            score=n168/sigma-2.*discount/sigma
            eligible=n168>0
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,score,-np.inf)))
                signals[t,1,j]=1.
            hi=int(np.argmax(score));lo=int(np.argmin(score))
            if score[hi]-score[lo]>.20:
                signals[t,2,hi]=.5;signals[t,2,lo]=-.5
            stress_score=n72/sigma
            if np.median(n72)<0:
                signals[t,3,int(np.argmin(stress_score))]=-1.
            elif np.median(n168)>0:
                signals[t,3,int(np.argmax(stress_score))]=1.
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12)):
            raise ValueError("IN_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IN_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IN_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IN_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IN_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IN_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IN_FUNDING_TREND_CAUSAL_AND_QUARANTINE_PASS")
