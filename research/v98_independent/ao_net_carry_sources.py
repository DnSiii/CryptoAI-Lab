#!/usr/bin/env python3
"""V98 AO independent net-carry growth, sparse event, RV and stress sources.

Completed close t only; first possible trade is open t+1. No PnL, no 2025.
"""
from __future__ import annotations
import numpy as np

WARMUP=2160
EPOCH=336
STATES=("BULL","BEAR","CHOP","STRESS")

def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=np.float64) for x in
                 (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,h,l,r,e,q)) or
        np.any(c<=0) or np.any(l<=0) or np.any(l>c) or
        np.any(h<c) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AO_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"CHOP",dtype="<U6")
    opportunity_expiry=np.zeros(4,dtype=np.int64)
    crisis_until=-1
    recovery_until=-1
    last_crisis=-10**9
    recovery_used=True
    for t in range(WARMUP,n):
        r30=logc[t]-logc[t-720]
        r90=logc[t]-logc[t-2160]
        r7=logc[t]-logc[t-168]
        # 720 completed hours contain exactly 90 native 8h funding events.
        carry=(r[t-719:t+1]*e[t-719:t+1]).sum(axis=0)
        net_score=r30-carry
        eligible=(r30>0)&(r90>0)&(net_score>0)
        rank=np.lexsort((np.arange(4),-net_score))
        selected=[int(j) for j in rank if eligible[j]][:2]
        if len(selected)==1:
            growth[t,selected[0]]=.70
        elif len(selected)==2:
            a,b=selected
            total=net_score[a]+net_score[b]
            first=min(.70,float(net_score[a]/total))
            growth[t,a]=first
            growth[t,b]=1.-first
        # Nonoverlapping 336h breakouts with native funding eligibility.
        breakout=(c[t]>np.max(h[t-672:t],axis=0))&(r7>.04)&(carry<.02)
        for j in range(4):
            if t>=opportunity_expiry[j] and breakout[j]:
                opportunity_expiry[j]=t+EPOCH
        active=opportunity_expiry>t
        if active.any():
            opportunity[t,active]=1./int(active.sum())
        # Two-sided, price-neutral-state native funding spread.
        neutral=np.flatnonzero(np.abs(r30)<.15)
        if len(neutral)>=2:
            order=np.lexsort((neutral,carry[neutral]))
            long=int(neutral[order[0]])
            short=int(neutral[order[-1]])
            if carry[short]-carry[long]>.005:
                relative[t,long]=.5
                relative[t,short]=-.5
        market7=float(np.median(r7))
        market30=float(np.median(r30))
        breadth=int(np.count_nonzero(r7>0))
        crash=market7<-.12 and market30<-.08
        if crash:
            crisis_until=t+168
            last_crisis=t
            recovery_until=-1
            recovery_used=False
        elif (not recovery_used and t>=crisis_until and
              t-last_crisis<=720 and market7>.10):
            recovery_until=t+168
            recovery_used=True
        if t<crisis_until:
            stress[t]=-.25
        elif t<recovery_until:
            stress[t]=.25
        if crash:
            states[t]="STRESS"
        elif market30>.04 and breadth>=3:
            states[t]="BULL"
        elif market30<-.04 and breadth<=1:
            states[t]="BEAR"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2500,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    a=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-24:]*=1.2
    b=source_bundle(changed,np.maximum(h,changed),
                    np.minimum(l,changed),r,e,q)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-24],y[:-24])
        assert np.isfinite(x).all()
        assert np.all(np.abs(x).sum(axis=1)<=1.+1e-12)
    assert np.array_equal(a[4]["state"][:-24],b[4]["state"][:-24])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AO_CAUSAL_SOURCE_PASS")
