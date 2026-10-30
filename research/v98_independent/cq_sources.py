#!/usr/bin/env python3
"""CQ causal directional dispersion / compression-breakout recovery seven-slot source.
Only completed bar t used; execution earliest next open.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.75,.45,.30,.20]),
 "MIXED":np.array([1.30,.40,.40,.35]),
 "RISK_OFF":np.array([.60,.30,.45,.55]),
}

def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e,q))
        or len(c)<=WARMUP or any(not np.isfinite(x).all() for x in (c,r,e,q))
        or np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CQ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r24=lc[t]-lc[t-24]
        r48=lc[t]-lc[t-48]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        r672=lc[t]-lc[t-672]
        nup=int(np.count_nonzero(r336>0))
        ndown=int(np.count_nonzero(r336<0))
        regimes[t]=("RISK_ON" if nup>=3 and r168[0]>0 else
                    "RISK_OFF" if ndown>=3 and r168[0]<0 else "MIXED")
        if (t-WARMUP)%336==0:
            returns672=np.diff(lc[t-672:t+1],axis=0)
            quality=r672/(np.sqrt(672.)*np.maximum(np.std(returns672,axis=0),1e-12))
            eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0]
            ranked=sorted(eligible,key=lambda j:(-quality[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.55
                signals[t,0,ranked[1]]=.45
            updates[t,0]=True
        vol72=np.std(np.diff(lc[t-72:t+1],axis=0),axis=0)
        vol336=np.std(np.diff(lc[t-408:t-71],axis=0),axis=0)
        candidates=[j for j in (2,3) if
                    r48[j]>.03 and c[t,j]>float(np.max(c[t-336:t,j]))
                    and vol72[j]>vol336[j]]
        if candidates:
            j=sorted(candidates,key=lambda j:(-r48[j],j))[0]
            signals[t,1,j]=1.
        updates[t,1]=True
        recent=np.diff(lc[t-168:t+1],axis=0)
        corr={}
        for j in (1,2,3):
            sd=float(np.std(recent[:,0])*np.std(recent[:,j]))
            corr[j]=float(np.mean((recent[:,0]-recent[:,0].mean())*
                                 (recent[:,j]-recent[:,j].mean())))/max(sd,1e-12)
        eligible=[j for j in (1,2,3) if r336[j]-r336[0]>.02
                  and r168[j]>0 and r336[0]>0 and corr[j]>.35]
        if eligible:
            j=sorted(eligible,key=lambda j:(-(r336[j]-r336[0]),j))[0]
            signals[t,2,j]=.5
            signals[t,2,0]=-.5
        updates[t,2]=True
        if (int(np.count_nonzero(r168<0))>=2 and float(np.mean(r24))>0
            and float(np.mean(vol72))<float(np.mean(vol336))):
            signals[t,3,0]=.60
            signals[t,3,1]=.40
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CQ_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CQ_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e,q)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    volumes=q.copy();volumes[2900:]*=4.
    s2,m2,z2=bundle(changed,rates,e,volumes)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CQ_CAUSAL_DIRECTIONAL_DISPERSION_SOURCE_PASS")
