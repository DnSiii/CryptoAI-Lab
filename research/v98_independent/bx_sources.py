#!/usr/bin/env python3
"""BX: causal all-asset momentum, breakout, native carry dispersion, crash/recovery sources.
Independent four-book portfolio; training data end 2024-12-31 only.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
CORE_EPOCH=336
SAT_EPOCH=168

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BX_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    vol=np.zeros(n)
    signed=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        crisis=np.median(r72)<-.08
        bull=np.median(r336)>.08 and np.count_nonzero(r168>0)>=3
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%SAT_EPOCH:continue
        v=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0)
        vol[t]=float(np.median(v))
        if (t-WARMUP)%CORE_EPOCH==0:
            r672=lc[t]-lc[t-672]
            eligible=np.flatnonzero(r672>0)
            if len(eligible):
                ranked=sorted(eligible,key=lambda j:(-r672[j]/max(v[j],.005),int(j)))[:2]
                scores=np.array([r672[j]/max(v[j],.005) for j in ranked])
                core[t,ranked]=scores/scores.sum()
            funding=signed[t]-signed[t-336]
            low=int(np.argmin(funding));high=int(np.argmax(funding))
            if (low!=high and funding[high]-funding[low]>.005
                and r168[low]>=r168[high]-.10):
                rv[t,low]=.5;rv[t,high]=-.5
        candidates=np.flatnonzero(
            (r168>.08)&(r24>.01)&(c[t]>np.max(c[t-168:t],axis=0)))
        if len(candidates):
            j=max(candidates,key=lambda k:(r168[k]/max(v[k],.005),-int(k)))
            opp[t,j]=1.
        if crisis:
            weak=np.argsort(r72,kind="stable")[:2]
            stress[t,weak]=-.5
        elif np.median(r168)<-.15 and np.median(r24)>.04:
            strong=np.argsort(-r24,kind="stable")[:2]
            stress[t,strong]=.5
    return core,opp,rv,stress,{"state":state,"vol":vol}

def static_check():
    n=2800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0002,.0001,.0004]])+
                 .04*np.sin(t[:,None]/80.+np.arange(4)))
    q=np.full_like(c,1e8)
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-45:]*=1.2
    rr=r.copy();rr[-45:]*=4
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-45],y[:-45])
        assert not np.any(x[:WARMUP])
        assert np.isfinite(x).all()
    for k in ("state","vol"):
        assert np.array_equal(a[4][k][:-45],b[4][k][:-45])
    assert np.all(a[0].sum(axis=1)<=1.+1e-10)
    assert np.allclose(a[2].sum(axis=1),0.)
    assert np.all(np.abs(a[3]).sum(axis=1)<=1.+1e-10)
    return True

if __name__=="__main__":
    assert static_check()
    print("BX_CAUSAL_ALL_ASSET_SOURCES_PASS")
