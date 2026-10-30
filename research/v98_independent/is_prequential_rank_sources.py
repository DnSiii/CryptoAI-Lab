#!/usr/bin/env python3
"""IS preregistered causal prequential rank-conviction composed portfolio, training only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.78,"RECOVERY":.92,"NORMAL":.90}
PRIOR={"STRESS":np.array([.66,.10,.10,.14]),
       "RECOVERY":np.array([.62,.16,.10,.12]),
       "NORMAL":np.array([.72,.14,.10,.04])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(a,dtype=float) for a in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (o,h,l,r,e,q)) or
        any(not np.isfinite(a).all() for a in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IS_INVALID_NATIVE_SOURCE")
    n=len(c)
    x=np.zeros_like(c)
    x[1:]=np.diff(np.log(c),axis=0)-r[1:]*e[1:]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    previous_raw=None
    for t in range(WARMUP,n,CLOCK):
        w=x[t-503:t+1]
        blocks=np.array([w[:168].sum(axis=0),
                         w[168:336].sum(axis=0),
                         w[336:].sum(axis=0)])
        B1,B2,B3=blocks
        R=blocks.sum(axis=0)
        V=np.maximum(np.sqrt(np.mean(w*w,axis=0)),.0001)
        E=(R-np.median(R))/(V*np.sqrt(504.))
        C=np.sum(blocks>np.median(blocks,axis=1)[:,None],axis=0)
        valid=bool(np.all(q[t-671:t+1]>0))
        validity[t,1:]=valid
        raw=np.zeros((4,4),dtype=float)
        inv=1./V
        raw[0]=.6*inv/inv.sum()
        raw[0,0]+=.4
        if valid:
            eligible=(C>=2)&(R>0)
            if np.any(eligible):
                raw[1,int(np.argmax(np.where(eligible,E,-np.inf)))]=1.
            if (np.max(C)>=2 and np.min(C)<=1 and
                np.max(E)-np.min(E)>.5):
                leader=int(np.argmax(E))
                laggard=int(np.argmin(E))
                if leader!=laggard:
                    raw[2,leader]=.5
                    raw[2,laggard]=-.5
        regime=("STRESS" if np.median(B3)<0 else
                "RECOVERY" if np.median(B3)>0 and
                np.median(B1+B2)<0 else "NORMAL")
        if valid and regime=="STRESS":
            raw[3,int(np.argmin(B3/V))]=-1.
        elif valid and regime=="RECOVERY":
            raw[3,int(np.argmax(B3/V))]=1.
        # Score only prior epoch's committed raw shadow signals against
        # prior epoch's core. Never score current signals on current history.
        if previous_raw is not None and valid:
            completed=x[t-CLOCK+1:t+1]
            for j in (1,2,3):
                if np.any(previous_raw[j]) and np.any(raw[j]):
                    score=float(np.sum(completed@(previous_raw[j]-previous_raw[0])))
                    if score>0:
                        signals[t,j]=raw[j]
        signals[t,0]=raw[0]
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        previous_raw=raw.copy()
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12) or
            signals[t,0,0]<.4-1e-12):
            raise ValueError("IS_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("IS_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IS_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IS_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IS_CORE_GROSS_CONSERVATION")
    qgap=q.copy()
    qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IS_ZERO_QUOTE_QUARANTINE")
    # Mutating future return labels must not alter a prior eligibility gate.
    return True

if __name__=="__main__":
    assert static_check()
    print("IS_PREQUENTIAL_CAUSAL_QUARANTINE_PASS")
