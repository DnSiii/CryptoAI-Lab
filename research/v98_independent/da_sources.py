#!/usr/bin/env python3
"""DA core-capacity complementary seven-slot causal signal/router source. TRAINING only."""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BASE_BUDGETS={
 "RISK_ON":np.array([2.30,.35,.50,.20]),
 "MIXED":np.array([1.70,.40,.55,.40]),
 "RISK_OFF":np.array([.50,.40,.55,.75]),
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
        raise ValueError("DA_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    prev=np.zeros((4,4))
    for t in range(WARMUP,n,GRID):
        ret336=lc[t]-lc[t-336]
        ret168=lc[t]-lc[t-168]
        ret72=lc[t]-lc[t-72]
        net336=ret336-native[t-335:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(net336>0))
        regime=("RISK_ON" if breadth>=3 and ret72[0]>0 else
                "RISK_OFF" if breadth<=1 and ret72[0]<0 else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%336==0:
            eligible=np.maximum(net336[[0,1,3]],0.)*(ret72[[0,1,3]]>0)
            if eligible.sum()>0:
                signals[t,0,[0,1,3]]=eligible/eligible.sum()
            updates[t,0]=True
        core_active=bool(np.any(signals[t,0])) if updates[t,0] else bool(np.any(prev[0]))
        scale=.55 if core_active else 1.8
        budgets[t]=BASE_BUDGETS[regime]*np.array([1.,scale,scale,scale])
        # 21 completed native funding events for BNB and ETH.
        idx2=np.flatnonzero(e[:t+1,2])
        idx1=np.flatnonzero(e[:t+1,1])
        bnb_funding=float(r[idx2[-21:],2].sum())
        eth_funding=float(r[idx1[-21:],1].sum())
        if bnb_funding<0 and ret168[2]>0:
            signals[t,1,2]=1.
        elif bnb_funding>0 and ret168[2]<0:
            signals[t,1,2]=-1.
        updates[t,1]=True
        rel=float(ret336[2]-ret336[1])
        if rel>0 and bnb_funding<eth_funding:
            signals[t,2,2]=.5;signals[t,2,1]=-.5
        elif rel<0 and bnb_funding>eth_funding:
            signals[t,2,2]=-.5;signals[t,2,1]=.5
        updates[t,2]=True
        if ret72[0]<0 and int(np.count_nonzero(ret72<0))>=3:
            signals[t,3,0]=-1.
        elif ret72[0]>0 and (lc[t-72,0]-lc[t-144,0])<0:
            signals[t,3,0]=1.
        updates[t,3]=True
        for i in np.flatnonzero(updates[t]):
            prev[i]=signals[t,i].copy()
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DA_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DA_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("DA_BUDGET_NONFINITE")
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
    print("DA_CAUSAL_SOURCE_STATIC_PASS")
