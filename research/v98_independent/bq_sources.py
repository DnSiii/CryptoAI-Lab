#!/usr/bin/env python3
"""BQ prequential shadow-expert signal proposals: inverse-vol growth, compression, reversion, crash hedge."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BQ_SOURCE_INPUT")
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
        r336=lc[t]-lc[t-336];r1008=lc[t]-lc[t-1008]
        funding336=np.sum(r[t-336:t]*e[t-336:t],axis=0)
        funding1008=np.sum(r[t-1008:t]*e[t-1008:t],axis=0)
        d1008=np.diff(lc[t-1008:t+1],axis=0)
        sigma1008=np.sqrt(np.mean(d1008*d1008,axis=0))
        sigma168=np.sqrt(np.mean(d1008[-168:]*d1008[-168:],axis=0))
        sigma336=np.sqrt(np.mean(d1008[-336:]*d1008[-336:],axis=0))
        crisis=bool(np.median(r72)<-.07 and
                    np.median(sigma168)>1.5*np.median(sigma1008))
        bull=bool(np.count_nonzero(r336>0)>=3 and r1008[0]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            eligible=[j for j in range(4) if r1008[j]>.10 and r336[j]>0
                      and r1008[j]-2.*funding1008[j]>.08]
            core_w=np.zeros(4)
            if eligible:
                inv=np.array([1./max(float(sigma336[j]),.002) for j in eligible])
                inv/=inv.sum()
                core_w[eligible]=inv
        core[t]=core_w
        if t>=ou:
            oa=-1
            if t>=ol+672 and state[t]!="CRISIS":
                candidates=[j for j in range(4) if
                    sigma168[j]<.75*sigma1008[j] and
                    r24[j]>.03 and r336[j]>.12 and
                    c[t,j]>1.01*np.max(c[t-168:t,j]) and funding336[j]<.02]
                if candidates:
                    oa=sorted(candidates,key=lambda j:
                        (-round(float(r24[j]-funding336[j]),12),j))[0]
                    ol=t;ou=t+336
        if oa>=0 and t<ou:
            opp[t,oa]=1.;edge[t,1]=float(r24[oa])
            carry_cost[t,1]=float(funding336[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+672 and state[t]!="CRISIS":
                candidates=[]
                for a in range(4):
                    for b in range(4):
                        if a==b:continue
                        # a = 336h laggard, b = 336h leader; 24h reversal.
                        if (r336[b]-r336[a]>.25 and r24[a]-r24[b]>.02
                            and funding336[a]-funding336[b]<.01):
                            candidates.append((r24[a]-r24[b],a,b))
                if candidates:
                    _,a,b=sorted(candidates,key=lambda x:(-round(float(x[0]),12),x[1],x[2]))[0]
                    pair=(a,b);pl=t;pu=t+168
        if pair[0]>=0 and t<pu:
            a,b=pair;rv[t,a]=.5;rv[t,b]=-.5
            edge[t,2]=float(r24[a]-r24[b])
            carry_cost[t,2]=float(rv[t]@funding336)
        if t>=hu:
            hedge=-1
            if t>=hl+504 and crisis and np.any(core_w):
                hedge=0;hl=t;hu=t+168
        if hedge>=0 and t<hu:
            stress[t,0]=-1.
            edge[t,3]=float(-r72[0])
            carry_cost[t,3]=float(-funding336[0])
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
    print("BQ_CAUSAL_SOURCE_PASS")
