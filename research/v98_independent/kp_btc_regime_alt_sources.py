#!/usr/bin/env python3
"""KP prospective seven-slot source: BTC regime, alt momentum opportunity and relative-strength spread."""
from __future__ import annotations
import numpy as np

WARMUP=744
BUDGET=np.array([.60,.17,.10,.08],dtype=float)
PATHS=("KP_core_only","KP_full","KP_minus_opportunity","KP_minus_RV","KP_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KP_INVALID_CANONICAL_SOURCE")
    n=len(c)
    logc=np.log(c)
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
        market72=float(np.mean(logc[t]-logc[t-72]))
        market24=float(np.mean(logc[t]-logc[t-24]))
        btc336=float(logc[t,0]-logc[t-336,0])
        bull=btc336>0 and c[t,0]>np.mean(c[t-719:t+1,0])
        recovery=market72<-.06 and market24>.005
        regimes[t]="RECOVERY" if recovery else "STRESS" if market72<-.06 else "BULL" if bull else "NEUTRAL"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if weekly and good:
            target=np.zeros(4,dtype=float)
            if good and bull:target[0]=BUDGET[0]
            current[0]=target;updates[t,0]=True
        if daily and good and expiry[1]<0 and 1 not in expired:
            momentum=logc[t,1:]-logc[t-72,1:]
            q24=q[t-23:t+1,1:].mean(axis=0)
            q168=q[t-191:t-23,1:].mean(axis=0)
            eligible=(momentum>.05)&(q24>1.10*q168)
            if np.any(eligible):
                j=1+int(np.argmax(np.where(eligible,momentum,-np.inf)))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+96;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            relative=logc[t,1:]-logc[t-168,1:]
            winner=1+int(np.argmax(relative));loser=1+int(np.argmin(relative))
            if winner!=loser and float(np.max(relative)-np.min(relative))>.07:
                current[2]=0.;current[2,winner]=BUDGET[2]/2
                current[2,loser]=-BUDGET[2]/2
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and recovery:
            current[3]=0.;current[3,0]=BUDGET[3]
            expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>1.+1e-10:
            raise ValueError("KP_HIDDEN_GROSS")
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
            raise ValueError("KP_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.95+1e-10):
        raise ValueError("KP_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KP_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KP_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("KP_SOURCE_SYNTHETIC_CAUSAL_PASS")
