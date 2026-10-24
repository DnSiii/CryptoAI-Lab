#!/usr/bin/env python3
"""BW independent slow major growth and distinct SOL/BNB carry momentum sleeves."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BW_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    oa=-1;ou=-1;ol=-100000
    pair=False;pu=-1;pl=-100000
    hedge=False;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336]
        r672=lc[t]-lc[t-672];r1008=lc[t]-lc[t-1008]
        f336=np.sum(r[t-336:t]*e[t-336:t],axis=0)
        crisis=bool(np.median(r336)<-.10 and np.median(r72)<-.03)
        bull=bool(r1008[0]>0 and r672[1]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        active=(r1008[:2]>0)
        if active.all():
            vol=np.sqrt(np.mean(np.diff(lc[t-336:t+1,:2],axis=0)**2,axis=0))
            inv=1./np.maximum(vol,.002)
            weights=np.clip(inv/inv.sum(),.30,.70)
            core[t,:2]=weights/weights.sum()
        elif active[0]:core[t,0]=1.
        elif active[1]:core[t,1]=1.
        if t>=ou:
            oa=-1
            if (t>=ol+1008 and r168[3]>.12 and r24[3]>.03
                and f336[3]<.02):
                oa=3;ol=t;ou=t+672
        if oa>=0 and t<ou:
            opp[t,3]=1.
            edge[t,1]=float(r24[3])
            carry_cost[t,1]=float(f336[3])
        if t>=pu:
            pair=False
            if (t>=pl+1008 and r1008[3]-r1008[2]>.05
                and f336[2]-f336[3]>.003):
                pair=True;pl=t;pu=t+672
        if pair and t<pu:
            rv[t,3]=.5;rv[t,2]=-.5
            edge[t,2]=float(r1008[3]-r1008[2]+f336[2]-f336[3])
            carry_cost[t,2]=float(.5*(f336[3]-f336[2]))
        if t>=hu:
            hedge=False
            if (t>=hl+1008 and np.median(r168)<-.10
                and r72[2]<-.08):
                hedge=True;hl=t;hu=t+336
        if hedge and t<hu:
            stress[t,2]=-1.
            edge[t,3]=float(-r72[2])
            carry_cost[t,3]=float(-f336[2])
    return core,opp,rv,stress,{"state":state,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=3000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                 .05*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-50:]*=1.2;rr=r.copy();rr[-50:]*=5.
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-50],y[:-50])
        assert not np.any(x[:WARMUP])
        assert np.isfinite(x).all()
    for k in ("state","edge","carry_cost"):
        assert np.array_equal(a[4][k][:-50],b[4][k][:-50])
    assert np.all(a[0].sum(axis=1)<=1.+1e-10)
    assert np.allclose(a[2].sum(axis=1),0.)
    assert not np.any(a[1][:,:2]) and not np.any(a[2][:,:2])
    assert not np.any(a[3][:,:2])
    return True
if __name__=="__main__":
    assert causal_check()
    print("BW_CAUSAL_SOURCE_PASS")
