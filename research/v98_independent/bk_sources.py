#!/usr/bin/env python3
"""BK seven-slot native carry-confirmed convex breakout, trend carry pair, and crash short. Chronological 2023-24 only."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BK_SOURCE_INPUT")
    n=len(c); lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_weights=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    pair=(-1,-1);pair_until=-1;pair_last=-100000
    hedge=-1;hedge_until=-1;hedge_last=-100000
    for t in range(WARMUP,n):
        ret24=lc[t]-lc[t-24]
        ret72=lc[t]-lc[t-72]
        ret168=lc[t]-lc[t-168]
        ret336=lc[t]-lc[t-336]
        funding168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(ret168<0)>=3 and np.median(ret72)<-.05)
        bull=bool(np.count_nonzero(ret168>0)>=3 and np.median(ret336)>0)
        if crisis:states[t]="CRISIS"
        elif bull:states[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            volatility=np.std(np.diff(lc[t-672:t+1],axis=0),axis=0,ddof=1)
            # Structural positive-trend growth with funding-aware inverse-vol breadth;
            # no ex-post asset selection or asset-specific hardcoding.
            eligible=(ret168>0)&(ret336>0)
            inv=eligible*np.exp(-4.*np.maximum(funding168,0.))/np.maximum(volatility,1e-5)
            core_weights=inv/inv.sum() if inv.sum()>0 else np.zeros(4)
        core[t]=core_weights
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+1008 and bull:
                eligible=[j for j in range(4)
                    if ret168[j]>.08 and ret72[j]>0 and
                       funding168[j]<.03 and
                       c[t,j]>1.005*np.max(c[t-504:t,j])]
                if eligible:
                    vol=np.std(np.diff(lc[t-168:t+1],axis=0),axis=0,ddof=1)
                    opp_asset=sorted(eligible,key=lambda j:
                        (-round(float(ret168[j]/max(vol[j],1e-5)),12),j))[0]
                    opp_last=t;opp_until=t+504
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=pair_until:
            pair=(-1,-1)
            if t>=pair_last+672:
                candidates=[]
                for long in range(4):
                    for short in range(4):
                        if long==short:continue
                        spread=float(funding168[short]-funding168[long])
                        if (spread>.005 and ret168[long]>.025 and
                            ret168[short]<-.025 and
                            ret168[long]>ret168[short]):
                            candidates.append((spread,long,short))
                if candidates:
                    _,long,short=sorted(candidates,key=lambda z:
                        (-round(z[0],12),z[1],z[2]))[0]
                    pair=(long,short);pair_last=t;pair_until=t+336
        if pair[0]>=0 and t<pair_until:
            rv[t,pair[0]]=.5;rv[t,pair[1]]=-.5
        # One-sided systemic crisis hedge, not permanent inverse-beta insurance.
        # Causal recovery closes the short, preventing fixed-duration rebound bleed.
        if hedge>=0 and np.median(ret24)>.025:
            hedge=-1;hedge_until=t
        if t>=hedge_until:
            hedge=-1
            if t>=hedge_last+504 and crisis and np.median(ret24)<-.025:
                eligible=[j for j in range(4) if ret168[j]<0]
                if eligible:
                    vol=np.std(np.diff(lc[t-168:t+1],axis=0),axis=0,ddof=1)
                    hedge=sorted(eligible,key=lambda j:
                        (-round(float(-ret168[j]/max(vol[j],1e-5)),12),j))[0]
                    hedge_last=t;hedge_until=t+168
        if hedge>=0 and t<hedge_until:stress[t,hedge]=-1.
        # Event admission metrics use ONLY completed-bar prices/funding.
        if np.any(opp[t]):edge[t,1]=float(opp[t]@ret168)
        if np.any(rv[t]):
            edge[t,2]=float(rv[t]@ret168)
            carry_cost[t,2]=float(rv[t]@funding168)
        if np.any(stress[t]):edge[t,3]=float(stress[t]@ret72)
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
    # Sign invariant: a short must earn positive trend evidence during a falling tape.
    falling=c.copy()
    falling[2400:]*=np.exp(-.005*np.arange(n-2400))[:,None]
    z=source_bundle(falling,q,r,e)
    active=np.flatnonzero(np.abs(z[3]).sum(axis=1)>0)
    assert len(active)>0 and np.any(z[4]["edge"][active,3]>0)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BK_CAUSAL_NATIVE_CARRY_SOURCE_PASS")
