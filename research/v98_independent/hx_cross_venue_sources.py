#!/usr/bin/env python3
"""HX frozen cross-venue buyer-pressure divergence seven-slot USD-M source; t close -> t+1 open."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.60}
PRIOR={"TREND":np.array([.58,.20,.12,.10]),
       "TRANSITION":np.array([.58,.18,.14,.10]),
       "STRESS":np.array([.45,.18,.15,.22])}

def bundle(opening,high,low,close,rate,event,quote,spot_buy,spot_quote,spot_valid,perp_buy,perp_quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    sb,sq,pb,pq=[np.asarray(x,dtype=float) for x in (spot_buy,spot_quote,perp_buy,perp_quote)]
    valid=np.asarray(spot_valid,dtype=bool)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,sb,sq,pb,pq,valid)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q,pb,pq)) or
        not np.isfinite(sb[valid]).all() or not np.isfinite(sq[valid]).all() or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any(pq<0) or
        np.any((e!=0)&(e!=1)) or
        np.any(pb<0) or np.any(pb>pq+1e-5) or np.any((pq==0)&(pb!=0)) or
        np.any(sq[valid]<=0) or np.any(sb[valid]<0) or
        np.any(sb[valid]>sq[valid]+1e-5)):
        raise ValueError("HX_INVALID_NATIVE_OR_CROSS_VENUE_SOURCE")
    if not np.allclose(q,pq,rtol=1e-9,atol=1e-7):
        raise ValueError("HX_PERP_QUOTE_CANONICAL_MISMATCH")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        n72,n168,n336,n672=(net(t,w) for w in (72,168,336,672))
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.60,.40]
        eligible=bool(np.all(valid[t-167:t+1]))
        gap=np.zeros(4)
        if eligible:
            sden=np.sum(sq[t-167:t+1],axis=0)
            pden=np.sum(pq[t-167:t+1],axis=0)
            if np.any(sden<=0) or np.any(pden<=0):
                eligible=False
            else:
                gap=(np.sum(sb[t-167:t+1],axis=0)/sden-
                     np.sum(pb[t-167:t+1],axis=0)/pden)
        maximum=float(np.max(gap)) if eligible else 0.
        spread=float(np.max(gap)-np.min(gap)) if eligible else 0.
        if eligible:
            leader=int(np.argmax(gap));laggard=int(np.argmin(gap))
            if maximum>0. and n168[leader]>0.:
                signals[t,1,leader]=1.
            if spread>.02 and n336[leader]>0.:
                signals[t,2,leader]=.5
                signals[t,2,laggard]=-.5
        stress=(float(np.median(n72))<-.04 or float(n72[0])<-.06)
        if eligible:
            if stress:
                if maximum>0.:signals[t,3,int(np.argmax(gap))]=1.
            else:
                choices=np.flatnonzero(gap>0.)
                if len(choices):signals[t,3,int(choices[np.argmax(n168[choices])])]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime
        allocation=PRIOR[regime].copy()
        for i,scale in ((1,min(1.,maximum/.05)),(2,min(1.,spread/.10))):
            if np.any(signals[t,i]):
                delta=allocation[i]*(1.-scale)
                allocation[i]-=delta;allocation[0]+=delta
            else:
                allocation[0]+=allocation[i];allocation[i]=0.
        budgets[t]=allocation
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or np.any(budgets[t]<0) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(gross[0],1.,atol=1e-12) or
            np.any((budgets[t,1:3]==0)&(gross[1:3]>0))):
            raise ValueError("HX_SEVEN_SLOT_SIGNED_FINANCING_INVALID")
    return signals,updates,regimes,budgets,native_valid

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    sb=q*(.5+.10*np.sin(t[:,None]/101.+np.arange(4)))
    pb=q*(.5+.08*np.sin(t[:,None]/103.+np.arange(4)))
    valid=np.ones_like(c,dtype=bool)
    valid[2000:2002]=False
    sb[~valid]=np.nan
    sq=q.copy();sq[~valid]=np.nan
    a=bundle(o,h,l,c,r,e,q,sb,sq,valid,pb,q)
    c2,o2,h2,l2,q2,r2,sb2,pb2,sq2=[x.copy() for x in (c,o,h,l,q,r,sb,pb,sq)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;sq2[3200:]*=4.;sb2[3200:]*=4.;pb2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2,sb2,sq2,valid,pb2,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HX_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
            a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HX_EPOCH_BUDGET_CONSERVATION")
    for k in epochs:
        if not np.all(valid[k-167:k+1]) and np.any(a[0][k,1:]):
            raise ValueError("HX_SPOT_MASK_LEAK")
    return True
if __name__=="__main__":
    assert static_check()
    print("HX_CROSS_VENUE_CAUSAL_SOURCE_PASS")
