#!/usr/bin/env python3
"""BP independent predeclared slow net-carry growth plus breakout, spread and capitulation rebound."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=720

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BP_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c);rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    core_w=np.zeros(4)
    oa=-1;ou=-1;ol=-100000
    pair=(-1,-1);pu=-1;pl=-100000
    recovery=-1;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24];r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168];r336=lc[t]-lc[t-336]
        r504=lc[t]-lc[t-504];r840=lc[t]-lc[t-840]
        fund336=np.sum(r[t-336:t]*e[t-336:t],axis=0)
        fund840=np.sum(r[t-840:t]*e[t-840:t],axis=0)
        hourly=np.diff(lc[t-336:t+1],axis=0)
        sigma=np.sqrt(np.mean(hourly*hourly,axis=0))
        crisis=bool(np.median(r168)<-.10 and np.count_nonzero(r168<0)>=3)
        bull=bool(np.count_nonzero(r336>0)>=3 and r504[0]>.04)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            # Volatility-aware net-of-native-funding long-run growth ranking.
            score=r840-3.*fund840-.8*sigma*np.sqrt(840.)
            eligible=[j for j in range(4) if r840[j]>.10 and
                      r336[j]>.04 and score[j]>.10]
            ranked=sorted(eligible,key=lambda j:(-round(float(score[j]),12),j))[:2]
            core_w=np.zeros(4)
            if len(ranked)==1:core_w[ranked[0]]=1.
            elif len(ranked)==2:
                core_w[ranked[0]]=.65;core_w[ranked[1]]=.35
        core[t]=core_w
        if t>=ou:
            oa=-1
            if t>=ol+672 and state[t]=="BULL":
                eligible=[j for j in range(4) if
                    c[t,j]>1.015*np.max(c[t-336:t,j]) and
                    r336[j]>.16 and r72[j]>.04 and fund336[j]<.02]
                if eligible:
                    oa=sorted(eligible,key=lambda j:
                        (-round(float(r168[j]-2.*fund336[j]),12),j))[0]
                    ol=t;ou=t+336
        if oa>=0 and t<ou:
            opp[t,oa]=1.
            edge[t,1]=float(max(0.,r168[oa]-.8*sigma[oa]*np.sqrt(336.)))
            carry_cost[t,1]=float(fund336[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+1008 and state[t]!="CRISIS":
                candidates=[]
                for a in range(4):
                    for b in range(4):
                        if a==b:continue
                        spread=float(r504[a]-r504[b])
                        carry=float(fund336[a]-fund336[b])
                        if (spread>.22 and r168[a]-r168[b]>.06
                            and r168[a]>0 and r168[b]<0 and carry<.005):
                            risk=.5*(sigma[a]+sigma[b])*np.sqrt(504.)
                            candidates.append((spread-2.*carry-risk,a,b))
                if candidates:
                    _,a,b=sorted(candidates,key=lambda x:(-round(x[0],12),x[1],x[2]))[0]
                    pair=(a,b);pl=t;pu=t+504
        if pair[0]>=0 and t<pu:
            a,b=pair;rv[t,a]=.5;rv[t,b]=-.5
            edge[t,2]=float(max(0.,r168[a]-r168[b]-
                               .5*(sigma[a]+sigma[b])*np.sqrt(504.)))
            carry_cost[t,2]=float(rv[t]@fund336)
        if t>=hu:
            recovery=-1
            if t>=hl+1008 and crisis and np.median(r24)>.025:
                # Recovery is LONG lower-volatility major, not BO's crash short.
                eligible=[j for j in (0,1) if r24[j]>.02 and fund336[j]<.02]
                if eligible:
                    recovery=sorted(eligible,key=lambda j:
                        (round(float(sigma[j]),12),j))[0]
                    hl=t;hu=t+336
        if recovery>=0 and t<hu:
            stress[t,recovery]=1.
            edge[t,3]=float(max(0.,r72[recovery]-
                               .6*sigma[recovery]*np.sqrt(336.)))
            carry_cost[t,3]=float(fund336[recovery])
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
    print("BP_CAUSAL_SOURCE_PASS")
