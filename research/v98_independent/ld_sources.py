#!/usr/bin/env python3
"""LD preregistered 7-slot source: downside-adjusted trend, squeeze, native funding carry, defensive trend.
TRAIN 2023/24 only; completed-close t decisions; no PnL, validation, benchmark or holdout.
"""
from __future__ import annotations
import numpy as np
from v98_prospective_quote_outage_policy import quote_safe
WARMUP=744
BUDGET=np.array([.68,.12,.08,.07],dtype=float)
PATHS=('LD_core_only','LD_full','LD_minus_opportunity','LD_minus_RV','LD_minus_stress')
FEATURE_LAGS=(6,24,72,168,336,672)
CONTINUOUS_WINDOWS=(168,64)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError('LD_INVALID_CANONICAL_SOURCE')
    n=len(c);lc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,'MIXED',dtype='<U12')
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        weekly=(t-WARMUP)%168==0
        biweekly=(t-WARMUP)%336==0
        good=quote_safe(q,t,FEATURE_LAGS,CONTINUOUS_WINDOWS)
        valid[t]=good
        r672=lc[t]-lc[t-672]
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72]
        r24=lc[t]-lc[t-24]
        r6=lc[t]-lc[t-6]
        m168=float(np.median(r168))
        regimes[t]='GROWTH' if m168>0 else 'DEFENSE' if m168<0 else 'MIXED'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if biweekly and good:
            current[0]=0.
            hourly=np.diff(lc[t-168:t+1],axis=0)
            downside=np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0))
            eligible=np.flatnonzero((r336>0)&(r72>0))
            score=r672/np.maximum(.005,downside)
            ranked=sorted(eligible,key=lambda j:(-float(score[j]),int(j)))
            if ranked:current[0,ranked[0]]=.58
            if len(ranked)>1:current[0,ranked[1]]=.10
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired and m168>0:
            vol24=np.std(np.diff(lc[t-24:t+1],axis=0),axis=0)
            vol168=np.std(np.diff(lc[t-168:t+1],axis=0),axis=0)
            ratio=vol24/np.maximum(vol168,1e-12)
            eligible=(r168>0)&(r6>0)&(ratio<.85)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r6,-np.inf)))
                current[1]=0.;current[1,j]=.12
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            event_idx=np.flatnonzero(e[:t+1,0]>0)[-8:]
            # Every asset must share the exact eight completed native event timestamps.
            if (len(event_idx)==8 and np.all(e[event_idx,:]>0)):
                mean_funding=np.mean(r[event_idx,:],axis=0)
                lo=int(np.argmin(mean_funding));hi=int(np.argmax(mean_funding))
                if lo!=hi and mean_funding[hi]-mean_funding[lo]>.00010:
                    current[2]=0.;current[2,lo]=.04;current[2,hi]=-.04
                    expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if weekly and good and expiry[3]<0 and 3 not in expired and m168<0:
            j=int(np.argmin(r168))
            if r24[j]<0:
                current[3]=0.;current[3,j]=-.07
                expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.95+1e-10:
            raise ValueError('LD_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def static_check():
    n=2400;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .07*np.sin(t[:,None]/79.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.tile(np.array([-.00020,.00025,.00001,.00012]),(n,1))
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[1700:]*=1.8
    qq[1700:]*=4.;rr[1700:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1700],b[i][:1700]):
            raise ValueError('LD_FUTURE_LEAK_'+str(i))
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes&~a[1][1:]):raise ValueError('LD_SILENT_ROW_REBALANCE')
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError('LD_QUOTE_QUARANTINE')
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.95+1e-10
    assert not a[1][:WARMUP].any()
    return True
if __name__=='__main__':
    assert static_check()
    print('LD_SOURCE_SYNTHETIC_CAUSAL_PASS')
