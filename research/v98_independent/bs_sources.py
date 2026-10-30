#!/usr/bin/env python3
"""BS synchronous 1008-hour carry-aware seven-slot signal system; no future data."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=1008

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BS_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    state=np.full(n,"NEUTRAL",dtype="<U12")
    edge=np.zeros((n,4));carry_cost=np.zeros((n,4))
    cw=np.zeros(4);ow=np.zeros(4);rw=np.zeros(4);sw=np.zeros(4)
    ew=np.zeros(4);fw=np.zeros(4)
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r1008=lc[t]-lc[t-1008]
        hourly=np.diff(lc[t-1008:t+1],axis=0)
        sig1008=np.sqrt(np.mean(hourly*hourly,axis=0))
        sig168=np.sqrt(np.mean(hourly[-168:]*hourly[-168:],axis=0))
        crisis=bool(np.median(r168)<-.08 and
                    np.median(sig168)>1.2*np.median(sig1008))
        bull=bool(np.count_nonzero(r336>0)>=3 and r1008[0]>0)
        if crisis:state[t]="CRISIS"
        elif bull:state[t]="BULL"
        if (t-WARMUP)%EPOCH==0:
            f168=np.sum(r[t-168:t]*e[t-168:t],axis=0)
            f1008=np.sum(r[t-1008:t]*e[t-1008:t],axis=0)
            sig336=np.sqrt(np.mean(hourly[-336:]*hourly[-336:],axis=0))
            cw=np.zeros(4);ow=np.zeros(4);rw=np.zeros(4);sw=np.zeros(4)
            ew=np.zeros(4);fw=np.zeros(4)
            core_score=r1008-2.*f1008-.5*sig336*np.sqrt(1008.)
            eligible=[j for j in range(4) if r1008[j]>.10 and r336[j]>0]
            top=sorted(eligible,key=lambda j:(-round(float(core_score[j]),12),j))[:2]
            if len(top)==1:cw[top[0]]=1.
            elif len(top)==2:
                cw[top[0]]=.70;cw[top[1]]=.30
            accel=r168-(168./1008.)*r1008
            eligible=[j for j in range(4) if r168[j]>.04 and
                      r1008[j]>.08 and accel[j]>.03 and f168[j]<.015]
            if eligible:
                j=sorted(eligible,key=lambda k:
                    (-round(float(accel[k]-2.*f168[k]),12),k))[0]
                ow[j]=1.;ew[1]=float(accel[j]);fw[1]=float(f168[j])
            pairs=[]
            for a in range(4):
                for b in range(4):
                    if a==b:continue
                    spread=float(r1008[a]-r1008[b])
                    short_trend=float(r168[a]-r168[b])
                    carry=float(f1008[a]-f1008[b])
                    if spread>.20 and short_trend>.02 and carry<.01:
                        pairs.append((spread-2.*carry,a,b))
            if pairs:
                score,a,b=sorted(pairs,key=lambda x:
                    (-round(float(x[0]),12),x[1],x[2]))[0]
                rw[a]=.5;rw[b]=-.5
                ew[2]=float(score);fw[2]=float(.5*(f1008[a]-f1008[b]))
            if np.median(r168)<-.05 and r1008[0]>0 and r24[0]>0:
                sw[0]=.5;sw[1]=.5
                ew[3]=float(-np.median(r168))
                fw[3]=float(.5*(f168[0]+f168[1]))
        core[t]=cw;opp[t]=ow;rv[t]=rw;stress[t]=sw
        edge[t]=ew;carry_cost[t]=fw
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
    print("BS_CAUSAL_SOURCE_PASS")
