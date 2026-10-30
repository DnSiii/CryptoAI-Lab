#!/usr/bin/env python3
"""CL preregistered seven-slot volume-weighted close-location-pressure sources.
OHLCV only through completed hour t; execution at t+1 in separate ledger.
"""
from __future__ import annotations
import numpy as np

WARMUP=2160
GRID=168
BUDGETS={
    "RISK_ON":np.array([1.80,.45,.25,.15]),
    "MIXED":np.array([1.35,.40,.30,.35]),
    "RISK_OFF":np.array([.70,.25,.45,.60]),
}

def bundle(open_,high,low,close,quote,rate,event):
    o,h,l,c,q,r,e=(np.asarray(v,dtype=float) for v in
                    (open_,high,low,close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP
        or any(x.shape!=c.shape for x in (o,h,l,q,r,e))
        or any(not np.isfinite(x).all() for x in (o,h,l,c,q,r,e))
        or np.any(l<=0) or np.any(q<0) or np.any(l>np.minimum(o,c))
        or np.any(h<np.maximum(o,c)) or np.any((e!=0)&(e!=1))):
        raise ValueError("CL_INVALID_OHLCV_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    clv=np.divide(2*c-h-l,h-l,out=np.zeros_like(c),where=(h>l))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        # Fixed 504h volume baseline known by completed close t.
        baseline=np.maximum(np.mean(q[t-503:t+1],axis=0),1e-12)
        weight=np.clip(np.sqrt(q[t-503:t+1]/baseline),.25,4.)
        flow=clv[t-503:t+1]*weight
        def score(window):
            a=flow[-window:];w=weight[-window:]
            return np.sum(a,axis=0)/np.maximum(np.sum(w,axis=0),1e-12)
        core_flow=score(504)
        breadth_flow=score(336)
        recent=score(48)
        preceding=(np.sum(flow[-96:-48],axis=0)/
                   np.maximum(np.sum(weight[-96:-48],axis=0),1e-12))
        rv_flow=score(168)
        r168=lc[t]-lc[t-168]
        r1008=lc[t]-lc[t-1008]
        breadth=int(np.count_nonzero(breadth_flow>0))
        regime=("RISK_ON" if breadth>=3 and r168[0]>0 else
                "RISK_OFF" if breadth<=1 and r168[0]<0 else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%336==0:
            eligible=[j for j in range(4) if core_flow[j]>.05 and r1008[j]>0]
            ranked=sorted(eligible,key=lambda j:(-core_flow[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.65
                signals[t,0,ranked[1]]=.35
            updates[t,0]=True
        eligible=[j for j in (2,3) if recent[j]>0 and
                  recent[j]-preceding[j]>.10 and
                  c[t,j]>np.median(c[t-167:t+1,j])]
        if eligible:
            best=sorted(eligible,key=lambda j:(-(recent[j]-preceding[j]),j))[0]
            signals[t,1,best]=1.
        updates[t,1]=True
        ranked=sorted(range(4),key=lambda j:(-rv_flow[j],j))
        if rv_flow[ranked[0]]-rv_flow[ranked[-1]]>.12:
            signals[t,2,ranked[0]]=.5
            signals[t,2,ranked[-1]]=-.5
        updates[t,2]=True
        if int(np.count_nonzero(r168<0))>=2:
            if recent[0]>.05:
                signals[t,3,0]=1.
            elif recent[0]<-.05:
                signals[t,3,0]=-1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CL_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CL_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1+.001*np.sin(t[:,None]/17.+np.arange(4)))
    h=np.maximum(o,c)*1.003
    l=np.minimum(o,c)*.997
    q=1e7*(1+.25*np.sin(t[:,None]/23.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    original=(o,h,l,c,q,r,e)
    s,m,z=bundle(*original)
    perturbed=[a.copy() for a in original]
    for j in (0,1,2,3):
        perturbed[j][2900:]*=1.9
    perturbed[4][2900:]*=1.6
    perturbed[5][2900:]*=-1.
    s2,m2,z2=bundle(*perturbed)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True

if __name__=="__main__":
    assert static_check()
    print("CL_CAUSAL_VOLUME_WEIGHTED_CLOSE_LOCATION_SOURCE_PASS")
