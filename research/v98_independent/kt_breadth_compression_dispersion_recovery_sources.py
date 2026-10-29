#!/usr/bin/env python3
"""KT preregistered breadth growth, ETH compression, BNB/SOL residual momentum, ETH recovery.
Source-only, t completed; no PnL, no 2025, no external benchmarks.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
BUDGET=np.array([.54,.16,.12,.08],dtype=float)
PATHS=("KT_core_only","KT_full","KT_minus_opportunity","KT_minus_RV","KT_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KT_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    market=logc.mean(axis=1)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        rotation=(t-WARMUP)%336==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        breadth=(logc[t,:2]-logc[t-672,:2]>0.) & (c[t,:2]>c[t-671:t+1,:2].mean(axis=0))
        recovery=bool((market[t]-market[t-72]<-.015) and
                      (logc[t,1]-logc[t-24,1]>.007) and
                      (c[t,1]>c[t-71:t+1,1].mean()))
        regimes[t]="RECOVERY" if recovery else "BREADTH" if np.any(breadth) else "MIXED"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if rotation and good:
            current[0]=0.
            if np.all(breadth):current[0,:2]=.27
            elif np.any(breadth):current[0,int(np.argmax(breadth))]=.54
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            recent=np.diff(logc[t-72:t+1,1])
            prior=np.diff(logc[t-240:t-72+1,1])
            compressed=(np.std(recent,ddof=0)<.9*np.std(prior,ddof=0))
            if (compressed and logc[t,1]-logc[t-336,1]>.04 and
                logc[t,1]-logc[t-24,1]>.005):
                current[1]=0.;current[1,1]=.16
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            residual=(logc[t,2:]-logc[t-336,2:])-(logc[t,0]-logc[t-336,0])
            if abs(float(residual[0]-residual[1]))>.04:
                winner=2+int(np.argmax(residual));loser=2+int(np.argmin(residual))
                current[2]=0.;current[2,winner]=.06;current[2,loser]=-.06
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and recovery:
            current[3]=0.;current[3,1]=.08
            expiry[3]=t+120;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.94+1e-10:
            raise ValueError("KT_HIDDEN_GROSS")
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
            raise ValueError("KT_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.94+1e-10):
        raise ValueError("KT_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KT_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KT_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KT_SOURCE_SYNTHETIC_CAUSAL_PASS")
