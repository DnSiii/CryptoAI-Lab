#!/usr/bin/env python3
"""BN preregistered liquidity-anchor, acceleration, ratio-dislocation, defensive-pair signals."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008
PAIRS=((0,1),(1,3),(0,2))

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BN_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    oa=-1;ou=-1;ol=-100000
    pair=(-1,-1);pu=-1;pl=-100000
    hedge=-1;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336]
        fund=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        crisis=bool(np.count_nonzero(r168<0)>=3 and np.median(r72)<-.05)
        bull=bool(np.count_nonzero(r168>0)>=3 and r336[0]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        core[t,0]=.5;core[t,1]=.5
        if t>=ou:
            oa=-1
            if t>=ol+720 and bull:
                v72=np.std(np.diff(lc[t-72:t+1],axis=0),axis=0,ddof=1)
                v336=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0,ddof=1)
                eligible=[j for j in range(4) if
                          r24[j]>.04 and r168[j]>.10 and r24[j]>.35*r168[j]
                          and v72[j]<1.1*v336[j] and fund[j]<.015]
                if eligible:
                    oa=sorted(eligible,key=lambda j:(-round(float(r24[j]/r168[j]),12),j))[0]
                    ol=t;ou=t+240
        if oa>=0 and t<ou:
            opp[t,oa]=1.
            edge[t,1]=float(r24[oa])
            carry_cost[t,1]=float(fund[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+1008 and state[t]=="NEUTRAL":
                candidates=[]
                for a,b in PAIRS:
                    x=lc[t-504:t+1,a]-lc[t-504:t+1,b]
                    mu=float(x[:-1].mean());sd=float(x[:-1].std(ddof=1))
                    if sd<=1e-8:continue
                    z=float((x[-1]-mu)/sd)
                    z24=float((x[-25]-mu)/sd)
                    if abs(z)<=1.8 or abs(z)>=abs(z24):continue
                    lo,hi=(b,a) if z>0 else (a,b)
                    carry=float((fund[lo]-fund[hi])*.5)
                    if carry>=.005:continue
                    candidates.append((abs(z),lo,hi,carry))
                if candidates:
                    _,lo,hi,_=sorted(candidates,key=lambda x:(-round(x[0],12),x[1],x[2]))[0]
                    pair=(lo,hi);pl=t;pu=t+336
        if pair[0]>=0 and t<pu:
            rv[t,pair[0]]=.5;rv[t,pair[1]]=-.5
            edge[t,2]=float(abs((lc[t,pair[0]]-lc[t,pair[1]])-
                                (lc[t-504:t,pair[0]]-lc[t-504:t,pair[1]]).mean()))
            carry_cost[t,2]=float(rv[t]@fund)
        if t>=hu:
            hedge=-1
            if t>=hl+504 and crisis:
                candidates=[j for j in (1,2,3) if
                            r168[0]-r168[j]>.08 and r72[j]<-.08 and fund[j]>=0]
                if candidates:
                    hedge=sorted(candidates,key=lambda j:(round(float(r72[j]),12),j))[0]
                    hl=t;hu=t+144
        if hedge>=0 and t<hu:
            stress[t,0]=.5;stress[t,hedge]=-.5
            edge[t,3]=float(r168[0]-r168[hedge])
            carry_cost[t,3]=float(stress[t]@fund)
    return core,opp,rv,stress,{"state":state,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=2900;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                 .05*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    cc=c.copy();cc[-50:]*=1.2;rr=r.copy();rr[-50:]*=5
    b=source_bundle(cc,q,rr,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-50],y[:-50])
        assert not np.any(x[:WARMUP])
        assert np.isfinite(x).all()
    for k in ("state","edge","carry_cost"):
        assert np.array_equal(a[4][k][:-50],b[4][k][:-50])
    assert np.allclose(a[0][WARMUP:].sum(axis=1),1.)
    assert np.allclose(a[2].sum(axis=1),0.)
    assert np.allclose(a[3].sum(axis=1),0.)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BN_CAUSAL_SOURCE_PASS")
