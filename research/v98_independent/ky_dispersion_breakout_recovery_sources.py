#!/usr/bin/env python3
"""KY preregistered dual-horizon trend, completed-range breakout, native funding spread, recovery."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.66,.12,.10,.06],dtype=float)
PATHS=("KY_core_only","KY_full","KY_minus_opportunity","KY_minus_RV","KY_minus_stress")
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KY_INVALID_CANONICAL_SOURCE")
    n=len(c);lc=np.log(c);market=lc.mean(axis=1)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U12")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        weekly=(t-WARMUP)%168==0
        monthly=(t-WARMUP)%672==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        r672=lc[t]-lc[t-672];r168=lc[t]-lc[t-168];r24=lc[t]-lc[t-24]
        m672=float(market[t]-market[t-672])
        m168=float(market[t]-market[t-168])
        m24=float(market[t]-market[t-24])
        regimes[t]="TREND" if m672>0 else "RECOVERY" if m168<0 and m24>0 else "DEFENSE" if m168<0 else "MIXED"
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if monthly and good:
            current[0]=0.
            eligible=np.flatnonzero((r168>0)&(r672>0))
            if len(eligible):
                ranked=eligible[np.argsort(-r672[eligible],kind="stable")]
                if len(ranked)==1:current[0,ranked[0]]=.66
                else:current[0,ranked[0]]=.44;current[0,ranked[1]]=.22
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired:
            excess=c[t]/np.max(h[t-168:t],axis=0)-1.
            eligible=(excess>0)&(lc[t]-lc[t-336]>0)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,excess,-np.inf)))
                current[1]=0.;current[1,j]=BUDGET[1]
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            carry=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
            lo=int(np.argmin(carry));hi=int(np.argmax(carry))
            if lo!=hi and carry[hi]-carry[lo]>.0015:
                current[2]=0.;current[2,lo]=.05;current[2,hi]=-.05
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if weekly and good and expiry[3]<0 and 3 not in expired and m168<0 and m24>0:
            eligible=r24>0
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r24,-np.inf)))
                current[3]=0.;current[3,j]=BUDGET[3]
                expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.94+1e-10:raise ValueError("KY_HIDDEN_GROSS")
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
            raise ValueError("KY_FUTURE_LEAK_"+str(i))
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):raise ValueError("KY_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KY_QUOTE_QUARANTINE")
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-10
    return True
if __name__=="__main__":
    assert static_check()
    print("KY_SOURCE_SYNTHETIC_CAUSAL_PASS")
