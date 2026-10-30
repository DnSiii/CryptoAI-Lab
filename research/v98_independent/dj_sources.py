#!/usr/bin/env python3
"""DJ distinct price-dislocation seven-slot sources; causal 2022-2024 training only."""
from __future__ import annotations
import numpy as np

WARMUP=1440
GRID=96
BUDGETS={
    "RISK_ON":np.array([3.8,.35,.25,.25],dtype=float),
    "MIXED":np.array([2.7,.45,.45,.45],dtype=float),
    "RISK_OFF":np.array([.65,.25,.50,.70],dtype=float),
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
        raise ValueError("DJ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,GRID):
        long720=lc[t]-lc[t-720]
        ret192=lc[t]-lc[t-192]
        ret48=lc[t]-lc[t-48]
        prev48=lc[t-48]-lc[t-96]
        # Growth: channel break with persistent positive 720h direction.
        eligible=[j for j in range(4)
                  if long720[j]>0 and c[t,j]>np.max(c[t-168:t,j])]
        top=sorted(eligible,key=lambda j:(-float(long720[j]),j))[:2]
        if top:signals[t,0,top]=1./len(top)
        # Opportunity: compression-to-expansion with observed quote-volume impulse.
        new_q=np.mean(q[t-47:t+1],axis=0)
        old_q=np.mean(q[t-239:t-47],axis=0)
        ok=[j for j in range(4) if ret48[j]>.02 and
            ret48[j]>1.5*abs(ret192[j])/4. and
            new_q[j]>=1.2*old_q[j] and old_q[j]>0]
        if ok:
            j=sorted(ok,key=lambda j:(-float(ret48[j]),j))[0]
            signals[t,1,j]=1.
        # Relative value: contemporaneous market factor neutralized.
        residual=ret192-np.mean(ret192)
        hi=sorted(range(4),key=lambda j:(-float(residual[j]),j))[0]
        lo=sorted(range(4),key=lambda j:(float(residual[j]),j))[0]
        if hi!=lo and residual[hi]-residual[lo]>.06 and ret48[hi]>ret48[lo]:
            signals[t,2,hi]=.5
            signals[t,2,lo]=-.5
        # Stress / recovery: broad price shock, or confirmed first rebound.
        if np.count_nonzero(ret48<0)>=3 and np.median(ret48)<-.045:
            worst=sorted(range(4),key=lambda j:(float(ret48[j]),j))[:2]
            signals[t,3,worst]=-.5
        elif np.count_nonzero(ret48>0)>=3 and np.median(prev48)<-.045:
            best=sorted(range(4),key=lambda j:(-float(ret48[j]),j))[:2]
            signals[t,3,best]=.5
        regime=("RISK_ON" if np.count_nonzero(ret192>0)>=3 and
                np.median(ret48)>=0 else
                "RISK_OFF" if np.count_nonzero(ret192<0)>=3 and
                np.median(ret48)<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        updates[t]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DJ_GROSS_SOURCE")
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
    print("DJ_CAUSAL_PRICE_DISLOCATION_SOURCE_STATIC_PASS")
