#!/usr/bin/env python3
"""AN slow long-term growth + hard-budget funding spread and crisis/recovery sources."""
from __future__ import annotations
import numpy as np

WARMUP=2160
EPOCH=720

def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=np.float64) for x in
                  (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (h,l,r,e,q))
        or any(not np.isfinite(x).all() for x in (c,h,l,r,e,q))
        or np.any(c<=0) or np.any(l<=0) or np.any(l>c) or np.any(h<c)
        or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AN_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"CHOP",dtype="<U6")
    expiry=np.zeros(4,dtype=np.int64)
    crisis_until=-1
    recovery_until=-1
    last_crisis=-10**9
    recovery_used=True
    for t in range(WARMUP,n):
        r60=logc[t]-logc[t-1440]
        r90=logc[t]-logc[t-2160]
        r14=logc[t]-logc[t-336]
        eligible=(r60>0)&(r90>0)
        if eligible.any():
            growth[t]=eligible/float(eligible.sum())
        # Slow event-driven breakout with 30-day non-overlapping inventory.
        breakout=(c[t]>np.max(h[t-1440:t],axis=0))&(r90>0)
        active=np.zeros(4,dtype=bool)
        for j in range(4):
            if t>=expiry[j] and breakout[j]:
                expiry[j]=t+EPOCH
            active[j]=t<expiry[j]
        if active.any():
            opportunity[t]=active/float(active.sum())
        # Only native funding observed up through completed close t.
        carry=np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
        longs=np.flatnonzero(r60>0)
        shorts=np.flatnonzero(r60<0)
        if len(longs) and len(shorts):
            i=int(longs[np.argmin(carry[longs])])
            j=int(shorts[np.argmax(carry[shorts])])
            relative[t,i]=.5
            relative[t,j]=-.5
        market14=float(np.median(r14))
        market60=float(np.median(r60))
        breadth=int(np.count_nonzero(r14>0))
        if market14<-.15 and t>=crisis_until:
            crisis_until=t+EPOCH
            last_crisis=t
            recovery_until=-1
            recovery_used=False
        elif (not recovery_used and t-last_crisis<=1440 and market14>.10):
            recovery_until=t+EPOCH
            recovery_used=True
        if t<crisis_until:
            stress[t]=-np.ones(4)/4.
        elif t<recovery_until:
            stress[t]=np.ones(4)/4.
        if market14<-.15:
            states[t]="STRESS"
        elif market60>.05 and breadth>=3:
            states[t]="BULL"
        elif market60<-.05 and breadth<=1:
            states[t]="BEAR"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2350,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    a=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-24:]*=1.2
    b=source_bundle(changed,np.maximum(h,changed),np.minimum(l,changed),r,e,q)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-24],y[:-24])
        assert np.isfinite(x).all()
        assert np.all(np.abs(x).sum(axis=1)<=1.+1e-12)
    assert np.array_equal(a[4]["state"][:-24],b[4]["state"][:-24])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AN_HARD_BUDGET_CAUSAL_SOURCE_PASS")
