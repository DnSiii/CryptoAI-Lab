#!/usr/bin/env python3
"""V98 LF frozen volatility trend / residual reversal seven-slot sources, 2023-24 TRAIN only."""
from __future__ import annotations
import numpy as np
WARMUP=744
HOURS=18288
BUDGET=np.array([.70,.10,.08,.06])
PATHS=('LF_core_only','LF_full','LF_minus_opportunity','LF_minus_RV','LF_minus_stress')
LAGS=(6,24,72,168,336)
WINDOWS=(168,64)

def quote_safe(q,t):
    if t<max((24,*LAGS,*WINDOWS)):return False
    spans=[q[t-23:t+1]]+[q[t-k:t-k+1] for k in LAGS]+[q[t-w+1:t+1] for w in WINDOWS]
    if any(not np.isfinite(s).all() or np.any(s<0) for s in spans):raise ValueError('LF_INVALID_QUOTE_SOURCE')
    return all(np.all(s>0) for s in spans)

def bundle(o,h,l,c,q,r,e):
    o,h,l,c,q,r,e=(np.asarray(a,dtype=float) for a in (o,h,l,c,q,r,e))
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,q,r,e)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):raise ValueError('LF_INVALID_CANONICAL_SOURCE')
    n=len(c);lc=np.log(c)
    intents=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool);valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        good=quote_safe(q,t);valid[t]=good
        r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24];r6=lc[t]-lc[t-6]
        med168=float(np.median(r168));med72=float(np.median(r72))
        risk_on=med168>0
        stress=int(np.sum(r72<-.04))>=2 and med72<0
        regimes[t]='STRESS' if stress else 'RISK_ON' if risk_on else 'RANGE'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if (t-WARMUP)%168==0 and good:
            hourly=np.diff(lc[t-168:t+1],axis=0)
            vol=np.std(hourly,axis=0)*np.sqrt(168.)
            eligible=(r336>0)&(r168>0)
            score=(r336+r168)/np.maximum(.01,vol)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(score[j]),int(j)))
            rows[0]=0.
            if ranked:rows[0,ranked[0]]=.62
            if len(ranked)>1:rows[0,ranked[1]]=.08
            updates[t,0]=True
        if (t-WARMUP)%48==0 and good and risk_on and expiry[1]<0 and 1 not in expired:
            eligible=(r336>0)&(r24<0)&(r6>0)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r336,-np.inf)))
                rows[1]=0.;rows[1,j]=.10;expiry[1]=t+48
                updates[t,1]=True;entries[t,0]=True
        if (t-WARMUP)%72==0 and good and abs(med72)<.08 and expiry[2]<0 and 2 not in expired:
            residual=r24-float(np.median(r24))
            hi=int(np.argmax(residual));lo=int(np.argmin(residual))
            if residual[hi]-residual[lo]>.05:
                rows[2]=0.;rows[2,lo]=.04;rows[2,hi]=-.04
                expiry[2]=t+72;updates[t,2]=True;entries[t,1]=True
        if (t-WARMUP)%48==0 and good and stress and expiry[3]<0 and 3 not in expired:
            j=int(np.argmin(r72))
            rows[3]=0.;rows[3,j]=-.06;expiry[3]=t+48
            updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-10:raise ValueError('LF_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def static_check():
    n=2400;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+.07*np.sin(t[:,None]/79.+np.arange(4)))
    o=c*(1-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e7);r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[z.copy() for z in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[1700:]*=1.7
    qq[1700:]*=3;rr[1700:]=-.002
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:1700],y[:1700]) for x,y in zip(a,b))
    assert not np.any(np.any(np.diff(a[0],axis=0)!=0,axis=2)&~a[1][1:])
    bad=q.copy();bad[700,0]=0.
    assert not bundle(o,h,l,c,bad,r,e)[3][744]
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-10
    return True
if __name__=='__main__':
    assert static_check();print('LF_SOURCE_CAUSAL_PASS')
