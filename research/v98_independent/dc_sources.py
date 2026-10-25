#!/usr/bin/env python3
"""DC causal orthogonal inventory-partition complete seven-slot source, 2022-24 only."""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BUDGETS={
    "RISK_ON":np.array([2.25,.35,.35,0.]),
    "MIXED":np.array([1.60,.40,.40,.35]),
    "RISK_OFF":np.array([0.,.15,.35,.80]),
}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DC_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        ret336=lc[t]-lc[t-336]
        ret168=lc[t]-lc[t-168]
        ret72=lc[t]-lc[t-72]
        ret48=lc[t]-lc[t-48]
        net336=ret336-native[t-335:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(net336>0))
        regime=("RISK_ON" if breadth>=3 and ret168[0]>0 else
                "RISK_OFF" if breadth<=1 and ret168[0]<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        used=set()
        # Core owns the first economically eligible inventory slot.
        score=np.where((net336>0)&(ret72>0),net336,0.)
        if budgets[t,0]>0 and score.max()>0:
            j=int(np.argmax(score));signals[t,0,j]=1.;used.add(j)
        updates[t,0]=True
        # Stress reserved before opportunistic and neutral sleeves.
        if budgets[t,3]>0 and 0 not in used:
            if ret168[0]<0 and int(np.count_nonzero(ret48<0))>=3:
                signals[t,3,0]=-1.;used.add(0)
            elif ret168[0]<0 and ret48[0]>0 and (
                  lc[t-48,0]-lc[t-96,0])<0:
                signals[t,3,0]=1.;used.add(0)
        updates[t,3]=True
        # Second-highest free asset positive 48h momentum when broad BTC trend.
        if ret168[0]>0 and int(np.count_nonzero(ret48>0))>=2 and budgets[t,1]>0:
            candidates=[j for j in range(4) if j not in used and ret48[j]>0]
            if candidates:
                j=max(candidates,key=lambda k:(float(ret48[k]),-k))
                signals[t,1,j]=1.;used.add(j)
        updates[t,1]=True
        # Residual free-asset pair: native funding spread, no price-sign selection.
        remaining=[j for j in range(4) if j not in used]
        if len(remaining)>=2 and budgets[t,2]>0:
            f={}
            for j in remaining:
                idx=np.flatnonzero(e[:t+1,j])
                f[j]=float(r[idx[-14:],j].sum())
            low_j=min(remaining,key=lambda j:(f[j],j))
            high_j=max(remaining,key=lambda j:(f[j],-j))
            if f[high_j]>f[low_j]:
                signals[t,2,low_j]=.5
                signals[t,2,high_j]=-.5
                used.update((low_j,high_j))
        updates[t,2]=True
        # Physical inventory partitions must be disjoint, no offsetting core.
        if np.any(np.sum(abs(signals[t])>1e-12,axis=0)>1):
            raise ValueError("DC_INVENTORY_PARTITION_COLLISION")
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DC_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DC_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("DC_BUDGET_NONFINITE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2=c.copy();o2=o.copy();h2=h.copy();l2=l.copy()
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2=q.copy();q2[3200:]*=4.
    r2=r.copy();r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    return True

if __name__=="__main__":
    assert static_check()
    print("DC_CAUSAL_PARTITION_STATIC_PASS")
