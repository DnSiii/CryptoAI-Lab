#!/usr/bin/env python3
"""V98 AQ inverse-vol structural core and distinct marginal overlay sources."""
from __future__ import annotations
import numpy as np
WARMUP=2160
def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=float) for x in
                 (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,h,l,r,e,q)) or
        np.any(c<=0) or np.any(l<=0) or np.any(l>c) or
        np.any(h<c) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AQ_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    lr=np.diff(logc,axis=0,prepend=logc[:1])
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U8")
    crisis_until=-1
    recovery_until=-1
    last_crisis=-10**9
    recovery_used=True
    for t in range(WARMUP,n):
        r7=logc[t]-logc[t-168]
        r30=logc[t]-logc[t-720]
        r90=logc[t]-logc[t-2160]
        vol90=np.sqrt(np.mean(lr[t-2159:t+1]**2,axis=0))
        inv=1./np.maximum(vol90,1e-5)
        growth[t]=inv/inv.sum()
        relative_strength=r30-float(np.median(r30))
        eligible=(relative_strength>.05)&(r30>0)&(r7>0)
        rank=np.lexsort((np.arange(4),-relative_strength))
        selected=[int(j) for j in rank if eligible[j]][:2]
        if selected:
            opportunity[t,selected]=1./len(selected)
        carry=(r[t-719:t+1]*e[t-719:t+1]).sum(axis=0)
        longs=np.flatnonzero(r30>0)
        shorts=np.flatnonzero(r30<0)
        if len(longs) and len(shorts):
            a=int(longs[np.lexsort((longs,carry[longs]))[0]])
            b=int(shorts[np.lexsort((shorts,-carry[shorts]))[0]])
            if carry[b]-carry[a]>.01:
                relative[t,a]=.5
                relative[t,b]=-.5
        market7=float(np.median(r7))
        market30=float(np.median(r30))
        market90=float(np.median(r90))
        vol7=float(np.mean(np.sqrt(np.mean(lr[t-167:t+1]**2,axis=0))))
        vol30=float(np.mean(np.sqrt(np.mean(lr[t-719:t+1]**2,axis=0))))
        panic=market7<-.08 and vol7>1.3*vol30
        if panic:
            crisis_until=t+168
            last_crisis=t
            recovery_until=-1
            recovery_used=False
        elif (not recovery_used and t>=crisis_until and
              t-last_crisis<=720 and market7>.08):
            recovery_until=t+168
            recovery_used=True
        if t<crisis_until:
            stress[t]=-.25
        elif t<recovery_until:
            stress[t]=.25
        breadth=int(np.count_nonzero(r7>0))
        if panic:
            states[t]="PANIC"
        elif market90>0 and breadth>=3:
            states[t]="RISK_ON"
        elif market30<-.05:
            states[t]="RISK_OFF"
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
    print("AQ_MARGINAL_SOURCE_CAUSAL_PASS")
