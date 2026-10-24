#!/usr/bin/env python3
"""BM: volatility-compression expansion, orthogonal rotation and distributed stress hedge."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BM_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_weights=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    pair=(-1,-1);pair_until=-1;pair_last=-100000
    hedge=();hedge_until=-1;hedge_last=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336];r672=lc[t]-lc[t-672]
        fund168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(r168<0)>=3 and np.median(r72)<-.05)
        bull=bool(np.count_nonzero(r168>0)>=3 and np.median(r336)>0)
        if crisis:states[t]="CRISIS"
        elif bull:states[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            # Long-run breadth core: no ex-post fixed asset selection.
            eligible=(r336>0)&(r672>0)&(fund168<.03)
            core_weights=eligible.astype(float)
            if core_weights.sum():core_weights/=core_weights.sum()
        core[t]=core_weights
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+1008 and bull:
                v48=np.std(np.diff(lc[t-48:t+1],axis=0),axis=0,ddof=1)
                v336=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0,ddof=1)
                eligible=[j for j in range(4) if
                    v48[j]<.75*v336[j] and r336[j]>.06 and
                    c[t,j]>1.01*np.max(c[t-168:t,j]) and
                    fund168[j]<.03]
                if eligible:
                    # Compression expansion; deterministic best compression rank.
                    opp_asset=sorted(eligible,key=lambda j:
                        (round(float(v48[j]/max(v336[j],1e-8)),12),j))[0]
                    opp_last=t;opp_until=t+336
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.
            edge[t,1]=float(r168[opp_asset])
        if t>=pair_until:
            pair=(-1,-1)
            if t>=pair_last+1008 and states[t]=="NEUTRAL":
                long=int(np.argmax(r72));short=int(np.argmin(r72))
                spread=float(r72[long]-r72[short])
                # Dispersion continuation after a 72h rotation, not reversal.
                if (long!=short and spread>.14 and r336[long]>.05
                    and r336[short]<0 and fund168[long]<fund168[short]):
                    pair=(long,short);pair_last=t;pair_until=t+504
        if pair[0]>=0 and t<pair_until:
            rv[t,pair[0]]=.5;rv[t,pair[1]]=-.5
            edge[t,2]=float(rv[t]@r72)
            carry_cost[t,2]=float(rv[t]@fund168)
        if t>=hedge_until:
            hedge=()
            if t>=hedge_last+672 and crisis and np.median(r24)<-.02:
                # Diversified crisis short: only completed-bar weak assets,
                # no asset-specific winners, no short outside systemic stress.
                eligible=[j for j in range(4) if r168[j]<-.04
                          and r24[j]<0 and fund168[j]>=0]
                if len(eligible)>=2:
                    hedge=tuple(eligible);hedge_last=t;hedge_until=t+168
        if hedge and t<hedge_until:
            stress[t,list(hedge)]=-1./len(hedge)
            edge[t,3]=float(stress[t]@r72)
            carry_cost[t,3]=float(stress[t]@fund168)
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
    assert np.all(np.sum(np.abs(a[3]),axis=1)<=1.+1e-10)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BM_COMPRESSION_ROTATION_STRESS_CAUSAL_PASS")
