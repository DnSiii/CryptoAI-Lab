#!/usr/bin/env python3
"""IL preregistered native OHLC intrabar auction rejection composed seven-slot causal source.
Pre-result contract: il_auction_rejection_prereg_20261027.md. Training 2023-24 only.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.72,"RECOVERY":.96,"NORMAL":.92}
PRIOR={"STRESS":np.array([.58,.10,.12,.20]),
       "RECOVERY":np.array([.48,.18,.14,.20]),
       "NORMAL":np.array([.55,.18,.17,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IL_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    prefix=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(prefix[t+1]-prefix[t-w+1])
    span=h-l
    denom=np.maximum(span,1e-12)
    body=(c-o)/denom
    rejection=(np.minimum(o,c)-l-(h-np.maximum(o,c)))/denom
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        quote336=q[t-335:t+1]
        span336=span[t-335:t+1]
        quality=np.sqrt(np.maximum(quote336.mean(axis=0),1e-12))
        signals[t,0]=quality/quality.sum()
        valid=bool(np.all(quote336>0) and np.all(span336>0))
        validity[t,1:]=valid
        n72=net(t,72);n168=net(t,168)
        if valid:
            q168=q[t-167:t+1]
            q72=q[t-71:t+1]
            score168=np.sum(q168*body[t-167:t+1],axis=0)/np.sum(q168,axis=0)
            score72=np.sum(q72*rejection[t-71:t+1],axis=0)/np.sum(q72,axis=0)
            eligible=(score168>0)&(n168>0)
            if np.any(eligible):
                score=np.where(eligible,score168,-np.inf)
                signals[t,1,int(np.argmax(score))]=1.
            highidx=int(np.argmax(score72))
            lowidx=int(np.argmin(score72))
            if float(score72[highidx]-score72[lowidx])>.02:
                signals[t,2,highidx]=.5
                signals[t,2,lowidx]=-.5
            if float(np.median(n72))<0:
                signals[t,3,lowidx]=-1.
            else:
                signals[t,3,highidx]=1.
            regime=("STRESS" if float(np.median(n72))<0 and
                    float(np.median(score72))<0 else
                    "RECOVERY" if float(np.median(n72))<0 else "NORMAL")
        else:
            regime="NORMAL"
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
            raise ValueError("IL_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IL_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IL_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IL_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IL_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IL_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IL_NATIVE_AUCTION_CAUSAL_AND_QUARANTINE_PASS")
