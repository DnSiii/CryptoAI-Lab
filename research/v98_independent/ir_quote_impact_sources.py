#!/usr/bin/env python3
"""IR preregistered native quote-price-impact resilience; 2023-24 training only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.78,"RECOVERY":.92,"NORMAL":.88}
PRIOR={"STRESS":np.array([.63,.12,.10,.15]),
       "RECOVERY":np.array([.57,.19,.12,.12]),
       "NORMAL":np.array([.62,.16,.12,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(a,dtype=float) for a in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (o,h,l,r,e,q)) or
        any(not np.isfinite(a).all() for a in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IR_INVALID_NATIVE_SOURCE")
    n=len(c)
    x=np.zeros_like(c)
    x[1:]=np.diff(np.log(c),axis=0)-r[1:]*e[1:]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        window=x[t-671:t+1]
        quote_window=q[t-671:t+1]
        valid=bool(np.all(quote_window>0))
        validity[t,1:]=valid
        average_quote=np.maximum(np.mean(quote_window,axis=0),1.)
        scale=np.sqrt(np.maximum(quote_window,1.)/average_quote)
        signed_impact=window/scale
        impact=np.maximum(np.mean(np.abs(signed_impact),axis=0),1e-6)
        resilience=np.clip(
            np.sum(signed_impact,axis=0)/
            (np.sum(np.abs(signed_impact),axis=0)+1e-8),-1.,1.)
        renewal=np.clip(
            np.mean(quote_window[-168:],axis=0)/
            np.maximum(np.mean(quote_window[:-168],axis=0),1e-12),
            .25,4.)
        trend=np.sum(window[-336:],axis=0)
        downside=np.sum(np.maximum(-signed_impact[-168:],0.),axis=0)
        z=float(np.median(resilience))
        u=float(np.median(renewal))
        core=np.sqrt(average_quote)/(impact+1e-6)*np.maximum(.1,1.+trend)
        if np.any(~np.isfinite(core)) or np.sum(core)<=0:
            raise ValueError("IR_CORE_INVALID_IMPACT")
        signals[t,0]=core/np.sum(core)
        if valid:
            signals[t,1,int(np.argmax(resilience*renewal))]=1.
            score=resilience/(impact+1e-6)
            order=np.argsort(score,kind="stable")
            leader=int(order[-1])
            laggard=int(order[0])
            if leader==laggard:
                raise ValueError("IR_RELATIVE_VALUE_NOT_DISTINCT")
            signals[t,2,leader]=.5
            signals[t,2,laggard]=-.5
            if z<0:
                signals[t,3,int(np.argmax(downside/(impact+1e-6)))]=-1.
            else:
                signals[t,3,int(np.argmax(trend*renewal/(impact+1e-6)))]=1.
        regime=("STRESS" if z<0 and u<1 else
                "RECOVERY" if z>=0 and u>=1 else
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
            raise ValueError("IR_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c)
    e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (c2,o2,h2,l2):
        z[3200:]*=1.8
    q2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IR_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IR_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IR_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IR_CORE_GROSS_CONSERVATION")
    qgap=q.copy()
    qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IR_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IR_QUOTE_IMPACT_CAUSAL_AND_QUARANTINE_PASS")
