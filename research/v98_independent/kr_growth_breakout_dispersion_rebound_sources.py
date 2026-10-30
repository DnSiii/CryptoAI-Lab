#!/usr/bin/env python3
"""KR preregistered growth / volatility breakout / cross-sectional dispersion / shock rebound; source-only."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.60,.16,.12,.07],dtype=float)
PATHS=("KR_core_only","KR_full","KR_minus_opportunity","KR_minus_RV","KR_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KR_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NEUTRAL",dtype="<U10")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        trend=(logc[t,:2]-logc[t-336,:2]>0)&(c[t,:2]>c[t-671:t+1,:2].mean(axis=0))
        shock=float(np.mean(logc[t]-logc[t-96]))<-.06
        rebound=float(np.mean(logc[t]-logc[t-12]))>.01
        recovery=shock and rebound
        regimes[t]="REBOUND" if recovery else "TREND" if trend.all() else "MIXED" if trend.any() else "NEUTRAL"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if weekly and good:
            current[0]=0.
            current[0,:2]=np.where(trend,.30,0.)
            updates[t,0]=True
        if daily and good and expiry[1]<0 and 1 not in expired:
            breakout=c[t,2:]>np.max(h[t-240:t,2:],axis=0)
            vol_now=q[t-23:t+1,2:].mean(axis=0)
            vol_prior=q[t-191:t-23,2:].mean(axis=0)
            eligible=breakout&(vol_now>1.20*vol_prior)&(logc[t,2:]-logc[t-48,2:]>0)
            if np.any(eligible):
                # deterministic largest normalized breakout, BNB tie first
                strength=c[t,2:]/np.max(h[t-240:t,2:],axis=0)-1.
                j=2+int(np.argmax(np.where(eligible,strength,-np.inf)))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+96;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            relative=float((logc[t,2]-logc[t-168,2])-(logc[t,3]-logc[t-168,3]))
            if abs(relative)>.06:
                leader,laggard=(2,3) if relative>0 else (3,2)
                current[2]=0.;current[2,leader]=.06;current[2,laggard]=-.06
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and recovery:
            current[3]=0.;current[3,0]=BUDGET[3]
            expiry[3]=t+120;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>1.+1e-10:
            raise ValueError("KR_HIDDEN_GROSS")
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
            raise ValueError("KR_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.95+1e-10):
        raise ValueError("KR_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KR_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KR_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("KR_SOURCE_SYNTHETIC_CAUSAL_PASS")
