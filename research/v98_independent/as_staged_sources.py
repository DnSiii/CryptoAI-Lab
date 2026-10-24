#!/usr/bin/env python3
"""V98 AS distinct liquidity-trend core, high-break, signed momentum and recovery."""
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
        raise ValueError("AS_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"CHOP",dtype="<U12")
    opp_until=-1
    opp_asset=-1
    arm_until=-1
    recovery_until=-1
    last_crisis=-1000000
    for t in range(WARMUP,n):
        r24=logc[t]-logc[t-24]
        r168=logc[t]-logc[t-168]
        r720=logc[t]-logc[t-720]
        r2160=logc[t]-logc[t-2160]
        median720=np.median(c[t-720:t],axis=0)
        eligible=(r2160>0)&(c[t]>median720)
        liquidity=np.sqrt(np.maximum(np.mean(q[t-719:t+1],axis=0),0.))
        weights=np.where(eligible,liquidity,0.)
        if weights.sum()>0:
            growth[t]=weights/weights.sum()

        if t>=opp_until:
            opp_asset=-1
            prior_high=np.max(c[t-720:t],axis=0)
            volume_gate=np.quantile(q[t-168:t],.75,axis=0)
            valid=(c[t]>prior_high)&(r168>.08)&(q[t]>volume_gate)
            if valid.any():
                rank=np.lexsort((np.arange(4),-r168))
                opp_asset=int(next(j for j in rank if valid[j]))
                opp_until=t+168
        if t<opp_until and opp_asset>=0:
            opportunity[t,opp_asset]=1.

        best=int(np.argmax(r720))
        worst=int(np.argmin(r720))
        if (best!=worst and float(r720[best]-r720[worst])>.10 and
            int(np.count_nonzero(r168>0))>=2):
            relative[t,best]=.5
            relative[t,worst]=-.5

        median168=float(np.median(r168))
        median24=float(np.median(r24))
        median30=float(np.median(r720))
        if (median168<-.12 and t>=last_crisis+336 and
            t>=recovery_until and t>=arm_until):
            last_crisis=t
            arm_until=t+336
        if (t<arm_until and t>=recovery_until and
            median24>.04 and t>last_crisis):
            recovery_until=t+168
            arm_until=-1
        if t<recovery_until:
            stress[t]=.25

        if t<recovery_until:
            states[t]="RECOVERY"
        elif median30>0 and np.count_nonzero(r168>0)>=3:
            states[t]="EXPANSION"
        elif median30<0:
            states[t]="CONTRACTION"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2600,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    a=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-48:]*=1.2
    b=source_bundle(changed,np.maximum(h,changed),
                    np.minimum(l,changed),r,e,q)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-48],y[:-48])
        assert np.isfinite(x).all()
        assert np.all(np.abs(x).sum(axis=1)<=1.+1e-12)
    assert np.array_equal(a[4]["state"][:-48],b[4]["state"][:-48])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AS_DISTINCT_SOURCE_CAUSAL_PASS")
