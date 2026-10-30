#!/usr/bin/env python3
"""IM preregistered causal conditional 72h cross-market shock-transmission seven-slot source.
No future holdout, benchmark internals, paper or live operations.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=72
GROSS={"STRESS":.80,"RECOVERY":.98,"NORMAL":.90}
PRIOR={"STRESS":np.array([.45,.20,.15,.20]),
       "RECOVERY":np.array([.40,.25,.15,.20]),
       "NORMAL":np.array([.62,.10,.18,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IM_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    prefix=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        q336=q[t-335:t+1]
        quality=np.sqrt(np.maximum(q336.mean(axis=0),1e-12))
        signals[t,0]=quality/quality.sum()
        # All source history used by the conditional model must have native nonzero quotes.
        valid=bool(np.all(q[t-671:t+1]>0))
        validity[t,1:]=valid
        regime="NORMAL"
        if valid:
            s=np.arange(t-672,t-71,dtype=int)  # latest s=t-72, labels end exactly at t
            market=np.median(lc[s]-lc[s-24],axis=1)
            threshold=2.*float(np.median(np.abs(market)))
            current=float(np.median(lc[t]-lc[t-24]))
            if threshold>0:
                state=-1 if current < -threshold else 1 if current>threshold else 0
                hist=np.where(market < -threshold,-1,np.where(market>threshold,1,0))
                selected=(hist==state)
                if int(np.count_nonzero(selected))>=12:
                    rows=s[selected]
                    # Label native funding events strictly AFTER historical decision s.
                    forward=lc[rows+72]-lc[rows]-(prefix[rows+73]-prefix[rows+1])
                    estimate=forward.mean(axis=0)
                    best=int(np.argmax(estimate));worst=int(np.argmin(estimate))
                    if state!=0 and float(estimate[best])>.012:
                        signals[t,1,best]=1.
                    if float(estimate[best]-estimate[worst])>.018:
                        signals[t,2,best]=.5
                        signals[t,2,worst]=-.5
                    if state==-1:
                        if float(estimate[worst])<-.012:
                            signals[t,3,worst]=-1.
                    elif float(estimate[best])>.012:
                        signals[t,3,best]=1.
                regime="STRESS" if state==-1 else "RECOVERY" if state==1 else "NORMAL"
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12)):
            raise ValueError("IM_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IM_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IM_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IM_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IM_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IM_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IM_SHOCK_TRANSMISSION_CAUSAL_AND_QUARANTINE_PASS")
