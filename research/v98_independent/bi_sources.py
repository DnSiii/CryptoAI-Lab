#!/usr/bin/env python3
"""V98 BI independent BTC liquidity anchor, alt-season, convergence and recovery."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008
HOLD=336
COOLDOWN=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BI_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_pair=(-1,-1);rv_until=-1;rv_last=-100000
    recovery_on=False;recovery_until=-1;recovery_last=-100000
    opp_edge=opp_carry=rv_edge=rv_carry=recovery_edge=recovery_carry=0.
    for t in range(WARMUP,n):
        core[t,0]=1.
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r672=lc[t]-lc[t-672]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(r72[0]<-.08 and np.count_nonzero(r72<0)>=3)
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+COOLDOWN and r336[0]>0 and np.count_nonzero(r672[1:]>0)>=2:
                eligible=[j for j in (1,2,3) if
                    r672[j]-r672[0]>.08 and r168[j]>0]
                if eligible:
                    opp_asset=sorted(eligible,key=lambda j:(-round(float(r672[j]),12),j))[0]
                    opp_last=t;opp_until=t+HOLD
                    opp_edge=float(.5*(r672[opp_asset]-r672[0])+.5*r168[opp_asset])
                    opp_carry=float(2.*f168[opp_asset])
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.;edge[t,1]=opp_edge;carry_cost[t,1]=opp_carry
        if t>=rv_until:
            rv_pair=(-1,-1)
            if t>=rv_last+COOLDOWN:
                long=int(np.argmin(r336));short=int(np.argmax(r336))
                disp336=float(r336[short]-r336[long])
                disp72=float(np.max(r72)-np.min(r72))
                spread=float(f168[short]-f168[long])
                if long!=short and disp336>.20 and disp72<disp336-.05 and spread>.002:
                    rv_pair=(long,short);rv_last=t;rv_until=t+HOLD
                    rv_edge=float(.5*(disp336-disp72)+spread)
                    rv_carry=float(f168[long]-f168[short])
        if rv_pair[0]>=0 and t<rv_until:
            rv[t,rv_pair[0]]=.5;rv[t,rv_pair[1]]=-.5
            edge[t,2]=rv_edge;carry_cost[t,2]=rv_carry
        if t>=recovery_until:
            recovery_on=False
            recovery=bool(np.count_nonzero(r168<-.08)>=3 and
                          np.count_nonzero(r72>.025)>=3 and np.median(r24)>0)
            if t>=recovery_last+COOLDOWN and recovery:
                recovery_on=True;recovery_last=t;recovery_until=t+HOLD
                recovery_edge=float(.5*np.median(r72)+.1*abs(np.median(r168)))
                recovery_carry=float(2.*np.mean(f168))
        if recovery_on and t<recovery_until:
            stress[t]=.25;edge[t,3]=recovery_edge;carry_cost[t,3]=recovery_carry
        if crisis:states[t]="CRISIS"
        elif r336[0]>0 and np.count_nonzero(r168>0)>=3:states[t]="BULL"
    return core,opp,rv,stress,{"state":states,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=2900;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                  .05*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-50:]*=1.2
    rr=r.copy();rr[-50:]*=5.
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-50],y[:-50])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    for k in ("state","edge","carry_cost"):
        assert np.array_equal(a[4][k][:-50],b[4][k][:-50])
    assert np.all(np.sum(a[0],axis=1)<=1.+1e-10)
    assert np.all(np.abs(a[2].sum(axis=1))<1e-10)
    assert np.all(np.sum(a[3],axis=1)<=1.+1e-10)
    return True

if __name__=="__main__":
    assert causal_check()
    print("BI_CAUSAL_ANCHOR_CONVERGENCE_RECOVERY_PASS")
