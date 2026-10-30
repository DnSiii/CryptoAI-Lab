#!/usr/bin/env python3
"""KN preregistered 7-slot event-latched leadership source-only intents. No PnL."""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.58,.16,.12,.08],dtype=float)
PATHS=("KN_core_only","KN_full","KN_minus_opportunity","KN_minus_RV","KN_minus_stress")
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KN_INVALID_CANONICAL_SOURCE")
    n=len(c)
    net=np.zeros_like(c)
    net[1:]=np.diff(np.log(c),axis=0)
    net-=r*e
    market=net.mean(axis=1)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        rv_clock=(t-WARMUP)%48==0
        core_clock=(t-WARMUP)%1440==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        m24=net[t-23:t+1].sum(axis=0)
        m48=net[t-47:t+1].sum(axis=0)
        m72=net[t-71:t+1].sum(axis=0)
        market24=float(market[t-23:t+1].sum())
        market72=float(market[t-71:t+1].sum())
        prior72=float(market[t-95:t-23].sum())
        if daily:
            regimes[t]=("STRESS" if market72<-.045 else
                        "RECOVERY" if market24>.025 and prior72<0 else "NORMAL")
        else:regimes[t]=regimes[t-1]
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1
        if core_clock and good:
            n720=net[t-719:t+1].sum(axis=0)
            downside=np.sqrt(np.mean(np.minimum(net[t-719:t+1],0.)**2,axis=0))
            score=n720-.30*downside*np.sqrt(168.)
            leader=int(np.argmax(score))
            current[0]=0.
            if score[leader]>0:current[0,leader]=BUDGET[0]
            updates[t,0]=True
        if daily and good and expiry[1]<0:
            recentq=q[t-47:t+1].mean(axis=0)
            priorq=q[t-143:t-47].mean(axis=0)
            eligible=(m48>.035)&(recentq>1.15*priorq)
            if np.any(eligible):
                leader=int(np.argmax(np.where(eligible,m48,-np.inf)))
                current[1]=0.;current[1,leader]=BUDGET[1]
                expiry[1]=t+96;updates[t,1]=True;entries[t,0]=True
        if rv_clock and good and expiry[2]<0:
            n336=net[t-335:t+1].sum(axis=0)
            downside=np.sqrt(np.mean(np.minimum(net[t-335:t+1],0.)**2,axis=0))
            score=n336-.35*downside*np.sqrt(168.)
            relative=score-np.median(score)
            leader=int(np.argmax(relative))
            if relative[leader]>.025 and n336[leader]>0:
                current[2]=0.;current[2,leader]=BUDGET[2]
                expiry[2]=t+336;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0:
            leader=int(np.argmax(m24))
            if market72<-.045 and m24[leader]>0:
                current[3]=0.;current[3,leader]=BUDGET[3]
                expiry[3]=t+48;updates[t,3]=True;entries[t,2]=True
            elif market24>.025 and prior72<0 and m24[leader]>0:
                current[3]=0.;current[3,leader]=BUDGET[3]
                expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>sum(BUDGET)+1e-10:
            raise ValueError("KN_HIDDEN_GROSS")
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
            raise ValueError("KN_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>sum(BUDGET)+1e-10):
        raise ValueError("KN_GROSS")
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KN_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("KN_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("KN_SOURCE_SYNTHETIC_CAUSAL_PASS")
