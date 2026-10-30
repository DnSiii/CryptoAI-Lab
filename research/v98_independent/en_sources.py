#!/usr/bin/env python3
"""EN seven-slot online marginal geometric-growth sources. Training 2023-2024 only."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=24
CORE_BUDGET={"TREND":2.3,"MIXED":1.9,"STRESS":1.1}
SATELLITE_CAP=np.array([.35,.30,.40])
GROSS_CAP=3.0
HISTORY=28

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EN_INVALID_PINNED_SOURCE")
    n=len(c); lc=np.log(c)
    hr=np.diff(lc,axis=0,prepend=lc[:1])
    market=hr.mean(axis=1)
    qcum=np.cumsum(q,axis=0)
    q24=qcum.copy()
    q24[24:]-=qcum[:-24]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    previous=np.zeros((4,4))
    last_turnover=np.zeros(4)
    shadow=[[] for _ in range(4)]
    for t in range(WARMUP,n,CLOCK):
        # The completed t-24..t shadow payoff belongs to positions selected at t-24,
        # never to positions about to be selected at t.
        if t>WARMUP:
            completed=(c[t]/c[t-24]-1.)-np.sum(r[t-23:t+1]*e[t-23:t+1],axis=0)
            for i in range(4):
                realized=float(previous[i]@completed)-.002*float(last_turnover[i])
                shadow[i].append(realized)
        net240=lc[t]-lc[t-240]-np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
        breadth=int(np.count_nonzero(net240>0))
        market48=float(np.mean(lc[t]-lc[t-48]))
        regime=("TREND" if breadth>=3 else
                "STRESS" if breadth<=1 and market48<0 else "MIXED")
        regimes[t]=regime
        candidate=np.zeros((4,4))
        # Growth Core: funding-aware long-only growth plus downside risk normalization.
        down=np.sqrt(np.mean(np.minimum(hr[t-239:t+1],0.)**2,axis=0))
        agree=(lc[t]-lc[t-48])>0.
        core_score=np.where(agree,np.maximum(net240,0.),0.)/np.maximum(down,1e-7)
        core_weights=core_score/core_score.sum() if core_score.sum()>1e-12 else np.full(4,.25)
        candidate[0]=.20*np.full(4,.25)+.80*core_weights
        # Opportunity: funded long-trend pullback with completed quote-volume confirmation.
        deviations=lc[t]-np.mean(lc[t-119:t+1],axis=0)
        opts=[(float(deviations[j]),j) for j in (1,2,3)
              if deviations[j]<0. and net240[j]>0.
              and q24[t,j]>np.median(q24[t-120:t,j])]
        if opts:
            _,j=min(opts,key=lambda z:(z[0],z[1]))
            candidate[1,j]=1.
        # Relative value: short-term cross-sectional idiosyncratic convergence.
        ret72=lc[t]-lc[t-72]
        residual=ret72-ret72.mean()
        lo=int(np.argmin(residual)); hi=int(np.argmax(residual))
        if lo!=hi and residual[hi]-residual[lo]>.015:
            candidate[2,lo]=.5
            candidate[2,hi]=-.5
        # Stress continuation: defensive short, never a retrospective hedge.
        falling=int(np.count_nonzero(lc[t]-lc[t-48]<0.))
        down24=float(np.sqrt(np.mean(np.minimum(market[t-23:t+1],0.)**2)))
        down240=float(np.sqrt(np.mean(np.minimum(market[t-239:t+1],0.)**2)))
        if falling>=3 and down24>1.2*max(down240,1e-10):
            weakest=1+int(np.argmin(lc[t,1:]-lc[t-24,1:]))
            candidate[3,weakest]=-1.
        requested=np.zeros(4)
        requested[0]=CORE_BUDGET[regime]
        if len(shadow[0])>=HISTORY:
            window=np.array([a[-HISTORY:] for a in shadow])
            core=window[0]
            for i in range(1,4):
                if not np.any(candidate[i]):
                    continue
                mu=float(np.mean(window[i]))
                cov=float(np.mean((core-core.mean())*(window[i]-mu)))
                stderr=float(np.std(window[i])/np.sqrt(HISTORY))
                marginal=mu-requested[0]*cov-.00075-.35*stderr
                if marginal>0.:
                    requested[i]=SATELLITE_CAP[i-1]*min(marginal/.004,1.)
        remaining=GROSS_CAP
        effective=np.zeros(4)
        for i in range(4):
            effective[i]=min(requested[i],remaining)
            remaining=max(0.,remaining-effective[i])
        if effective.sum()>GROSS_CAP+1e-12:
            raise ValueError("EN_HIDDEN_LEVERAGE")
        for i in range(4):
            signals[t,i]=candidate[i]
            budgets[t,i]=effective[i]
            updates[t,i]=True
        last_turnover=np.sum(abs(candidate-previous),axis=1)
        previous=candidate
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EN_SOURCE_GROSS")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EN_NONFINITE_BUDGET")
    return signals,updates,regimes,budgets

def static_check():
    n=3600;t=np.arange(n,dtype=float)
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
    assert np.all(a[0][:WARMUP]==0.)
    assert np.all(np.sum(np.abs(a[0]),axis=2)<=1.+1e-12)
    assert np.all(np.isfinite(a[3]))
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK),:].all(axis=1))
    return True

if __name__=="__main__":
    assert static_check()
    print("EN_ONLINE_SHADOW_COVARIANCE_SEVEN_SLOT_STATIC_PASS")
