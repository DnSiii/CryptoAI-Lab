#!/usr/bin/env python3
"""BT independent always-invested risk-parity growth with residual event sleeves."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BT_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    cw=np.zeros(4)
    oa=-1;ou=-1;ol=-100000
    pair=(-1,-1);pu=-1;pl=-100000
    recover=-1;hu=-1;hl=-100000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        funding336=np.sum(r[t-336:t]*e[t-336:t],axis=0)
        hourly=np.diff(lc[t-1008:t+1],axis=0)
        sig1008=np.sqrt(np.mean(hourly*hourly,axis=0))
        sig168=np.sqrt(np.mean(hourly[-168:]*hourly[-168:],axis=0))
        sig336=np.sqrt(np.mean(hourly[-336:]*hourly[-336:],axis=0))
        crisis=bool(np.median(r168)<-.08 and
                    np.median(sig168)>1.3*np.median(sig1008))
        bull=bool(r1008[0]>0 and np.count_nonzero(r336>0)>=3)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            inv=1./np.maximum(sig336,.002)
            cw=np.clip(inv/inv.sum(),.10,.40)
            cw/=cw.sum()
        core[t]=cw
        if t>=ou:
            oa=-1
            if t>=ol+1008 and state[t]!="CRISIS":
                b=hourly[:,0]-hourly[:,0].mean()
                denom=float(b@b)
                candidates=[]
                if denom>1e-10:
                    for j in (1,2,3):
                        y=hourly[:,j]-hourly[:,j].mean()
                        beta=float(y@b/denom)
                        residual=float(r72[j]-beta*r72[0])
                        if residual>.06 and r336[j]>0 and funding336[j]<.02:
                            candidates.append((residual,j))
                if candidates:
                    _,oa=sorted(candidates,key=lambda x:(-round(x[0],12),x[1]))[0]
                    ol=t;ou=t+504
        if oa>=0 and t<ou:
            opp[t,oa]=1.
            b=hourly[:,0]-hourly[:,0].mean()
            denom=float(b@b)
            y=hourly[:,oa]-hourly[:,oa].mean()
            beta=float(y@b/denom) if denom>1e-10 else 0.
            edge[t,1]=float(r72[oa]-beta*r72[0])
            carry_cost[t,1]=float(funding336[oa])
        if t>=pu:
            pair=(-1,-1)
            if t>=pl+1008 and state[t]!="CRISIS":
                candidates=[]
                for a in range(4):
                    for b in range(4):
                        if a==b:continue
                        ratio=float(sig336[b]/max(sig336[a],1e-8))
                        spread=float(r168[a]-r168[b])
                        carry=float(funding336[a]-funding336[b])
                        if ratio>1.5 and spread>.03 and carry<.01:
                            candidates.append((spread,a,b))
                if candidates:
                    _,a,b=sorted(candidates,key=lambda x:
                        (-round(float(x[0]),12),x[1],x[2]))[0]
                    pair=(a,b);pl=t;pu=t+840
        if pair[0]>=0 and t<pu:
            a,b=pair;rv[t,a]=.5;rv[t,b]=-.5
            edge[t,2]=float(r168[a]-r168[b])
            carry_cost[t,2]=float(.5*(funding336[a]-funding336[b]))
        if t>=hu:
            recover=-1
            if t>=hl+1008 and crisis and np.median(r24)>.02:
                recover=1;hl=t;hu=t+672
        if recover>=0 and t<hu:
            stress[t,1:]=1./3.
            edge[t,3]=float(-np.median(r168))
            carry_cost[t,3]=float(np.mean(funding336[1:]))
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
    print("BT_CAUSAL_SOURCE_PASS")
