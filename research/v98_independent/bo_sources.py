#!/usr/bin/env python3
"""BO preregistered carry-confirmed trend, pullback opportunity, relative momentum carry, crash short."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BO_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_w=np.zeros(4)
    oa=-1;ou=-1;ol=-100000
    pair=(-1,-1);pu=-1;pl=-100000
    hedge=-1;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336];r504=lc[t]-lc[t-504]
        fund168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
        fund504=np.sum(r[t-504:t]*e[t-504:t],axis=0)
        crisis=bool(np.count_nonzero(r168<0)>=3 and np.median(r72)<-.06)
        bull=bool(np.count_nonzero(r336>0)>=3 and r504[0]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            # 42-day momentum discounted for actual trailing signed native funding.
            scores=r504-2.*fund504
            eligible=[j for j in range(4) if r504[j]>.08 and r168[j]>0 and scores[j]>.06]
            leaders=sorted(eligible,key=lambda j:(-round(float(scores[j]),12),j))[:2]
            core_w=np.zeros(4)
            if leaders:core_w[leaders]=1./len(leaders)
        core[t]=core_w
        if t>=ou:
            oa=-1
            if t>=ol+1008 and bull:
                eligible=[j for j in range(4) if r504[j]>.25 and
                    -.08<r72[j]<-.015 and r24[j]>.012 and fund168[j]<.01]
                if eligible:
                    oa=sorted(eligible,key=lambda j:
                        (-round(float(r504[j]-2*fund504[j]),12),j))[0]
                    ol=t;ou=t+504
        if oa>=0 and t<ou:
            opp[t,oa]=1.
            edge[t,1]=float(r504[oa]-2.*fund504[oa])
            carry_cost[t,1]=float(fund168[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+1344 and state[t]!="CRISIS":
                candidates=[]
                for a in range(4):
                    for b in range(4):
                        if a==b:continue
                        spread=float(r336[a]-r336[b])
                        carry=float(fund168[a]-fund168[b])
                        if (spread>.25 and r72[a]-r72[b]>.025
                            and carry<-.01 and r168[a]>0):
                            candidates.append((spread-2.*carry,a,b))
                if candidates:
                    _,a,b=sorted(candidates,key=lambda x:(-round(x[0],12),x[1],x[2]))[0]
                    pair=(a,b);pl=t;pu=t+672
        if pair[0]>=0 and t<pu:
            a,b=pair;rv[t,a]=.5;rv[t,b]=-.5
            edge[t,2]=float(r336[a]-r336[b])
            carry_cost[t,2]=float(rv[t]@fund168)
        if t>=hu:
            hedge=-1
            if t>=hl+672 and crisis:
                candidates=[j for j in (1,2,3) if
                    r168[j]<-.2 and r24[j]<-.04 and fund168[j]>=0]
                if candidates:
                    hedge=sorted(candidates,key=lambda j:(round(float(r168[j]),12),j))[0]
                    hl=t;hu=t+168
        if hedge>=0 and t<hu:
            stress[t,hedge]=-1.
            edge[t,3]=float(-r168[hedge])
            carry_cost[t,3]=float(-fund168[hedge])
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
    assert np.all(np.sum(np.abs(a[3]),axis=1)<=1.+1e-10)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BO_CAUSAL_SOURCE_PASS")
