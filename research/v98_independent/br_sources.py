#!/usr/bin/env python3
"""BR original persistent carry-aware rotation source proposals, training only."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=840

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BR_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_w=np.zeros(4)
    oa=-1;ou=-1;ol=-100000
    pair=(-1,-1);pu=-1;pl=-100000
    hedge=-1;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        fund336=np.sum(r[t-336:t]*e[t-336:t],axis=0)
        fund1008=np.sum(r[t-1008:t]*e[t-1008:t],axis=0)
        hourly=np.diff(lc[t-1008:t+1],axis=0)
        sig1008=np.sqrt(np.mean(hourly*hourly,axis=0))
        sig168=np.sqrt(np.mean(hourly[-168:]*hourly[-168:],axis=0))
        sig336=np.sqrt(np.mean(hourly[-336:]*hourly[-336:],axis=0))
        crisis=bool(np.median(r72)<-.055 and
                    np.median(sig168)>1.25*np.median(sig1008))
        bull=bool(np.count_nonzero(r336>0)>=3 and r1008[0]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            score=r1008-2.*fund1008-.4*sig336*np.sqrt(1008.)
            eligible=[j for j in range(4) if score[j]>.05 and r336[j]>-.02]
            ranked=sorted(eligible,key=lambda j:(-round(float(score[j]),12),j))[:2]
            core_w=np.zeros(4)
            if len(ranked)==1:core_w[ranked[0]]=1.
            elif len(ranked)==2:
                core_w[ranked[0]]=.65;core_w[ranked[1]]=.35
        core[t]=core_w
        if t>=ou:
            oa=-1
            if t>=ol+840 and state[t]!="CRISIS":
                candidates=[j for j in range(4) if
                    r168[j]-np.median(r168)>.08 and
                    r72[j]>.025 and r336[j]>.08 and fund336[j]<.025]
                if candidates:
                    oa=sorted(candidates,key=lambda j:
                        (-round(float(r168[j]-np.median(r168)-2.*fund336[j]),12),j))[0]
                    ol=t;ou=t+504
        if oa>=0 and t<ou:
            opp[t,oa]=1.
            edge[t,1]=float(r168[oa]-np.median(r168))
            carry_cost[t,1]=float(fund336[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+840 and state[t]!="CRISIS":
                candidates=[]
                for a in range(4):
                    for b in range(4):
                        if a==b:continue
                        carry=float(fund336[a]-fund336[b])
                        spread=float(r336[a]-r336[b])
                        if carry<-.0025 and spread>-.03:
                            candidates.append((-carry+spread,a,b))
                if candidates:
                    _,a,b=sorted(candidates,key=lambda x:
                        (-round(float(x[0]),12),x[1],x[2]))[0]
                    pair=(a,b);pl=t;pu=t+672
        if pair[0]>=0 and t<pu:
            a,b=pair;rv[t,a]=.5;rv[t,b]=-.5
            edge[t,2]=float(fund336[b]-fund336[a])
            carry_cost[t,2]=float(.5*(fund336[a]-fund336[b]))
        if t>=hu:
            hedge=-1
            if t>=hl+672 and crisis and r72[0]<-.05:
                hedge=0;hl=t;hu=t+336
        if hedge>=0 and t<hu:
            stress[t,0]=-1.
            edge[t,3]=float(-r72[0])
            carry_cost[t,3]=float(-fund336[0])
    return core,opp,rv,stress,{"state":state,"edge":edge,"carry_cost":carry_cost}

def causal_check():
    n=2900;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]])+
                 .05*np.sin(t[:,None]/48.+np.arange(4)))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
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
    return True
if __name__=="__main__":
    assert causal_check()
    print("BR_CAUSAL_SOURCE_PASS")
