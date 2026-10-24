#!/usr/bin/env python3
"""AU independent monthly funding-adjusted leadership + sparse signed sleeves.
Only completed-hour Clean4 data. No 2025, no external engines.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
MONTH=720

def source_bundle(close, quote, rate, event):
    c,q,r,e=(np.asarray(a,dtype=np.float64) for a in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(a.shape!=c.shape for a in (q,r,e))
        or any(not np.isfinite(a).all() for a in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AU_SOURCE_INPUT")
    n=len(c); lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c); opp=np.zeros_like(c)
    rv=np.zeros_like(c); stress=np.zeros_like(c)
    state=np.full(n,"TRANSITION",dtype="<U12")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    stress_asset=-1;stress_until=-1;stress_last=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r336=lc[t]-lc[t-336]
        if (t-WARMUP)%MONTH==0:
            r1008=lc[t]-lc[t-1008]
            volatility=np.std(lr[t-1007:t+1],axis=0)*np.sqrt(1008.)
            # Exactly the previous 1008h (126 native 8h events).
            events=np.sum(e[t-1007:t+1],axis=0)
            meanfund=np.sum(r[t-1007:t+1]*e[t-1007:t+1],axis=0)/np.maximum(events,1.)
            score=(.6*r1008+.4*r336-90.*meanfund)/np.maximum(volatility,.05)
            eligible=(score>0)&(r336>0)
            ranked=sorted((int(j) for j in range(4) if eligible[j]),
                          key=lambda j:(-round(float(score[j]),12),j))
            cur_core[:]=0.
            if ranked:
                cur_core[ranked[0]]=.7 if len(ranked)>1 else 1.
                if len(ranked)>1:cur_core[ranked[1]]=.3
            # Risk-adjusted dispersion: monthly long/short, funding-cost filter.
            riskadj=r336/np.maximum(np.std(lr[t-335:t+1],axis=0)*np.sqrt(336.),.05)
            ordered=sorted(range(4),key=lambda j:(-round(float(riskadj[j]),12),j))
            strong,weak=ordered[0],ordered[-1]
            spread=float(r336[strong]-r336[weak])
            carry_cost=90.*float(meanfund[strong]-meanfund[weak])
            cur_rv[:]=0.
            if strong!=weak and spread>.08 and carry_cost<.015:
                cur_rv[strong]=.5;cur_rv[weak]=-.5
        core[t]=cur_core
        rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            breadth=int(np.count_nonzero(r24>.03))
            ratio=q[t]/np.maximum(np.median(q[t-336:t],axis=0),1e-8)
            candidates=[int(j) for j in range(4) if r24[j]>.03 and ratio[j]>1.4]
            if breadth>=3 and candidates and t>=opp_last+168:
                opp_asset=sorted(candidates,key=lambda j:(-round(float(r24[j]),12),j))[0]
                opp_last=t;opp_until=t+96
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=stress_until:
            stress_asset=-1
            if (t>=stress_last+336 and np.count_nonzero(r72<-.10)>=3
                and r336[0]<0):
                vol=np.std(lr[t-335:t+1],axis=0)
                stress_asset=sorted(range(4),key=lambda j:(-round(float(vol[j]),12),j))[0]
                stress_last=t;stress_until=t+72
        if stress_asset>=0 and t<stress_until:stress[t,stress_asset]=-1.
        breadth336=int(np.count_nonzero(r336>0))
        if r336[0]>0 and breadth336>=3:state[t]="EXPANSION"
        elif r336[0]<0 and breadth336<=1:state[t]="CONTRACTION"
    return core,opp,rv,stress,{"state":state}

def causal_check():
    n=2520
    t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    changed=c.copy();changed[-32:]*=1.1
    b=source_bundle(changed,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-32],y[:-32])
        assert np.isfinite(x).all()
        assert not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-32],b[4]["state"][:-32])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AU_SOURCE_CAUSAL_PASS")
