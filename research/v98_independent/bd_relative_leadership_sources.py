#!/usr/bin/env python3
"""BD independent relative leadership, acceleration, trend dispersion and crash hedge.
Signals at completed close[t], earliest physical execution at next open[t+1].
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=168

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BD_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_until=-1;rv_last=-100000
    stress_asset=-1;stress_until=-1;stress_last=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r48=lc[t]-lc[t-48]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        if (t-WARMUP)%EPOCH==0:
            eligible=np.flatnonzero((r1008>0)&(r336>0))
            ranked=sorted(eligible,key=lambda j:(-round(float(r1008[j]),12),int(j)))[:2]
            cur_core[:]=0.
            if len(ranked)==1:cur_core[ranked[0]]=1.
            elif len(ranked)==2:
                cur_core[ranked[0]]=.6;cur_core[ranked[1]]=.4
        core[t]=cur_core
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+168:
                median_q=np.median(q[t-168:t],axis=0)
                eligible=np.flatnonzero((r24>.03)&(r168>.08)&(
                    q[t]>1.1*np.maximum(median_q,1e-8)))
                if len(eligible):
                    opp_asset=sorted(eligible,key=lambda j:(-round(float(r24[j]),12),int(j)))[0]
                    opp_last=t;opp_until=t+72
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            cur_rv[:]=0.
            if t>=rv_last+336:
                rank=sorted(range(4),key=lambda j:(-round(float(r336[j]),12),j))
                hi,lo=rank[0],rank[-1]
                if r336[hi]-r336[lo]>.08 and r168[hi]-r168[lo]>.02:
                    cur_rv[hi]=.5;cur_rv[lo]=-.5
                    rv_last=t;rv_until=t+336
        rv[t]=cur_rv
        if t>=stress_until:
            stress_asset=-1
            if (t>=stress_last+168 and np.count_nonzero(r48<0)>=3
                and float(np.median(r168))<0):
                stress_asset=int(np.argmin(r168))
                stress_last=t;stress_until=t+48
        if stress_asset>=0 and t<stress_until:stress[t,stress_asset]=-1.
        if np.count_nonzero(r336>0)>=3:
            states[t]="EXPANSION"
        elif np.count_nonzero(r48<0)>=3 and float(np.median(r168))<0:
            states[t]="DRAWDOWN"
        elif float(np.max(r168)-np.min(r168))>.18:
            states[t]="ROTATION"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2800;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                  .04*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-30:]*=1.2
    b=source_bundle(cc,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-30],y[:-30])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-30],b[4]["state"][:-30])
    assert np.all(np.sum(a[0],axis=1)<=1.+1e-10)
    assert np.all(np.abs(a[2].sum(axis=1))<1e-10)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BD_CAUSAL_SOURCE_PASS")
