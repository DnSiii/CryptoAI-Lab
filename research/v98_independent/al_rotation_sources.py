#!/usr/bin/env python3
"""AL seven-slot signal layer: completed-bar cross-sectional rotation, not AK carry."""
from __future__ import annotations
import numpy as np

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
STATES = ("BULL", "BEAR", "CHOP", "STRESS")
WARMUP = 2016

def source_bundle(close, high, low, funding_rate, funding_event, quote_volume):
    c,h,l,r,e,q = (np.asarray(x, dtype=np.float64) for x in
                   (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (h,l,r,e,q))
        or any(not np.isfinite(x).all() for x in (c,h,l,r,e,q))
        or np.any(c<=0) or np.any(l<=0) or np.any(l>c) or np.any(h<c)
        or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AL_BAD_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    lr=np.diff(logc,axis=0,prepend=logc[:1])
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"CHOP",dtype="<U6")
    expiry=np.zeros(4,dtype=np.int64)
    last_crisis=-10**9
    recovery_until=-1
    recovery_used=True
    for t in range(WARMUP,n):
        r14=logc[t]-logc[t-336]
        r42=logc[t]-logc[t-1008]
        r72=logc[t]-logc[t-72]
        r168=logc[t]-logc[t-168]
        vol=np.sqrt(np.mean(lr[t-335:t+1]**2,axis=0))
        inv=1./np.maximum(vol,.0005)
        median14=float(np.median(r14))
        score=r14+.5*r42/3.-.3*median14
        eligible=(r14>0)&(r42>0)&(score>0)
        ranked=np.lexsort((np.arange(4),-score))
        chosen=[j for j in ranked if eligible[j]][:2]
        if chosen:
            raw=np.zeros(4)
            raw[chosen]=inv[chosen]*np.maximum(score[chosen],1e-8)
            growth[t]=raw/raw.sum()
        # Completed bar t only; actual opening fill is t+1.
        prior_high=np.max(h[t-240:t],axis=0)
        median_q=np.median(q[t-168:t],axis=0)
        new=(c[t]>prior_high)&(r72>r14*(72./336.))&(
            q[t]>.8*np.maximum(median_q,1e-8))&(t>=expiry)
        expiry[new]=t+72
        active=expiry>t
        if active.any():
            raw=active*inv
            opportunity[t]=raw/raw.sum()
        residual=r168-float(np.median(r168))
        rv_eligible=(residual>0)&(r14>0)
        rv_rank=np.lexsort((np.arange(4),-residual))
        winner=next((j for j in rv_rank if rv_eligible[j]),None)
        if winner is not None:
            relative[t,winner]=1.
        market72=float(np.median(r72))
        market168=float(np.median(r168))
        market336=float(np.median(r14))
        breadth=int(np.count_nonzero(r14>0))
        if market72<-.09:
            last_crisis=t
            recovery_until=-1
            recovery_used=False
        elif (not recovery_used and t-last_crisis<=336 and
              market72>.05 and market168>0):
            recovery_until=t+96
            recovery_used=True
        if t<recovery_until and market72>=-.09:
            stress[t]=inv/inv.sum()
        if market72<-.09:
            states[t]="STRESS"
        elif market336>.06 and breadth>=3:
            states[t]="BULL"
        elif market336<-.04 and breadth<=1:
            states[t]="BEAR"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2200,dtype=np.float64)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c)
    e=np.zeros_like(c);e[::8]=1.
    q=np.ones_like(c)*1e8
    a=source_bundle(c,h,l,r,e,q)
    b=c.copy();b[-15:]*=1.2
    z=source_bundle(b,np.maximum(h,b),np.minimum(l,b),r,e,q)
    for x,y in zip(a[:4],z[:4]):
        assert np.array_equal(x[:-15],y[:-15])
    assert np.array_equal(a[4]["state"][:-15],z[4]["state"][:-15])
    assert all(np.isfinite(x).all() for x in a[:4])
    assert all(np.all(np.abs(x).sum(axis=1)<=1.+1e-12) for x in a[:4])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AL_CAUSAL_SEVEN_SLOT_SOURCE_PASS")
