#!/usr/bin/env python3
"""V98 AT independent completed-bar funding/acceleration seven-slot sources."""
from __future__ import annotations
import numpy as np
WARMUP=2160

def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=np.float64) for x in
                 (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,h,l,r,e,q)) or
        np.any(c<=0) or np.any(l<=0) or np.any(l>c) or
        np.any(h<c) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AT_CLEAN4_INPUT")
    n=len(c); logc=np.log(c)
    lr=np.diff(logc,axis=0,prepend=logc[:1])
    core=np.zeros_like(c); opp=np.zeros_like(c)
    rv=np.zeros_like(c); stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U10")
    opp_end=-1; opp_asset=-1
    stress_end=-1; stress_last=-1000000
    for t in range(WARMUP,n):
        r12=logc[t]-logc[t-12]
        r72=logc[t]-logc[t-72]
        r168=logc[t]-logc[t-168]
        r720=logc[t]-logc[t-720]
        stdev=np.std(lr[t-719:t+1],axis=0)
        strength=np.where((r720>0)&(c[t]>np.median(c[t-168:t],axis=0)),
                          np.maximum(0.,r720)/(np.maximum(stdev,1e-6)*np.sqrt(720.)),0.)
        if strength.sum()>0:
            core[t]=strength/strength.sum()
        if t>=opp_end:
            opp_asset=-1
            previous72=logc[t-12]-logc[t-84]
            gate=(r12>.045)&(np.abs(previous72)<.08)&(
                q[t]>2.*np.median(q[t-168:t],axis=0))
            if np.any(gate):
                rank=np.lexsort((np.arange(4),-r12))
                opp_asset=int(next(j for j in rank if gate[j]))
                opp_end=t+72
        if t<opp_end and opp_asset>=0:
            opp[t,opp_asset]=1.
        event_counts=np.sum(e[t-719:t+1],axis=0)
        mean_funding=np.sum(r[t-719:t+1]*e[t-719:t+1],axis=0)/np.maximum(event_counts,1.)
        cheap=int(np.argmin(mean_funding))
        dear=int(np.argmax(mean_funding))
        if (cheap!=dear and mean_funding[dear]-mean_funding[cheap]>.00020
            and abs(float(r168[cheap]-r168[dear]))<.10):
            rv[t,cheap]=.5; rv[t,dear]=-.5
        breadth=int(np.count_nonzero(r72<0))
        if (t>=stress_end and t>=stress_last+168 and
            float(np.median(r72))<-.10 and breadth>=3):
            stress_last=t; stress_end=t+48
        if t<stress_end:
            stress[t]=-.25
        if float(np.median(r720))>0 and np.count_nonzero(r168>0)>=3:
            states[t]="RISK_ON"
        elif float(np.median(r72))<0 and np.count_nonzero(r168>0)<=1:
            states[t]="DEFENSIVE"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    t=np.arange(2700,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0003,.0001,.0002,.0004]]))
    h,l=c*1.005,c*.995
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    a=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-40:]*=1.1
    b=source_bundle(changed,np.maximum(h,changed),np.minimum(l,changed),r,e,q)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.all(np.isfinite(x))
        assert np.all(np.abs(x).sum(axis=1)<=1.+1e-12)
        assert not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    return True
if __name__=="__main__":
    assert causal_check()
    print("AT_SOURCE_CAUSAL_PASS")
