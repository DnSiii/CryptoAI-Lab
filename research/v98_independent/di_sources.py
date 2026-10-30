#!/usr/bin/env python3
"""DI stateful inventory persistence and native-carry seven-slot source, training only."""
from __future__ import annotations
import numpy as np
WARMUP=1440
GRID=120
BUDGETS={
    "RISK_ON":np.array([3.0,.25,.25,.15]),
    "MIXED":np.array([2.3,.40,.45,.35]),
    "RISK_OFF":np.array([.60,.35,.55,.70]),
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
        raise ValueError("DI_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    previous=np.zeros((4,4))
    previous_budget=np.zeros(4)
    for t in range(WARMUP,n,GRID):
        net960=lc[t]-lc[t-960]-native[t-959:t+1].sum(axis=0)
        raw240=lc[t]-lc[t-240]
        eligible=[j for j in range(4) if net960[j]>0 and raw240[j]>0]
        selected=sorted(eligible,key=lambda j:(-float(net960[j]),j))[:2]
        if selected:
            signals[t,0,selected]=1./len(selected)
        # Native carry: 120h completed event-rate average.
        carry=native[t-119:t+1].sum(axis=0)/15.
        carry_low=min(range(4),key=lambda j:(float(carry[j]),j))
        carry_high=max(range(4),key=lambda j:(float(carry[j]),-j))
        if carry[carry_low]<0 and raw240[carry_low]>0:
            signals[t,1,carry_low]=1.
        if (carry_low!=carry_high and carry[carry_high]-carry[carry_low]>.00015
            and raw240[carry_low]-raw240[carry_high]>=-.03):
            signals[t,2,carry_low]=.5
            signals[t,2,carry_high]=-.5
        breadth_neg=int(np.count_nonzero(raw240<0))
        breadth_pos=int(np.count_nonzero(raw240>0))
        old240=lc[t-240]-lc[t-480]
        if breadth_neg>=3 and raw240[0]<0:
            signals[t,3,0]=-.5
            signals[t,3,3]=-.5
        elif breadth_pos>=3 and np.count_nonzero(old240>0)<=1:
            signals[t,3,0]=.5
            signals[t,3,3]=.5
        regime=("RISK_ON" if breadth_pos>=3 else
                "RISK_OFF" if breadth_neg>=3 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        for i in range(4):
            if (not np.array_equal(signals[t,i],previous[i]) or
                budgets[t,i]!=previous_budget[i]):
                updates[t,i]=True
                previous[i]=signals[t,i].copy()
                previous_budget[i]=budgets[t,i]
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DI_GROSS_SOURCE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
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
    return True
if __name__=="__main__":
    assert static_check()
    print("DI_CAUSAL_STATEFUL_INVENTORY_STATIC_PASS")
