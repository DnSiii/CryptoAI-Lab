#!/usr/bin/env python3
"""IO preregistered slow-horizon inventory seven-slot source, 2023-2024 only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=672
GROSS={"STRESS":.72,"RECOVERY":.88,"NORMAL":.88}
PRIOR={"STRESS":np.array([.56,.08,.12,.24]),
       "RECOVERY":np.array([.50,.22,.16,.12]),
       "NORMAL":np.array([.62,.16,.12,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IO_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    net_hour=np.zeros_like(c)
    net_hour[1:]=np.diff(lc,axis=0)-r[1:]*e[1:]
    prefix=np.vstack((np.zeros((1,4)),np.cumsum(net_hour,axis=0)))
    def net(t,w):
        return prefix[t+1]-prefix[t-w+1]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        signals[t,0]=.25
        valid=bool(np.all(q[t-671:t+1]>0))
        validity[t,1:]=valid
        n168=net(t,168);n672=net(t,672)
        regime=("STRESS" if np.count_nonzero(n168<0)>=3 else
                "RECOVERY" if np.count_nonzero(n168>0)>=3 and
                np.count_nonzero(n672<0)>=2 else "NORMAL")
        if valid:
            blocks=np.array([net(t-504,168),net(t-336,168),
                             net(t-168,168),net(t,168)])
            persistence=np.count_nonzero(blocks>0,axis=0)/4.
            score=persistence+.1*n672
            if np.max(persistence)>=.5:
                eligible=persistence>=.5
                j=int(np.argmax(np.where(eligible,score,-np.inf)))
                signals[t,1,j]=1.
            discount=lc[t]-np.mean(lc[t-671:t+1],axis=0)
            if np.min(discount)<0:
                signals[t,2,int(np.argmin(discount))]=1.
            path=c[t-671:t+1]
            running=np.maximum.accumulate(path,axis=0)
            drawdowns=np.max(1.-path/running,axis=0)
            signals[t,3,int(np.argmin(drawdowns))]=1.
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
            raise ValueError("IO_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IO_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IO_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IO_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IO_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IO_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IO_SLOW_HORIZON_CAUSAL_AND_QUARANTINE_PASS")
