#!/usr/bin/env python3
"""KU preregistered inverse-vol BTC/ETH growth, ETH pullback, funding-adjusted BNB/SOL momentum, bearish ETH hedge."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.58,.14,.12,.08],dtype=float)
PATHS=("KU_core_only","KU_full","KU_minus_opportunity","KU_minus_RV","KU_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KU_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        rotation=(t-WARMUP)%336==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        trend672=logc[t,:2]-logc[t-672,:2]
        eth_bear=bool(logc[t,1]-logc[t-336,1]<0 and
                      c[t,1]<np.median(c[t-671:t+1,1]))
        regimes[t]="BEAR" if eth_bear else "BULL" if np.any(trend672>0) else "MIXED"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if rotation and good:
            current[0]=0.
            eligible=trend672>0.
            if np.any(eligible):
                vol=np.maximum(np.std(np.diff(logc[t-336:t+1,:2],axis=0),axis=0,ddof=0),1e-8)
                score=np.where(eligible,1./vol,0.)
                current[0,:2]=BUDGET[0]*score/score.sum()
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            if trend672[1]>0 and logc[t,1]-logc[t-24,1]<0:
                current[1]=0.;current[1,1]=BUDGET[1]
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            funding=(r[t-335:t+1]*e[t-335:t+1]).sum(axis=0)
            score=logc[t,2:]-logc[t-336,2:]-funding[2:]
            winner=2+int(np.argmax(score));loser=2+int(np.argmin(score))
            current[2]=0.;current[2,winner]=.06;current[2,loser]=-.06
            expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and eth_bear:
            current[3]=0.;current[3,1]=-BUDGET[3]
            expiry[3]=t+120;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.94+1e-10:
            raise ValueError("KU_HIDDEN_GROSS")
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
            raise ValueError("KU_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.94+1e-10):
        raise ValueError("KU_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KU_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KU_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KU_SOURCE_SYNTHETIC_CAUSAL_PASS")
