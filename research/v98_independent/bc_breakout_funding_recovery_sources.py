#!/usr/bin/env python3
"""BC preregistered independent breakout / native funding carry / recovery sources.
Only completed close[t], quote[t], and native funding events <=t. Fill earliest t+1.
"""
from __future__ import annotations
from collections import deque
import numpy as np

WARMUP=2160
EPOCH=336

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BC_SOURCE_INPUT")
    n=len(c)
    lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    core_current=np.zeros(4)
    rv_current=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_until=-1;rv_last=-100000
    stress_asset=-1;stress_until=-1;stress_last=-100000
    funding=[deque(maxlen=18) for _ in range(4)]
    for t in range(n):
        for j in range(4):
            if e[t,j]:funding[j].append(float(r[t,j]))
        if t<WARMUP:continue
        r24=lc[t]-lc[t-24]
        r48=lc[t]-lc[t-48]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        if (t-WARMUP)%EPOCH==0:
            breakout=c[t]>np.max(c[t-504:t],axis=0)
            eligible=(r336>0)&(r1008>0)&breakout
            vol=np.std(lr[t-335:t+1],axis=0)
            inv=np.where(eligible,1./np.maximum(vol,1e-5),0.)
            core_current[:]=0.
            if np.any(inv>0):
                raw=inv/inv.sum()
                core_current=np.minimum(raw,.45)
        core[t]=core_current
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+336:
                vol72=np.std(lr[t-71:t+1],axis=0)
                vol504=np.std(lr[t-503:t+1],axis=0)
                prev_high=np.max(c[t-168:t],axis=0)
                prior_high=np.max(c[t-169:t-1],axis=0)
                crossing=(c[t]>prev_high)&(c[t-1]<=prior_high)
                prior_q=np.mean(q[t-168:t],axis=0)
                recent_q=np.sum(q[t-23:t+1],axis=0)
                eligible=(r1008>0)&(vol72<.65*np.maximum(vol504,1e-8))&crossing&(
                    recent_q>1.2*24*np.maximum(prior_q,1e-8))
                indices=np.flatnonzero(eligible)
                if len(indices):
                    opp_asset=sorted(indices,key=lambda j:(-round(float(r24[j]),12),int(j)))[0]
                    opp_last=t;opp_until=t+120
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            rv_current[:]=0.
            if t>=rv_last+168 and all(len(x)==18 for x in funding):
                avg=np.array([np.mean(x) for x in funding])
                low=int(np.argmin(avg));high=int(np.argmax(avg))
                if (low!=high and avg[high]-avg[low]>=.0002
                    and abs(r168[low]-r168[high])<.04):
                    rv_current[low]=.5;rv_current[high]=-.5
                    rv_last=t;rv_until=t+120
        rv[t]=rv_current
        if t>=stress_until:
            stress_asset=-1
            if (t>=stress_last+336 and np.count_nonzero(r336<0)>=3
                and np.count_nonzero(r48>0)>=3):
                eligible=np.flatnonzero((r336<0)&(r48>0))
                if len(eligible):
                    stress_asset=sorted(eligible,key=lambda j:(-round(float(r48[j]),12),int(j)))[0]
                    stress_last=t;stress_until=t+168
        if stress_asset>=0 and t<stress_until:stress[t,stress_asset]=1.
        if np.count_nonzero(r336>0)>=3 and float(np.median(r168))>0:
            states[t]="EXPANSION"
        elif np.count_nonzero(r336<0)>=3 and np.count_nonzero(r48>0)>=3:
            states[t]="RECOVERY"
        elif np.count_nonzero(r168<0)>=3:
            states[t]="DEFENSE"
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
    print("BC_CAUSAL_SOURCE_PASS")
