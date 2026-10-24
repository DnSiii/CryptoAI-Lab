#!/usr/bin/env python3
"""BF original breadth-led long-only catch-up architecture; strictly causal 1h inputs."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=336
COOLDOWN=336

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BF_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"FLAT",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_w=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_asset=-1;rv_until=-1;rv_last=-100000
    stress_on=False;stress_until=-1;stress_last=-100000
    opp_edge=opp_carry=rv_edge=rv_carry=stress_edge=stress_carry=0.
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r504=lc[t]-lc[t-504]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        if (t-WARMUP)%EPOCH==0:
            score=.7*r504+.3*r168-3.*f168
            eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0]
            ranked=sorted(eligible,key=lambda j:(-round(float(score[j]),12),j))[:2]
            core_w[:]=0.
            if len(ranked)==1:core_w[ranked[0]]=1.
            elif len(ranked)==2:
                core_w[ranked[0]]=.75;core_w[ranked[1]]=.25
        core[t]=core_w
        breadth=int(np.count_nonzero(r168>0))
        market_stress=bool(np.count_nonzero(r72<-.09)>=3 and np.median(r24)<-.035)
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+COOLDOWN:
                eligible=[j for j in range(4) if
                    r72[j]<0 and r24[j]>.035 and r336[j]>0]
                if eligible:
                    opp_asset=sorted(eligible,
                        key=lambda j:(-round(float(r24[j]-r72[j]),12),j))[0]
                    opp_last=t;opp_until=t+96
                    opp_edge=float(r24[opp_asset]-.5*r72[opp_asset])
                    opp_carry=float(f168[opp_asset])*96./168.
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.;edge[t,1]=opp_edge;carry_cost[t,1]=opp_carry
        if t>=rv_until:
            rv_asset=-1
            if t>=rv_last+COOLDOWN and breadth>=3:
                med=float(np.median(r336))
                eligible=[j for j in range(4) if
                    r336[j]<med and r72[j]>.045 and r24[j]>.025]
                if eligible:
                    rv_asset=sorted(eligible,key=lambda j:(
                        -round(float(r72[j]-r336[j]*72./336.),12),j))[0]
                    rv_last=t;rv_until=t+168
                    rv_edge=float(r72[rv_asset]-r336[rv_asset]*72./336.)
                    rv_carry=float(f168[rv_asset])
        if rv_asset>=0 and t<rv_until:
            rv[t,rv_asset]=1.;edge[t,2]=rv_edge;carry_cost[t,2]=rv_carry
        if t>=stress_until:
            stress_on=False
            if t>=stress_last+COOLDOWN and market_stress:
                stress_on=True;stress_last=t;stress_until=t+48
                stress_edge=float(-np.median(r24)-.1*np.median(r72))
                stress_carry=float(-.5*(f168[0]+f168[1])*48./168.)
        if stress_on and t<stress_until:
            stress[t,0]=-.5;stress[t,1]=-.5
            edge[t,3]=stress_edge;carry_cost[t,3]=stress_carry
        if market_stress:states[t]="STRESS"
        elif breadth>=3:states[t]="BREADTH"
        elif float(r336.max()-r336.min())>.30:states[t]="ROTATION"
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
    assert np.all(np.sum(a[2],axis=1)<=1.+1e-10)
    assert np.all(np.abs(a[3].sum(axis=1))<=1.+1e-10)
    return True

if __name__=="__main__":
    assert causal_check()
    print("BF_CAUSAL_BREADTH_SOURCE_PASS")
