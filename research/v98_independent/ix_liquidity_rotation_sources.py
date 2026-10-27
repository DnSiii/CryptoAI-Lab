#!/usr/bin/env python3
"""IX preregistered native quote participation and long-only relative rotation seven-slot source, training only."""
from __future__ import annotations
import numpy as np
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.82,"RECOVERY":.98,"NORMAL":.93}
PRIOR={"STRESS":np.array([.70,.12,.08,.10]),
       "RECOVERY":np.array([.50,.22,.14,.14]),
       "NORMAL":np.array([.58,.18,.12,.12])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(a,dtype=float) for a in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (o,h,l,r,e,q)) or
        any(not np.isfinite(a).all() for a in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IX_INVALID_NATIVE_SOURCE")
    n=len(c)
    x=np.zeros_like(c)
    x[1:]=np.diff(np.log(c),axis=0)-r[1:]*e[1:]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        sl=slice(t-671,t+1)
        m168=np.sum(x[t-167:t+1],axis=0)
        m336=np.sum(x[t-335:t+1],axis=0)
        m672=np.sum(x[sl],axis=0)
        participation=np.clip(4.*np.sum(q[t-167:t+1],axis=0)/
                              (np.sum(q[sl],axis=0)+1e-12),0.,4.)
        drawdown=np.log(c[t]/np.max(c[sl],axis=0))
        valid=bool(np.all(q[sl]>0))
        validity[t,1:]=valid
        signals[t,0]=np.array([.45,.20,.15,.20])
        regime=("STRESS" if np.median(m168)<0. and np.median(participation)>1. else
                "RECOVERY" if np.median(m168)>0. and np.median(participation)>1. else
                "NORMAL")
        if valid:
            opportunity=m168*np.minimum(participation,2.)/(1.+np.abs(drawdown))
            signals[t,1,int(np.argmax(opportunity))]=1.
            rv=m672[1:]-np.median(m672[1:])+.25*m336[1:]+.10*drawdown[1:]
            signals[t,2,1+int(np.argmax(rv))]=1.
            if regime=="STRESS":
                resilience=m168+.5*drawdown
                signals[t,3,int(np.argmax(resilience))]=1.
            else:
                recovery=m336*np.minimum(participation,2.)
                signals[t,3,int(np.argmax(recovery))]=1.
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
            raise ValueError("IX_SEVEN_SLOT_FINANCING_INVALID")
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
    for z in (c2,o2,h2,l2):z[3200:]*=1.8
    q2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IX_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IX_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IX_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IX_CORE_GROSS_CONSERVATION")
    qgap=q.copy()
    qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IX_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IX_LIQUIDITY_ROTATION_CAUSAL_QUARANTINE_PASS")
