#!/usr/bin/env python3
"""DH signed persistent-trend and carry-dispersion seven-slot source; training only."""
from __future__ import annotations
import numpy as np
WARMUP=1152
GRID=36
BUDGETS={
    "RISK_ON":np.array([2.6,.35,.45,.25]),
    "MIXED":np.array([2.0,.50,.55,.35]),
    "RISK_OFF":np.array([1.3,.45,.65,.50]),
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
        raise ValueError("DH_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net480=lc[t]-lc[t-480]-native[t-479:t+1].sum(axis=0)
        net120=lc[t]-lc[t-120]-native[t-119:t+1].sum(axis=0)
        eligible=[j for j in range(4) if net480[j]*net120[j]>0 and abs(net480[j])>.04]
        selected=sorted(eligible,key=lambda j:(-float(abs(net480[j])),j))[:2]
        if selected:
            for j in selected:
                signals[t,0,j]=float(np.sign(net480[j]))/len(selected)
        # Opportunity: acceleration confirmed by drift and contemporaneously completed volume.
        latest=lc[t]-lc[t-24]
        preceding=lc[t-24]-lc[t-48]
        acceleration=latest-preceding
        volume_recent=q[t-23:t+1].mean(axis=0)
        volume_prior=q[t-192:t-24].mean(axis=0)
        candidates=[j for j in range(4) if acceleration[j]*latest[j]>0 and
                    volume_recent[j]>1.15*volume_prior[j]]
        if candidates:
            j=max(candidates,key=lambda j:(float(abs(acceleration[j])),-j))
            signals[t,1,j]=float(np.sign(acceleration[j]))
        # Relative Value: persistent cross-sectional native-carry-adjusted dispersion.
        net240=lc[t]-lc[t-240]-native[t-239:t+1].sum(axis=0)
        net72=lc[t]-lc[t-72]-native[t-71:t+1].sum(axis=0)
        leader=max(range(4),key=lambda j:(float(net240[j]),-j))
        laggard=min(range(4),key=lambda j:(float(net240[j]),j))
        if (leader!=laggard and net240[leader]-net240[laggard]>.12
            and net72[leader]>net72[laggard]):
            signals[t,2,leader]=.5
            signals[t,2,laggard]=-.5
        # Stress/Recovery: signed BTC shock confirmed by market breadth.
        breadth_pos=int(np.count_nonzero(latest>0))
        breadth_neg=int(np.count_nonzero(latest<0))
        if latest[0]<-.05 and breadth_neg>=3:
            signals[t,3,0]=-.5
            signals[t,3,3]=-.5
        elif latest[0]>.05 and breadth_pos>=3:
            signals[t,3,0]=.5
            signals[t,3,3]=.5
        positive=int(np.count_nonzero(net120>0))
        regime=("RISK_ON" if positive>=3 and net120[0]>0 else
                "RISK_OFF" if positive<=1 and net120[0]<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DH_GROSS_SOURCE")
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
    print("DH_CAUSAL_SIGNED_DISPERSION_STATIC_PASS")
