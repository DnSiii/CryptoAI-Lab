#!/usr/bin/env python3
"""V98 BJ independent cooperative source and causal net-shadow evidence."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BJ_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    shadow_gain=np.zeros((n,4))
    core_weights=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-100000
    rv_pair=(-1,-1);rv_until=-1;rv_last=-100000
    stress_on=False;stress_until=-1;stress_last=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(r168<0)>=3 and np.median(r72)<-.05)
        if (t-WARMUP)%EPOCH==0:
            vol=np.std(np.diff(lc[t-672:t+1],axis=0),axis=0,ddof=1)
            inv=1./np.maximum(vol,1e-5)
            core_weights=inv/inv.sum()
        core[t]=core_weights
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+672 and np.count_nonzero(r168>0)>=3:
                eligible=[j for j in range(4) if r72[j]>.04]
                if eligible:
                    opp_asset=sorted(eligible,key=lambda j:(-round(float(r168[j]),12),j))[0]
                    opp_last=t;opp_until=t+336
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if t>=rv_until:
            rv_pair=(-1,-1)
            if t>=rv_last+672:
                eligible=[]
                for long in range(4):
                    for short in range(4):
                        if long==short:continue
                        spread=float(f168[short]-f168[long])
                        if spread>.004 and r168[long]>r168[short]:
                            eligible.append((spread,long,short))
                if eligible:
                    _,long,short=sorted(eligible,key=lambda z:(-round(z[0],12),z[1],z[2]))[0]
                    rv_pair=(long,short);rv_last=t;rv_until=t+336
        if rv_pair[0]>=0 and t<rv_until:
            rv[t,rv_pair[0]]=.5;rv[t,rv_pair[1]]=-.5
        if t>=stress_until:
            stress_on=False
            if t>=stress_last+336 and crisis:
                stress_on=True;stress_last=t;stress_until=t+168
        if stress_on and t<stress_until:stress[t]=-.25
        if crisis:states[t]="CRISIS"
        elif np.count_nonzero(r168>0)>=3 and np.median(r336)>0:states[t]="BULL"
        # Online shadow is strictly a trailing causal proxy, NOT realized system PnL.
        # At t the previous completed sleeve signal is exposed to t-1->t returns,
        # with native t funding and severe one-way friction on its previous change.
        for i,s in enumerate((opp,rv,stress),start=1):
            prev=s[t-1];prevprev=s[t-2]
            shadow_gain[t,i]=float(prev@(lc[t]-lc[t-1])
                -prev@(r[t]*e[t])
                -.005*np.sum(np.abs(prev-prevprev)))
            if np.any(s[t]):
                edge[t,i]=float(np.sum(shadow_gain[max(WARMUP,t-671):t+1,i]))
                carry_cost[t,i]=float(np.maximum(0.,s[t]@f168))
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
    print("BJ_CAUSAL_ONLINE_SHADOW_SOURCE_PASS")
