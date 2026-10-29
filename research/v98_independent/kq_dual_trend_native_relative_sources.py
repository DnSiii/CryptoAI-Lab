#!/usr/bin/env python3
"""KQ source-only preregistered dual-core trend, volume impulse, funding-adjusted relative strength and downside."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.58,.18,.12,.07],dtype=float)
PATHS=("KQ_core_only","KQ_full","KQ_minus_opportunity","KQ_minus_RV","KQ_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KQ_INVALID_CANONICAL_SOURCE")
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
        rv_clock=(t-WARMUP)%120==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        momentum504=logc[t,:2]-logc[t-504,:2]
        trend=(momentum504>0)&(c[t,:2]>c[t-503:t+1,:2].mean(axis=0))
        m24=logc[t]-logc[t-24]
        market24=float(m24.mean())
        stress=market24<-.02 and (m24[3]-m24[0])<-.01
        regimes[t]="STRESS" if stress else "RISK_ON" if trend.all() else "MIXED" if trend.any() else "NEUTRAL"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if weekly and good:
            current[0]=0.
            current[0,:2]=np.where(trend,BUDGET[0]/2,0.)
            updates[t,0]=True
        if daily and good and expiry[1]<0 and 1 not in expired:
            momentum=m24[1:]
            q24=q[t-23:t+1,1:].mean(axis=0)
            q168=q[t-191:t-23,1:].mean(axis=0)
            eligible=(momentum>.025)&(q24>1.05*q168)
            if np.any(eligible):
                j=1+int(np.argmax(np.where(eligible,momentum,-np.inf)))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+72;updates[t,1]=True;entries[t,0]=True
        if rv_clock and good and expiry[2]<0 and 2 not in expired:
            paid=(r[t-119:t+1]*e[t-119:t+1]).sum(axis=0)
            adjusted=(logc[t]-logc[t-120])-2.*paid
            j=1+int(np.argmax(adjusted[1:]))
            if adjusted[j]>.015 and adjusted[j]>adjusted[0]:
                current[2]=0.;current[2,j]=BUDGET[2]
                expiry[2]=t+120;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0 and 3 not in expired and stress:
            current[3]=0.;current[3,3]=-BUDGET[3]
            expiry[3]=t+48;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>1.+1e-10:
            raise ValueError("KQ_HIDDEN_GROSS")
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
            raise ValueError("KQ_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>.95+1e-10):
        raise ValueError("KQ_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KQ_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KQ_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("KQ_SOURCE_SYNTHETIC_CAUSAL_PASS")
