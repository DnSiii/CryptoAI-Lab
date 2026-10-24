#!/usr/bin/env python3
"""CA original BTC/ETH-only seven-slot source signals; no prior engine alpha imports."""
from __future__ import annotations
import numpy as np
WARMUP=2160
CORE_EPOCH=504

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (q,r,e)) or
        any(not np.isfinite(x).all() for x in (c,q,r,e)) or
        np.any(c<=0) or np.any(q<0) or
        not np.isin(e,(0.,1.)).all()):
        raise ValueError("CA_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    vol=np.zeros(n)
    opp_end=rv_end=stress_end=-1
    opp_last=rv_last=stress_last=-100000
    rv_long=rv_short=-1
    for t in range(WARMUP,n):
        r72=lc[t,:2]-lc[t-72,:2]
        r168=lc[t,:2]-lc[t-168,:2]
        r336=lc[t,:2]-lc[t-336,:2]
        r1008=lc[t,:2]-lc[t-1008,:2]
        rms336=np.sqrt(np.mean(np.diff(lc[t-336:t+1,:2],axis=0)**2,axis=0))
        rms1008=np.sqrt(np.mean(np.diff(lc[t-1008:t+1,:2],axis=0)**2,axis=0))
        rms168=np.sqrt(np.mean(np.diff(lc[t-168:t+1,:2],axis=0)**2,axis=0))
        vol[t]=float(np.median(rms336))
        if np.median(r72)<-.08:state[t]="CRISIS"
        elif np.all(r336>0) and r1008[0]>0:state[t]="BULL"
        if (t-WARMUP)%CORE_EPOCH==0:
            eligible=np.flatnonzero(r1008>0)
            if len(eligible):
                inv=1./np.maximum(rms336[eligible],.0001)
                core[t,eligible]=inv/inv.sum()
        if t>=opp_end:
            if (t>=opp_last+1008 and
                rms336[1]<.75*rms1008[1] and r72[1]>.04 and
                c[t,1]>np.max(c[t-168:t,1])):
                opp_last=t;opp_end=t+504
        if t<opp_end:opp[t,1]=1.
        if t>=rv_end:
            rv_long=rv_short=-1
            native=np.sum(r[t-335:t+1,:2]*e[t-335:t+1,:2],axis=0)
            if (t>=rv_last+1008 and abs(native[0]-native[1])>.003
                and abs(r168[0]-r168[1])<.10):
                rv_long=int(np.argmin(native))
                rv_short=1-rv_long
                rv_last=t;rv_end=t+672
        if t<rv_end and rv_long>=0:
            rv[t,rv_long]=.5;rv[t,rv_short]=-.5
        if t>=stress_end:
            if (t>=stress_last+504 and np.median(r72)<-.08
                and r72[1]<-.10 and rms168[1]>1.5*rms1008[1]):
                stress_last=t;stress_end=t+168
        if t<stress_end:stress[t,1]=-1.
    return core,opp,rv,stress,{"state":state,"vol":vol}

def static_check():
    n=2800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0003,.0002,.0001,.0004]])+
                 .05*np.sin(t[:,None]/80.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-45:]*=1.2
    rr=r.copy();rr[-45:]*=4
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-45],y[:-45])
        assert not np.any(x[:WARMUP])
        assert np.isfinite(x).all()
        assert not np.any(x[:,2:])
    for k in ("state","vol"):
        assert np.array_equal(a[4][k][:-45],b[4][k][:-45])
    assert np.all(a[0].sum(axis=1)<=1.+1e-10)
    assert np.allclose(a[2].sum(axis=1),0.)
    return True

if __name__=="__main__":
    assert static_check()
    print("CA_CAUSAL_MAJORS_ONLY_SOURCES_PASS")
