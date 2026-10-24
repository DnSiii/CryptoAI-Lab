#!/usr/bin/env python3
"""V98 AY preregistered independent cross-sectional dispersion seven-slot sources.
Close[t] is known only after hour t; actual fills cannot precede open[t+1].
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
CORE_EPOCH=1008
RV_EPOCH=504

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AY_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"MIXED",dtype="<U12")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    stress_until=-1;stress_last=-1000000;stress_seen=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        if (t-WARMUP)%CORE_EPOCH==0:
            r1008=lc[t]-lc[t-1008]
            ev=e[t-1007:t+1]
            meanfund=np.sum(r[t-1007:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            net=r1008-126.*meanfund
            past=lr[t-335:t+1]
            downside=np.sqrt(np.mean(np.minimum(past,0.)**2,axis=0))*np.sqrt(336.)
            score=net/(.05+downside)
            ranked=sorted((int(j) for j in range(4) if net[j]>0 and r168[j]>0),
                          key=lambda j:(-round(float(score[j]),12),j))[:3]
            cur_core[:]=0.
            weights=np.array([.5,.3,.2])[:len(ranked)]
            if len(ranked):
                weights=weights/weights.sum()
                for j,w in zip(ranked,weights):cur_core[j]=w
        if (t-WARMUP)%RV_EPOCH==0:
            ev=e[t-503:t+1]
            meanfund=np.sum(r[t-503:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            net=r336-42.*meanfund
            rank=sorted(range(4),key=lambda j:(-round(float(net[j]),12),j))
            hi,lo=rank[0],rank[-1]
            cur_rv[:]=0.
            if (net[hi]-net[lo]>.15 and r168[hi]>0
                and meanfund[hi]<=meanfund[lo]+.0003):
                cur_rv[hi]=.5
                cur_rv[lo]=-.5
        core[t]=cur_core
        rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+504:
                median_r72=float(np.median(r72))
                prev_high=np.max(c[t-336:t],axis=0)
                median_q=np.median(q[t-168:t],axis=0)
                ev=e[t-503:t+1]
                mf=np.sum(r[t-503:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
                candidates=[j for j in range(4)
                    if r72[j]>.06 and c[t,j]>prev_high[j]
                    and r72[j]>median_r72+.035
                    and q[t,j]>1.2*max(float(median_q[j]),1e-8)
                    and mf[j]<=float(np.median(mf))+.0002]
                if candidates:
                    opp_asset=sorted(candidates,
                        key=lambda j:(-round(float(r72[j]-median_r72),12),j))[0]
                    opp_last=t;opp_until=t+192
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if np.count_nonzero(r168<0)>=3:stress_seen=t
        if t>=stress_until and t>=stress_last+504 and t-stress_seen<=168:
            if np.count_nonzero(r24>0)>=3 and float(np.median(r24))>.025:
                stress_last=t;stress_until=t+168
        if t<stress_until:
            stress[t,0]=.5;stress[t,1]=.5
        if float(np.median(r336))>0 and np.count_nonzero(r168>0)>=3:
            states[t]="EXPANSION"
        elif np.count_nonzero(r168<0)>=3:
            states[t]="DISLOCATION"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2750;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    changed=c.copy();changed[-40:]*=1.1
    b=source_bundle(changed,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    assert np.allclose(np.sum(a[2],axis=1),0.)
    return True
if __name__=="__main__":
    assert causal_check()
    print("AY_SOURCE_CAUSAL_PASS")
