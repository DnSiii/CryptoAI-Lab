#!/usr/bin/env python3
"""V98 AW distinct causal long-biased component sources, no benchmark data."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1344

def source_bundle(close,rate,event):
    c,r,e=(np.asarray(x,dtype=float) for x in (close,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e))
        or any(not np.isfinite(x).all() for x in (c,r,e))
        or np.any(c<=0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AW_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"DEFENSIVE",dtype="<U10")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    stress_until=-1;stress_last=-1000000;stress_seen=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r336=lc[t]-lc[t-336]
        if (t-WARMUP)%EPOCH==0:
            r1344=lc[t]-lc[t-1344]
            ev=e[t-1343:t+1]
            meanfund=np.sum(r[t-1343:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            net=r1344-168.*meanfund
            eligible=(net>0)&(r336>0)
            scores=np.where(eligible,net,0.)
            cur_core=scores/scores.sum() if scores.sum()>0 else np.zeros(4)
            # Lower-half 336h performers with positive trend and cheap carry.
            order=sorted(range(4),key=lambda j:(round(float(r336[j]),12),j))
            eligible_rv=[j for j in order[:2] if r336[j]>0]
            cur_rv[:]=0.
            if eligible_rv:
                cheap=sorted(eligible_rv,key=lambda j:(round(float(meanfund[j]),12),j))[0]
                if meanfund[cheap]<float(np.median(meanfund))-.00010:
                    cur_rv[cheap]=1.
        core[t]=cur_core
        rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+504:
                prevmax=np.max(c[t-336:t],axis=0)
                candidates=[int(j) for j in range(4)
                            if c[t,j]>prevmax[j] and r72[j]>.06]
                if candidates:
                    opp_asset=sorted(candidates,key=lambda j:(-round(float(r72[j]),12),j))[0]
                    opp_last=t;opp_until=t+168
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if np.count_nonzero(r72<-.12)>=3:stress_seen=t
        if t>=stress_until:
            if t>=stress_last+504 and t-stress_seen<=168 and r24[0]>.025:
                stress_last=t;stress_until=t+168
        if t<stress_until:
            stress[t,0]=.5;stress[t,1]=.5
        if float(np.median(r336))>0:states[t]="EXPANSION"
        elif float(np.median(r72))>0:states[t]="RECOVERY"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2700;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,r,e)
    d=c.copy();d[-40:]*=1.1
    b=source_bundle(d,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    return True
if __name__=="__main__":
    assert causal_check()
    print("AW_SOURCE_CAUSAL_PASS")
