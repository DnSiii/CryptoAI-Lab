#!/usr/bin/env python3
"""BB independent: trend re-entry, native funding-aligned pair continuation, panic hedge.
Only completed close[t] and funding events <=t. Orders earliest open[t+1].
"""
from __future__ import annotations
from collections import deque
import numpy as np

WARMUP=2160
EPOCH=168

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (q,r,e)) or
        any(not np.isfinite(x).all() for x in (c,q,r,e)) or
        np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BB_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"TRANSITION",dtype="<U12")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_until=-1;rv_last=-100000
    stress_asset=-1;stress_until=-1;stress_last=-100000
    funding=[deque(maxlen=24) for _ in range(4)]
    for t in range(n):
        for j in range(4):
            if e[t,j]:funding[j].append(float(r[t,j]))
        if t<WARMUP:continue
        r6=lc[t]-lc[t-6];r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72];r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336];r1008=lc[t]-lc[t-1008]
        if (t-WARMUP)%EPOCH==0:
            vol=np.std(lr[t-167:t+1],axis=0)
            eligible=(r168>0)&(r1008>0)
            inv=np.where(eligible,1./np.maximum(vol,1e-5),0.)
            cur_core[:]=0.
            active=eligible.copy();remaining=1.
            for _ in range(4):
                if not active.any() or remaining<=1e-12:break
                ix=np.flatnonzero(active)
                proposal=remaining*inv[ix]/inv[ix].sum()
                excess=proposal>.5
                if not excess.any():
                    cur_core[ix]=proposal
                    break
                capped=ix[excess]
                cur_core[capped]=.5
                remaining-=.5*len(capped)
                active[capped]=False
        core[t]=cur_core
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+240:
                med=np.median(q[t-168:t],axis=0)
                candidates=[j for j in range(4)
                    if r1008[j]>0 and r24[j]<-.06 and r6[j]>.02
                    and q[t,j]>1.5*max(float(med[j]),1e-8)]
                if candidates:
                    opp_asset=sorted(candidates,key=lambda j:(-round(float(r6[j]),12),j))[0]
                    opp_last=t;opp_until=t+96
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            cur_rv[:]=0.
            if t>=rv_last+168 and all(len(x)==24 for x in funding):
                f=np.array([np.mean(x) for x in funding])
                low=int(np.argmin(f));high=int(np.argmax(f))
                if (low!=high and f[high]-f[low]>=.00015
                    and r72[low]-r72[high]>.03):
                    cur_rv[low]=.5;cur_rv[high]=-.5
                    rv_last=t;rv_until=t+72
        rv[t]=cur_rv
        if t>=stress_until:
            stress_asset=-1
            if (t>=stress_last+168 and np.count_nonzero(r168<0)>=3
                and float(np.median(r24))<-.03):
                stress_asset=int(np.argmin(r168))
                stress_last=t;stress_until=t+96
        if stress_asset>=0 and t<stress_until:stress[t,stress_asset]=-1.
        if np.count_nonzero(r336>0)>=3 and float(np.median(r168))>0:
            states[t]="EXPANSION"
        elif np.count_nonzero(r168<0)>=3 and float(np.median(r24))<-.03:
            states[t]="PANIC"
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
    print("BB_CAUSAL_SOURCE_PASS")
