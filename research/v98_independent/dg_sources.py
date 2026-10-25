#!/usr/bin/env python3
"""DG idle-capital seven-slot state-exclusive causal source; training-only."""
from __future__ import annotations
import numpy as np
WARMUP=1200
GRID=48
BUDGETS={
    "GROWTH":np.array([2.8,0.,0.,0.]),
    "MIXED":np.array([1.3,.60,.55,.35]),
    "RISK_OFF":np.array([.70,.45,.65,.70]),
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
        raise ValueError("DG_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net384=lc[t]-lc[t-384]-native[t-383:t+1].sum(axis=0)
        raw96=lc[t]-lc[t-96]
        eligible=np.flatnonzero((net384>0)&(raw96>0))
        if len(eligible):
            strength=net384[eligible]
            limit=2.*float(np.median(strength))
            strength=np.minimum(strength,limit)
            signals[t,0,eligible]=strength/strength.sum()
        if len(eligible)>=2:
            regime="GROWTH"
        else:
            regime=("RISK_OFF" if np.count_nonzero(raw96<0)>=3 else "MIXED")
            # Opportunity: reversal following a completed losing interval.
            old48=lc[t-12]-lc[t-60]
            rev12=lc[t]-lc[t-12]
            vol_new=q[t-11:t+1].mean(axis=0)
            vol_old=q[t-131:t-11].mean(axis=0)
            low48=l[t-47:t+1].min(axis=0)
            candidates=np.flatnonzero((old48<0)&(rev12>0)&
                (c[t]>=1.02*low48)&(vol_new>vol_old))
            if len(candidates):
                j=max(candidates,key=lambda j:(float(rev12[j]),-int(j)))
                signals[t,1,j]=1.
            # Relative value: defensive cross-sectional dispersion continuation.
            net192=lc[t]-lc[t-192]-native[t-191:t+1].sum(axis=0)
            leader=max(range(4),key=lambda j:(float(net192[j]),-j))
            laggard=min(range(4),key=lambda j:(float(net192[j]),j))
            raw24=lc[t]-lc[t-24]
            if leader!=laggard and raw24[leader]>0 and raw24[laggard]<0:
                signals[t,2,leader]=.5
                signals[t,2,laggard]=-.5
            # Stress: range-shock short, or broad recovery long.
            raw48=lc[t]-lc[t-48]
            recent_range=float(np.max((h[t-11:t+1,0]-l[t-11:t+1,0])/c[t-11:t+1,0]))
            old_range=float(np.median((h[t-180:t-12,0]-l[t-180:t-12,0])/c[t-180:t-12,0]))
            if np.count_nonzero(raw48<0)>=3 and recent_range>2.*old_range:
                worst=int(np.argmin(raw48))
                if worst==0:
                    signals[t,3,0]=-1.
                else:
                    signals[t,3,0]=-.5
                    signals[t,3,worst]=-.5
            elif np.count_nonzero(raw24>0)>=3 and np.count_nonzero(old48>0)<=1:
                best=max(range(4),key=lambda j:(float(raw24[j]),-j))
                signals[t,3,best]=1.
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DG_GROSS_SOURCE")
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
    print("DG_CAUSAL_IDLE_CAPITAL_STATIC_PASS")
