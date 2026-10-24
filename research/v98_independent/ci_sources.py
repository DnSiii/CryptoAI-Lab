#!/usr/bin/env python3
"""CI preregistered stateful channel/dispersion/tail seven-slot source; TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.65,.55,.30,.15]),
 "MIXED":np.array([1.30,.45,.35,.35]),
 "RISK_OFF":np.array([.55,.20,.40,.65]),
}
def bundle(close,rate,event):
    c=np.asarray(close,dtype=float);r=np.asarray(rate,dtype=float);e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CI_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    active=np.zeros(4,dtype=bool)
    for t in range(WARMUP,n,GRID):
        hourly=np.diff(lc[t-672:t+1],axis=0)
        v168=float(np.std(hourly[-168:,0],ddof=1))
        v672=float(np.std(hourly[:,0],ddof=1))
        vr=v168/max(v672,1e-8)
        regime="RISK_OFF" if vr>=1.30 else "RISK_ON" if vr<=.85 else "MIXED"
        regimes[t]=regime
        above=c[t]>np.max(c[t-672:t],axis=0)
        mean168=np.mean(c[t-167:t+1],axis=0)
        active[above]=True
        active[c[t]<mean168]=False
        eligible=[j for j in range(4) if active[j]]
        ranked=sorted(eligible,key=lambda j:(-(c[t,j]/mean168[j]-1.),j))
        if len(ranked)==1:
            signals[t,0,ranked[0]]=1.
        elif len(ranked)>=2:
            signals[t,0,ranked[0]]=.60
            signals[t,0,ranked[1]]=.40
        updates[t,0]=True
        r48=lc[t]-lc[t-48]
        vol48=np.std(hourly[-48:],axis=0,ddof=1)
        vol336=np.std(hourly[-336:],axis=0,ddof=1)
        eligible=[j for j in (2,3) if r48[j]>0]
        if eligible:
            ranked=sorted(eligible,key=lambda j:(vol48[j]/max(vol336[j],1e-8),j))
            signals[t,1,ranked[0]]=1.
        updates[t,1]=True
        vsol=float(np.var(hourly[-336:,3],ddof=1))
        cov=float(np.cov(hourly[-336:,2],hourly[-336:,3],ddof=1)[0,1])
        beta=float(np.clip(cov/max(vsol,1e-12),.5,2.))
        r336=lc[t]-lc[t-336]
        residual=float(r336[2]-beta*r336[3])
        bnb=1./(1.+beta);sol=beta/(1.+beta)
        if residual>0:
            signals[t,2,2]=-bnb
            signals[t,2,3]=sol
        elif residual<0:
            signals[t,2,2]=bnb
            signals[t,2,3]=-sol
        updates[t,2]=True
        hist24=lc[t-672:t,0]-lc[t-696:t-24,0]
        lo,hi=np.quantile(hist24,[.10,.90])
        ret24=float(lc[t,0]-lc[t-24,0])
        ret168=float(lc[t,0]-lc[t-168,0])
        if ret24<lo:
            signals[t,3,0]=-1.
        elif ret24>hi and ret168<0:
            signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CI_GROSS_SOURCE")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    s2,m2,z2=bundle(changed,rates,e)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CI_CAUSAL_CHANNEL_DISPERSION_TAIL_SOURCE_PASS")
