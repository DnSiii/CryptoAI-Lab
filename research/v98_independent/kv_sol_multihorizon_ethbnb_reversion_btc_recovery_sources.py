#!/usr/bin/env python3
"""KV source-only SOL dual horizon core, SOL relative strength, ETH/BNB reversion, BTC rebound."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.60,.14,.12,.08],dtype=float)
PATHS=("KV_core_only","KV_full","KV_minus_opportunity","KV_minus_RV","KV_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KV_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c);market=logc.mean(axis=1)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"BTC_TREND",dtype="<U12")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        rotation=(t-WARMUP)%336==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        r672=logc[t]-logc[t-672]
        r168=logc[t]-logc[t-168]
        sol_growth=bool(r672[3]>0 and r168[3]>0)
        defensive=bool(market[t]-market[t-72]<0)
        regimes[t]="SOL_GROWTH" if sol_growth else "DEFENSIVE" if defensive else "BTC_TREND"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if rotation and good:
            current[0]=0.
            if sol_growth:
                if r672[0]>0:
                    current[0,3]=.40;current[0,0]=.20
                else:current[0,3]=.60
            elif r672[0]>0:current[0,0]=.60
            elif r672[1]>0:current[0,1]=.60
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            if r168[3]>r168[0]:
                current[1]=0.;current[1,3]=BUDGET[1]
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            diff=float(r168[1]-r168[2])
            if abs(diff)>.03:
                current[2]=0.
                if diff>0:current[2,1]=-.06;current[2,2]=.06
                else:current[2,1]=.06;current[2,2]=-.06
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired:
            if defensive and logc[t,0]-logc[t-24,0]>0:
                current[3]=0.;current[3,0]=BUDGET[3]
                expiry[3]=t+96;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.94+1e-10:
            raise ValueError("KV_HIDDEN_GROSS")
    return intents,updates,entries,valid,regimes

def static_check():
    n=1900;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
        .045*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.tile(np.array([-.00008,.00012,.00001,.00025]),(n,1))
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[1600:]*=1.8
    qq[1600:]*=4.;rr[1600:]*=-1
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1600],b[i][:1600]):
            raise ValueError("KV_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.94+1e-10):
        raise ValueError("KV_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KV_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KV_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KV_SOURCE_SYNTHETIC_CAUSAL_PASS")
