#!/usr/bin/env python3
"""V98 AX independent causal downside-quality core and beta-residual growth."""
from __future__ import annotations
import numpy as np
WARMUP=2160
CORE_EPOCH=672
RV_EPOCH=336

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AX_SOURCE_INPUT")
    n=len(c);lc=np.log(c);lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"TRANSITION",dtype="<U10")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    stress_until=-1;stress_last=-1000000;stress_seen=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r96=lc[t]-lc[t-96]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r672=lc[t]-lc[t-672]
        if (t-WARMUP)%CORE_EPOCH==0:
            past=lr[t-671:t+1]
            downside=np.sqrt(np.mean(np.minimum(past,0.)**2,axis=0))*np.sqrt(672.)
            ev=e[t-671:t+1]
            mf=np.sum(r[t-671:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            net=r672-84.*mf
            score=net/np.maximum(downside,.05)
            ranked=sorted((int(j) for j in range(4)
                           if net[j]>0 and r168[j]>0),
                          key=lambda j:(-round(float(score[j]),12),j))
            cur_core[:]=0.
            if ranked:
                cur_core[ranked[0]]=.65 if len(ranked)>1 else 1.
                if len(ranked)>1:cur_core[ranked[1]]=.35
        if (t-WARMUP)%RV_EPOCH==0:
            past=lr[t-671:t+1]
            b=past[:,0];var=float(np.mean((b-b.mean())**2))
            beta=np.array([float(np.mean((past[:,j]-past[:,j].mean())*(b-b.mean()))/
                            max(var,1e-12)) for j in range(4)])
            residual=r336-beta*r336[0]
            ev=e[t-671:t+1]
            mf=np.sum(r[t-671:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            candidates=[j for j in (1,2,3) if residual[j]>.05
                        and r168[j]>0 and mf[j]<=float(np.median(mf))+.00015]
            cur_rv[:]=0.
            if candidates:
                j=sorted(candidates,key=lambda j:(-round(float(residual[j]),12),j))[0]
                cur_rv[j]=1.
        core[t]=cur_core;rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+336:
                med=np.median(q[t-168:t],axis=0)
                accel=r24-.375*r96
                candidates=[int(j) for j in range(4)
                            if r24[j]>.04 and accel[j]>0
                            and q[t,j]>1.5*max(float(med[j]),1e-8)]
                if candidates:
                    opp_asset=sorted(candidates,key=lambda j:(-round(float(accel[j]),12),j))[0]
                    opp_last=t;opp_until=t+144
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if r168[0]<-.10:stress_seen=t
        if t>=stress_until:
            if (t>=stress_last+504 and t-stress_seen<=168
                and r24[0]>.025 and float(np.median(r24))>0):
                stress_last=t;stress_until=t+144
        if t<stress_until:
            stress[t,0]=.5;stress[t,3]=.5
        if float(np.median(r672))>0 and np.count_nonzero(r168>0)>=3:
            states[t]="TREND"
        elif float(np.median(r168))<0 and r168[0]<0:
            states[t]="STRESS"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2600;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    d=c.copy();d[-40:]*=1.1
    b=source_bundle(d,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    return True
if __name__=="__main__":
    assert causal_check()
    print("AX_SOURCE_CAUSAL_PASS")
