#!/usr/bin/env python3
"""V98 AZ independent native funding-carry quality and volatility compression sources."""
from __future__ import annotations
import numpy as np
WARMUP=2160
EPOCH=672

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AZ_SOURCE_INPUT")
    n=len(c);lc=np.log(c);lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"CARRY",dtype="<U10")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    stress_until=-1;stress_last=-1000000;stress_seen=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        if (t-WARMUP)%EPOCH==0:
            r672=lc[t]-lc[t-672]
            ev=e[t-671:t+1]
            meanfund=np.sum(r[t-671:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
            net=r672-84.*meanfund
            downside=np.sqrt(np.mean(np.minimum(lr[t-335:t+1],0.)**2,axis=0))*np.sqrt(336.)
            score=net/(.05+downside)
            ranked=sorted((int(j) for j in range(4) if net[j]>0 and r168[j]>0),
                          key=lambda j:(-round(float(score[j]),12),j))[:2]
            cur_core[:]=0.
            if ranked:
                cur_core[ranked[0]]=.7 if len(ranked)>1 else 1.
                if len(ranked)>1:cur_core[ranked[1]]=.3
            cur_rv[:]=0.
            med=float(np.median(meanfund))
            cheap=[j for j in range(4) if r336[j]>0 and r168[j]>0
                   and net[j]>0 and meanfund[j]<=med-.00008]
            if cheap:
                long=sorted(cheap,key=lambda j:(round(float(meanfund[j]),12),j))[0]
                short=[j for j in range(4) if j!=long and r336[j]<0
                       and r168[j]<0 and meanfund[j]>=med+.00008]
                if short:
                    j=sorted(short,key=lambda j:(-round(float(meanfund[j]),12),j))[0]
                    cur_rv[long]=.5;cur_rv[j]=-.5
                else:
                    cur_rv[long]=1.
        core[t]=cur_core;rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+672:
                prev_high=np.max(c[t-168:t],axis=0)
                median_q=np.median(q[t-168:t],axis=0)
                recent_vol=np.std(lr[t-167:t+1],axis=0)
                old_vol=np.std(lr[t-335:t-167],axis=0)
                candidates=[j for j in range(4) if r24[j]>.035
                    and c[t,j]>prev_high[j]
                    and q[t,j]>1.4*max(float(median_q[j]),1e-8)
                    and recent_vol[j]<old_vol[j]]
                if candidates:
                    opp_asset=sorted(candidates,
                        key=lambda j:(-round(float(r24[j]),12),j))[0]
                    opp_last=t;opp_until=t+168
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if float(np.median(r72))<-.07:stress_seen=t
        if t>=stress_until and t>=stress_last+504 and t-stress_seen<=168:
            if float(np.median(r24))>.02 and r24[0]>0:
                stress_last=t;stress_until=t+120
        if t<stress_until:
            stress[t,0]=.5;stress[t,1]=.5
        if np.count_nonzero(r168>0)>=3 and float(np.median(r336))>0:
            states[t]="TREND"
        elif float(np.median(r168))<=-.03:
            states[t]="DEFENSE"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2750;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    changed=c.copy();changed[-40:]*=1.1
    b=source_bundle(changed,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    return True
if __name__=="__main__":
    assert causal_check()
    print("AZ_SOURCE_CAUSAL_PASS")
