#!/usr/bin/env python3
"""V98 BH independent seven-slot signal sources; only completed t information."""
from __future__ import annotations
import numpy as np

WARMUP=2160
EPOCH=1008
OPP_HOLD=168
RV_HOLD=336
STRESS_HOLD=168

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BH_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_weights=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_pair=(-1,-1);rv_until=-1;rv_last=-100000
    stress_on=False;stress_until=-1;stress_last=-100000
    opp_edge=opp_carry=rv_edge=rv_carry=stress_edge=stress_carry=0.
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r672=lc[t]-lc[t-672]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(r72<-.04)>=3 and np.median(r168)<-.08)
        if (t-WARMUP)%EPOCH==0:
            vol=np.std(np.diff(lc[t-672:t+1],axis=0),axis=0,ddof=1)
            score=r672/np.maximum(vol*np.sqrt(672.),.01)
            eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0]
            ranked=sorted(eligible,key=lambda j:(-round(float(score[j]),12),j))[:2]
            core_weights[:]=0.
            if ranked:
                inv=1./np.maximum(vol[ranked],1e-5)
                inv=inv/inv.sum()
                for j,w in zip(ranked,inv):core_weights[j]=float(w)
        core[t]=core_weights
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+504:
                med=np.median(q[t-336:t],axis=0)
                eligible=[j for j in range(4) if
                    c[t,j]>np.max(c[t-336:t,j]) and r168[j]>.04
                    and q[t,j]>1.25*max(float(med[j]),1e-8)]
                if eligible:
                    opp_asset=sorted(eligible,key=lambda j:(-round(float(r168[j]),12),j))[0]
                    opp_last=t;opp_until=t+OPP_HOLD
                    opp_edge=float(r168[opp_asset])
                    opp_carry=float(f168[opp_asset])
        if opp_asset>=0 and t<opp_until:
            opp[t,opp_asset]=1.;edge[t,1]=opp_edge;carry_cost[t,1]=opp_carry
        if t>=rv_until:
            rv_pair=(-1,-1)
            if t>=rv_last+1008:
                eligible=[]
                for long in range(4):
                    for short in range(4):
                        if long==short:continue
                        gap=float(r336[long]-r336[short])
                        spread=float(f168[short]-f168[long])
                        if gap>.15 and spread>.004:
                            eligible.append((spread+.25*gap,long,short))
                if eligible:
                    _,long,short=sorted(eligible,key=lambda z:(-round(z[0],12),z[1],z[2]))[0]
                    rv_pair=(long,short);rv_last=t;rv_until=t+RV_HOLD
                    rv_edge=float(.4*(r336[long]-r336[short])+f168[short]-f168[long])
                    rv_carry=float(f168[long]-f168[short])
        if rv_pair[0]>=0 and t<rv_until:
            rv[t,rv_pair[0]]=.5;rv[t,rv_pair[1]]=-.5
            edge[t,2]=rv_edge;carry_cost[t,2]=rv_carry
        if t>=stress_until:
            stress_on=False
            if t>=stress_last+504 and crisis:
                stress_on=True;stress_last=t;stress_until=t+STRESS_HOLD
                stress_edge=float(-.5*np.median(r168))
                stress_carry=float(-.25*np.sum(f168))
        if stress_on and t<stress_until:
            stress[t]=-.25;edge[t,3]=stress_edge;carry_cost[t,3]=stress_carry
        if crisis:states[t]="CRISIS"
        elif np.count_nonzero(r168>0)>=3 and np.median(r336)>0:states[t]="BULL"
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
    assert np.all(np.abs(a[3].sum(axis=1))<=1.+1e-10)
    return True

if __name__=="__main__":
    assert causal_check()
    print("BH_CAUSAL_SEVEN_SLOT_SOURCE_PASS")
