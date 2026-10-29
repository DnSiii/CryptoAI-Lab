#!/usr/bin/env python3
"""KX preregistered breadth/carry seven-slot causal source, 2023-2024 training only."""
from __future__ import annotations
import numpy as np

WARMUP=744
BUDGET=np.array([.64,.12,.10,.08],dtype=float)
PATHS=("KX_core_only","KX_full","KX_minus_opportunity","KX_minus_RV","KX_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KX_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c);market=logc.mean(axis=1)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U12")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        weekly=(t-WARMUP)%168==0
        rotation=(t-WARMUP)%672==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        r336=logc[t]-logc[t-336]
        m336=float(market[t]-market[t-336])
        m72=float(market[t]-market[t-72])
        regimes[t]="TREND" if m336>0 else "DEFENSE" if m72<0 else "MIXED"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if rotation and good:
            current[0]=0.
            if m336>0:
                current[0,0]=.24;current[0,3]=.24;current[0,2]=.16
            elif r336[0]>0:
                current[0,0]=BUDGET[0]
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            r168=logc[t]-logc[t-168]
            vol=np.std(np.diff(logc[t-168:t+1],axis=0),axis=0,ddof=0)
            eligible=(r168>0)&(vol>1e-12)
            if np.any(eligible):
                score=np.where(eligible,r168/np.maximum(vol,1e-12),-np.inf)
                j=int(np.argmax(score))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            carry=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
            eligible=(r336>0)&(carry<0)
            if np.any(eligible):
                j=int(np.argmin(np.where(eligible,carry,np.inf)))
                current[2]=0.;current[2,j]=BUDGET[2]
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if weekly and good and expiry[3]<0 and 3 not in expired and m72<0:
            r72=logc[t]-logc[t-72]
            j=int(np.argmax(r72))
            current[3]=0.;current[3,j]=BUDGET[3]
            expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.94+1e-10:
            raise ValueError("KX_HIDDEN_GROSS")
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
    qq[1600:]*=4.;rr[1600:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1600],b[i][:1600]):
            raise ValueError("KX_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.94+1e-10):
        raise ValueError("KX_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KX_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KX_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KX_SOURCE_SYNTHETIC_CAUSAL_PASS")
