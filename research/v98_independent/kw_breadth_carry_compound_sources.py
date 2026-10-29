#!/usr/bin/env python3
"""KW preregistered breadth/carry seven-slot causal source, 2023-2024 training only."""
from __future__ import annotations
import numpy as np

WARMUP=744
BUDGET=np.array([.54,.14,.10,.08],dtype=float)
PATHS=("KW_core_only","KW_full","KW_minus_opportunity","KW_minus_RV","KW_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KW_INVALID_CANONICAL_SOURCE")
    n=len(c);logc=np.log(c);market=logc.mean(axis=1)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"DEFENSIVE",dtype="<U12")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        rotation=(t-WARMUP)%672==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        r336=logc[t]-logc[t-336]
        breadth=int(np.sum(r336>0))
        m336=float(market[t]-market[t-336])
        m168=float(market[t]-market[t-168])
        m24=float(market[t]-market[t-24])
        riskon=breadth>=2 and m336>0
        recovery=m168<-.02 and m24>0
        regimes[t]="BREADTH" if riskon else "RECOVERY" if recovery else "DEFENSIVE"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if rotation and good:
            current[0]=0.
            if riskon:
                carry=(r[t-335:t+1]*e[t-335:t+1]).sum(axis=0)
                score=np.where(r336>0,r336-2.*np.maximum(carry,0.),-np.inf)
                winners=np.argsort(-score)[:2]
                if np.isfinite(score[winners]).all():
                    current[0,winners]=.27
            elif logc[t,0]-logc[t-672,0]>0:
                current[0,0]=BUDGET[0]
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            r72=logc[t]-logc[t-72]
            r168=logc[t]-logc[t-168]
            now=q[t-23:t+1].mean(axis=0)
            before=q[t-191:t-23].mean(axis=0)
            eligible=(r72>.02)&(r168>.04)&(now>before)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r72,-np.inf)))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            # Weekly eligibility, 336h fixed unit hold, 168h native funding source.
            carry=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
            eligible=(r336>0)
            if np.any(eligible):
                j=int(np.argmin(np.where(eligible,carry,np.inf)))
                if carry[j]<.0005:
                    current[2]=0.;current[2,j]=BUDGET[2]
                    expiry[2]=t+336;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and recovery:
            r24=logc[t]-logc[t-24]
            j=int(np.argmax(r24))
            if r24[j]>0:
                current[3]=0.;current[3,j]=BUDGET[3]
                expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.86+1e-10:
            raise ValueError("KW_HIDDEN_GROSS")
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
            raise ValueError("KW_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.86+1e-10):
        raise ValueError("KW_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KW_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KW_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KW_SOURCE_SYNTHETIC_CAUSAL_PASS")
