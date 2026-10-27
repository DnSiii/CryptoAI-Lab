#!/usr/bin/env python3
"""HS preregistered signed funding-carry and relative-strength spread seven-slot source.

DATA/SIGNAL ONLY. Native 8h funding, real signed shorts; no PnL or holdout.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"TREND":.72,"TRANSITION":.70,"STRESS":.65}
PRIOR={"TREND":np.array([.55,.20,.15,.10]),
       "TRANSITION":np.array([.45,.25,.20,.10]),
       "STRESS":np.array([.35,.25,.20,.20])}


def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HS_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        n24,n72,n168,n336=(net(t,w) for w in (24,72,168,336))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n336/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.60,.40]
        burden=funding[t+1]-funding[t-335]
        carry_order=np.argsort(burden,kind="stable")
        long_carry=int(carry_order[0]);short_carry=int(carry_order[-1])
        if long_carry==short_carry:raise ValueError("HS_FUNDING_SPREAD_SAME_ASSET")
        signals[t,1,long_carry]=.75
        signals[t,1,short_carry]=-.25
        strength=np.argsort(n168,kind="stable")
        long_strength=int(strength[-1]);short_strength=int(strength[0])
        if long_strength==short_strength:raise ValueError("HS_RV_SPREAD_SAME_ASSET")
        signals[t,2,long_strength]=.65
        signals[t,2,short_strength]=-.35
        stress=float(np.median(n72))<-.08
        if stress:
            shock_order=np.argsort(n72,kind="stable")
            signals[t,3,int(shock_order[-1])]=.25
            signals[t,3,int(shock_order[0])]=-.75
        else:
            signals[t,3,int(np.argmax(n24))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0)>=3 else "TRANSITION"
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.allclose(np.sum(np.abs(signals[t]),axis=1),1.,atol=1e-12) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            np.any(budgets[t]<=0)):
            raise ValueError("HS_SIGNED_SEVEN_SLOT_BOOK_INVALID")
    return signals,updates,regimes,budgets,native_valid


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
            raise ValueError("HS_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
            np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-12):
        raise ValueError("HS_SIGNED_EPOCH_CONSERVATION")
    if not (np.all((a[0][epochs,1]<0).any(axis=1)) and
            np.all((a[0][epochs,1]>0).any(axis=1)) and
            np.all((a[0][epochs,2]<0).any(axis=1))):
        raise ValueError("HS_SIGNED_PAIR_MISSING")
    return True


if __name__=="__main__":
    if not static_check():raise SystemExit(2)
    print("HS_SIGNED_CARRY_SEVEN_SLOT_CAUSAL_SOURCE_PASS")
