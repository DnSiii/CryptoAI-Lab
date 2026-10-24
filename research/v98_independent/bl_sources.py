#!/usr/bin/env python3
"""BL causal multi-timescale pullback, residual reversal and crash recovery portfolio."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BL_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_weights=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    pair=(-1,-1);pair_until=-1;pair_last=-100000
    recovery=-1;recovery_until=-1;recovery_last=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        fund168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        recovery_state=bool(np.count_nonzero(r168<0)>=3 and
                            np.median(r72)<-.06 and np.median(r24)>.025)
        crisis=bool(np.count_nonzero(r168<0)>=3 and np.median(r72)<-.06)
        bull=bool(np.count_nonzero(r168>0)>=3 and np.median(r336)>0)
        if recovery_state:states[t]="RECOVERY"
        elif crisis:states[t]="CRISIS"
        elif bull:states[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            eligible=(r168>0)&(r336>0)
            # Long-horizon equal risk participation among independently trending assets,
            # no fixed winner, no carry-optimized ex-post asset rank.
            core_weights=eligible.astype(float)
            if core_weights.sum():core_weights/=core_weights.sum()
        core[t]=core_weights
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+504 and bull:
                eligible=[j for j in range(4) if
                    r336[j]>.15 and r168[j]>0 and -.10<r72[j]<0 and
                    r24[j]<-.04 and fund168[j]<.03]
                if eligible:
                    # Oversold in a confirmed broad uptrend: no breakout chase.
                    opp_asset=sorted(eligible,key=lambda j:
                        (round(float(r24[j]),12),j))[0]
                    opp_last=t;opp_until=t+168
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.;edge[t,1]=float(-r24[opp_asset])
        if t>=pair_until:
            pair=(-1,-1)
            if t>=pair_last+504 and states[t]=="NEUTRAL":
                long=int(np.argmin(r168));short=int(np.argmax(r168))
                spread=float(r168[short]-r168[long])
                # Residual relative-price reversal confirmed in last 24h,
                # and native carry must not structurally oppose the pair.
                if (long!=short and spread>.25 and
                    r24[long]>.012 and r24[short]<-.012 and
                    fund168[long]<=fund168[short]):
                    pair=(long,short);pair_last=t;pair_until=t+168
        if pair[0]>=0 and t<pair_until:
            rv[t,pair[0]]=.5;rv[t,pair[1]]=-.5
            edge[t,2]=float(r24[pair[0]]-r24[pair[1]])
            carry_cost[t,2]=float(rv[t]@fund168)
        if t>=recovery_until:
            recovery=-1
            if t>=recovery_last+672 and recovery_state:
                eligible=[j for j in range(4) if r168[j]<0 and r24[j]>.025]
                if eligible:
                    recovery=sorted(eligible,key=lambda j:
                        (round(float(r168[j]),12),j))[0]
                    recovery_last=t;recovery_until=t+336
        if recovery>=0 and t<recovery_until:
            stress[t,recovery]=1.
            edge[t,3]=float(r24[recovery])
    return core,opp,rv,stress,{"state":states,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=2900;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                  .05*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-50:]*=1.2
    rr=r.copy();rr[-50:]*=5.
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-50],y[:-50])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    for k in ("state","edge","carry_cost"):
        assert np.array_equal(a[4][k][:-50],b[4][k][:-50])
    assert np.all(np.sum(a[0],axis=1)<=1.+1e-10)
    assert np.all(np.abs(a[2].sum(axis=1))<1e-10)
    assert np.all(np.sum(a[3],axis=1)<=1.+1e-10)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BL_CAUSAL_REVERSAL_RECOVERY_SOURCE_PASS")
