#!/usr/bin/env python3
"""BG persistent equal-weight market beta + sparse breakout/carry/cash hedge, causal."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=2160
COOLDOWN=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BG_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_asset=-1;rv_until=-1;rv_last=-100000
    stress_on=False;stress_until=-1;stress_last=-100000
    opp_edge=opp_carry=rv_edge=rv_carry=stress_edge=stress_carry=0.
    for t in range(WARMUP,n):
        core[t]=.25
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(r72<-.10)>=3 and np.median(r24)<-.05)
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+COOLDOWN:
                med_q=np.median(q[t-168:t],axis=0)
                eligible=[j for j in range(4) if
                    c[t,j]>np.max(c[t-168:t,j]) and r72[j]>.08
                    and q[t,j]>1.5*max(float(med_q[j]),1e-8)]
                if eligible:
                    opp_asset=sorted(eligible,key=lambda j:(
                        -round(float(r72[j]),12),j))[0]
                    opp_last=t;opp_until=t+168
                    opp_edge=float(r72[opp_asset])
                    opp_carry=float(f168[opp_asset])
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.;edge[t,1]=opp_edge;carry_cost[t,1]=opp_carry
        if t>=rv_until:
            rv_asset=-1
            if t>=rv_last+COOLDOWN:
                eligible=[j for j in range(4) if
                    f168[j]<-.002 and r168[j]>.05]
                if eligible:
                    rv_asset=sorted(eligible,key=lambda j:(
                        round(float(f168[j]),12),j))[0]
                    rv_last=t;rv_until=t+336
                    rv_edge=float(.5*r168[rv_asset]-2.*f168[rv_asset])
                    rv_carry=float(2.*f168[rv_asset])
        if rv_asset>=0 and t<rv_until:
            rv[t,rv_asset]=1.;edge[t,2]=rv_edge;carry_cost[t,2]=rv_carry
        if t>=stress_until:
            stress_on=False
            if t>=stress_last+COOLDOWN and crisis:
                stress_on=True;stress_last=t;stress_until=t+72
                stress_edge=float(-.3*np.median(r72))
                stress_carry=float(-.25*np.sum(f168)*72./168.)
        if stress_on and t<stress_until:
            stress[t]=-.25
            edge[t,3]=stress_edge;carry_cost[t,3]=stress_carry
        if crisis:states[t]="CRISIS"
        elif np.count_nonzero(r168>0)>=3:states[t]="BULL"
    return core,opp,rv,stress,{"state":states,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=2800;t=np.arange(n,dtype=float)
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
    assert np.all(np.abs(a[3].sum(axis=1))<=1.+1e-10)
    return True

if __name__=="__main__":
    assert causal_check()
    print("BG_CAUSAL_PERSISTENT_BASKET_PASS")
