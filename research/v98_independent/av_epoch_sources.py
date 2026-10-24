#!/usr/bin/env python3
"""V98 AV distinct causal 4-sleeve 1h sources, Dec2022-Dec2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,rate,event):
    c,r,e=(np.asarray(a,dtype=np.float64) for a in (close,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(a.shape!=c.shape for a in (r,e))
        or any(not np.isfinite(a).all() for a in (c,r,e))
        or np.any(c<=0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AV_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"MIXED",dtype="<U10")
    cur_core=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    rv_weak=-1;rv_strong=-1;rv_until=-1;rv_last=-1000000
    stress_until=-1;stress_last=-1000000
    for t in range(WARMUP,n):
        r48=lc[t]-lc[t-48]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r672=lc[t]-lc[t-672]
        r1008=lc[t]-lc[t-1008]
        if (t-WARMUP)%EPOCH==0:
            r1344=lc[t]-lc[t-1344]
            vol672=np.std(lr[t-671:t+1],axis=0)*np.sqrt(672.)
            ev=np.sum(e[t-1343:t+1],axis=0)
            meanfund=np.sum(r[t-1343:t+1]*e[t-1343:t+1],axis=0)/np.maximum(ev,1.)
            score=(r1344-126.*meanfund)/np.maximum(vol672,.05)
            ranked=sorted((int(j) for j in range(4)
                           if score[j]>0 and r672[j]>0),
                          key=lambda j:(-round(float(score[j]),12),j))
            cur_core[:]=0.
            if ranked:
                cur_core[ranked[0]]=.6 if len(ranked)>1 else 1.
                if len(ranked)>1:cur_core[ranked[1]]=.4
        core[t]=cur_core
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+336:
                candidates=[int(j) for j in range(4)
                            if e[t,j]==1. and r[t,j]<-.0004 and r48[j]>0]
                if candidates:
                    opp_asset=sorted(candidates,key=lambda j:(round(float(r[t,j]),12),j))[0]
                    opp_last=t;opp_until=t+48
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            rv_weak=rv_strong=-1
            if t>=rv_last+336:
                ordered=sorted(range(4),key=lambda j:(round(float(r168[j]),12),j))
                weak,strong=ordered[0],ordered[-1]
                if (float(r168[strong]-r168[weak])>.18
                    and r72[weak]>0 and r72[strong]<0):
                    rv_weak=weak;rv_strong=strong
                    rv_last=t;rv_until=t+72
        if rv_weak>=0 and t<rv_until:
            rv[t,rv_weak]=.5;rv[t,rv_strong]=-.5
        if t>=stress_until:
            if (t>=stress_last+336 and r168[0]<-.15
                and np.count_nonzero(r168<0)>=3):
                stress_last=t;stress_until=t+96
        if t<stress_until:stress[t,0]=-1.
        v168=float(np.median(np.std(lr[t-167:t+1],axis=0)))
        v672=float(np.median(np.std(lr[t-671:t+1],axis=0)))
        ratio=v168/max(v672,1e-8)
        if r1008[0]>0 and ratio<1.5:states[t]="RISK_ON"
        elif r1008[0]<0 or ratio>2.:states[t]="RISK_OFF"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2520;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,r,e)
    d=c.copy();d[-35:]*=1.1
    b=source_bundle(d,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-35],y[:-35])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-35],b[4]["state"][:-35])
    return True
if __name__=="__main__":
    assert causal_check()
    print("AV_SOURCE_CAUSAL_PASS")
