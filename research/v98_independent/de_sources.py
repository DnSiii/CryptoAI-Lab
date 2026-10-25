#!/usr/bin/env python3
"""DE capital-neutral within-core factor tilt seven-slot causal source, training only."""
from __future__ import annotations
import numpy as np
WARMUP=1152
GRID=96
BUDGETS={
 "RISK_ON":np.array([2.3,.30,.25,.20]),
 "MIXED":np.array([1.7,.35,.30,.35]),
 "RISK_OFF":np.array([.60,.30,.35,.55]),
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
        raise ValueError("DE_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net504=lc[t]-lc[t-504]-native[t-503:t+1].sum(axis=0)
        net216=lc[t]-lc[t-216]-native[t-215:t+1].sum(axis=0)
        ret96=lc[t]-lc[t-96]
        ret36=lc[t]-lc[t-36]
        breadth=int(np.count_nonzero(net216>0))
        regime=("RISK_ON" if breadth>=3 and ret96[0]>0 else
                "RISK_OFF" if breadth<=1 and ret96[0]<0 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        candidates=[j for j in range(4) if net504[j]>0 and ret96[j]>0]
        selected=sorted(candidates,key=lambda j:(-float(net504[j]),j))[:2]
        if selected:
            signals[t,0,selected]=1./len(selected)
        updates[t,0]=True
        if len(selected)==2:
            a,b=selected
            # Opportunity: confirmed upside range breakout, capital-neutral rotation.
            options=[]
            for j in selected:
                past_hi=float(np.max(h[t-240:t-24,j]))
                old_q=float(q[t-216:t-24,j].mean())
                recent_q=float(q[t-23:t+1,j].mean())
                if c[t,j]>past_hi and recent_q>old_q:
                    options.append((float(c[t,j])/past_hi-1.,j))
            if options:
                _,winner=max(options,key=lambda x:(x[0],-x[1]))
                loser=b if winner==a else a
                signals[t,1,winner]=.5
                signals[t,1,loser]=-.5
            # Relative value: cross-horizon relative persistence net of native carry.
            f168=native[t-167:t+1].sum(axis=0)
            rel168=float((lc[t,a]-lc[t-168,a]-f168[a])-
                         (lc[t,b]-lc[t-168,b]-f168[b]))
            rel48=float((lc[t,a]-lc[t-48,a])-(lc[t,b]-lc[t-48,b]))
            if rel168*rel48>0:
                winner,loser=(a,b) if rel168>0 else (b,a)
                signals[t,2,winner]=.5
                signals[t,2,loser]=-.5
        updates[t,1]=True
        updates[t,2]=True
        # Stress and recovery are *only* on already selected core holdings.
        if selected:
            prev36=lc[t-36]-lc[t-72]
            if int(np.count_nonzero(ret36<0))>=3:
                signals[t,3,selected]=-.5 if len(selected)==2 else -1.
            elif int(np.count_nonzero(prev36>0))<=1 and int(np.count_nonzero(ret36>0))>=3:
                signals[t,3,selected]=.5 if len(selected)==2 else 1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DE_GROSS_SOURCE")
    if not np.allclose(signals[:,1,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DE_OPPORTUNITY_NOT_NEUTRAL")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DE_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("DE_BUDGET_NONFINITE")
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
    assert np.allclose(a[0][:,1,:].sum(axis=1),0.)
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    return True
if __name__=="__main__":
    assert static_check()
    print("DE_CAUSAL_CAPITAL_NEUTRAL_STATIC_PASS")
