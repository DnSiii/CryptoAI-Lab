#!/usr/bin/env python3
"""IP preregistered distributional-tail seven-slot signals, 2023-2024 TRAINING ONLY."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.72,"RECOVERY":.90,"NORMAL":.90}
PRIOR={"STRESS":np.array([.58,.10,.12,.20]),
       "RECOVERY":np.array([.48,.22,.12,.18]),
       "NORMAL":np.array([.55,.18,.15,.12])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IP_INVALID_NATIVE_SOURCE")
    n=len(c)
    x=np.zeros_like(c)
    x[1:]=np.diff(np.log(c),axis=0)-r[1:]*e[1:]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        window=x[t-335:t+1]
        valid=bool(np.all(q[t-335:t+1]>0))
        validity[t,1:]=valid
        sorted_x=np.sort(window,axis=0)
        upper=np.mean(np.maximum(sorted_x[-12:],0.),axis=0)
        lower=np.mean(np.maximum(-sorted_x[:12],0.),axis=0)
        tail=np.clip((upper-lower)/(upper+lower+1e-8),-1.,1.)
        participation=np.mean(window>0,axis=0)
        jump=np.mean(np.abs(window)>2.*np.median(np.abs(window),axis=0),axis=0)
        vol=np.maximum(np.sqrt(np.mean(window*window,axis=0)),.0001)
        net72=np.sum(window[-72:],axis=0)
        liquidity=np.sqrt(np.mean(q[t-335:t+1],axis=0))
        core=liquidity/vol
        if np.any(~np.isfinite(core)) or np.sum(core)<=0:
            raise ValueError("IP_CORE_INVALID_LIQUIDITY")
        signals[t,0]=core/np.sum(core)
        if valid:
            eligible=(tail>0)&(participation>=.48)
            if np.any(eligible):
                score=np.where(eligible,tail*jump,-np.inf)
                signals[t,1,int(np.argmax(score))]=1.
            if np.max(tail)-np.min(tail)>=.05:
                signals[t,2,int(np.argmax(tail))]=.5
                signals[t,2,int(np.argmin(tail))]=-.5
            if np.median(net72)<0:
                signals[t,3,int(np.argmax(lower/vol))]=-1.
            else:
                signals[t,3,int(np.argmax(upper/vol))]=1.
        regime=("STRESS" if np.median(net72)<0 and np.median(jump)>=.18 else
                "RECOVERY" if np.median(net72)>0 and np.median(tail)<0 else
                "NORMAL")
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
            raise ValueError("IP_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IP_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IP_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IP_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IP_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IP_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IP_DISTRIBUTIONAL_TAIL_CAUSAL_AND_QUARANTINE_PASS")
