#!/usr/bin/env python3
"""BE original causal slow net-momentum and event sleeves; no holdout or benchmarks."""
from __future__ import annotations
import numpy as np

WARMUP=2160
EPOCH=672
HOLD_OPP=168
HOLD_RV=336
HOLD_STRESS=72
COOLDOWN=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (q,r,e)) or
        any(not np.isfinite(x).all() for x in (c,q,r,e)) or
        np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BE_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"MIXED",dtype="<U12")
    core_asset=-1
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_pair=(-1,-1);rv_until=-1;rv_last=-100000
    stress_asset=-1;stress_until=-1;stress_last=-100000
    # Causal funding cost is the sum of native event rates over 168 completed hours.
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        r1344=lc[t]-lc[t-1344]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        if (t-WARMUP)%EPOCH==0:
            net_score=r1344-8.*f168
            eligible=[j for j in range(4) if net_score[j]>.08]
            if not eligible:
                core_asset=-1
            else:
                best=sorted(eligible,key=lambda j:(-round(float(net_score[j]),12),j))[0]
                if core_asset not in eligible or net_score[best]-net_score[core_asset]>.08:
                    core_asset=best
        if core_asset>=0:core[t,core_asset]=1.
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+COOLDOWN:
                eligible=[j for j in range(4) if
                    r1008[j]>0 and r168[j]<-.08 and r24[j]>.035
                    and f168[j]<.012]
                if eligible:
                    opp_asset=sorted(eligible,
                        key=lambda j:(-round(float(r24[j]-r168[j]),12),j))[0]
                    opp_last=t;opp_until=t+HOLD_OPP
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            rv_pair=(-1,-1)
            if t>=rv_last+COOLDOWN:
                eligible=[]
                for long in range(4):
                    for short in range(4):
                        if long==short:continue
                        trend=float(r336[long]-r336[short])
                        carry=float(2.*(f168[short]-f168[long]))
                        if trend>.07 and carry>.0035:
                            eligible.append((trend+carry,long,short))
                if eligible:
                    _,long,short=sorted(eligible,
                        key=lambda z:(-round(z[0],12),z[1],z[2]))[0]
                    rv_pair=(long,short);rv_last=t;rv_until=t+HOLD_RV
        if rv_pair[0]>=0 and t<rv_until:
            rv[t,rv_pair[0]]=.5;rv[t,rv_pair[1]]=-.5
        if t>=stress_until:
            stress_asset=-1
            if t>=stress_last+COOLDOWN and np.count_nonzero(r72<-.09)>=3:
                eligible=[j for j in range(4) if r24[j]>.045 and r336[j]>0]
                if eligible:
                    stress_asset=sorted(eligible,
                        key=lambda j:(-round(float(r24[j]),12),j))[0]
                    stress_last=t;stress_until=t+HOLD_STRESS
        if stress_asset>=0 and t<stress_until:stress[t,stress_asset]=1.
        if np.count_nonzero(r336>0)>=3 and np.median(r336)>.04:
            states[t]="BULL"
        elif np.count_nonzero(r72<-.09)>=3:
            states[t]="CRISIS"
        elif float(r336.max()-r336.min())>.30:
            states[t]="DISPERSION"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2850;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                  .06*np.sin(t[:,None]/70.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-50:]*=1.2
    rr=r.copy();rr[-50:]*=5.
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-50],y[:-50])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-50],b[4]["state"][:-50])
    assert np.all(np.sum(a[0],axis=1)<=1.+1e-10)
    assert np.all(np.abs(a[2].sum(axis=1))<1e-10)
    return True

if __name__=="__main__":
    assert causal_check()
    print("BE_CAUSAL_SOURCES_PASS")
