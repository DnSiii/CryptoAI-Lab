#!/usr/bin/env python3
"""V98 Independent LE preregistered seven-slot source. TRAIN ONLY 2023-24; no PnL."""
from __future__ import annotations
import numpy as np
HOURS=18288
WARMUP=744
BUDGET=np.array([.70,.10,.08,.06],dtype=float)
PATHS=('LE_core_only','LE_full','LE_minus_opportunity','LE_minus_RV','LE_minus_stress')
FEATURE_LAGS=(6,24,72,168,504)
CONTINUOUS_WINDOWS=(168,64)

def quote_safe(q,t):
    if t<max((24,*FEATURE_LAGS,*CONTINUOUS_WINDOWS)):
        return False
    spans=[q[t-23:t+1]]
    spans.extend(q[t-k:t-k+1] for k in FEATURE_LAGS)
    spans.extend(q[t-w+1:t+1] for w in CONTINUOUS_WINDOWS)
    if any(not np.isfinite(s).all() or np.any(s<0) for s in spans):
        raise ValueError('LE_INVALID_QUOTE_SOURCE')
    return all(np.all(s>0) for s in spans)

def bundle(o,h,l,c,q,r,e):
    o,h,l,c,q,r,e=(np.asarray(a,dtype=float) for a in (o,h,l,c,q,r,e))
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,q,r,e)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError('LE_INVALID_CANONICAL_SOURCE')
    n=len(c); lc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,'NEUTRAL',dtype='<U13')
    rows=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        good=quote_safe(q,t);valid[t]=good
        r504=lc[t]-lc[t-504];r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24];r6=lc[t]-lc[t-6]
        risk_on=float(np.median(r168))>0
        stress=(int(np.sum(r72<-.03))>=3 and float(np.median(r168))<0)
        regimes[t]='BROAD_STRESS' if stress else 'RISK_ON' if risk_on else 'NEUTRAL'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if (t-WARMUP)%336==0 and good:
            eligible=(r504>0)&(r168>0)&(r72>0)
            score=.6*r504+.4*r168-.5*np.maximum(0.,-np.minimum(r72,r168))
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(score[j]),int(j)))
            rows[0]=0.
            if ranked:rows[0,ranked[0]]=.62
            if len(ranked)>1:rows[0,ranked[1]]=.08
            updates[t,0]=True
        if (t-WARMUP)%72==0 and good and risk_on and expiry[1]<0 and 1 not in expired:
            event_idx=np.arange(max(0,t//8-5),t//8+1,dtype=int)*8
            if len(event_idx)==6 and np.all(e[event_idx,:]>0):
                avg=np.mean(r[event_idx,:],axis=0)
                eligible=(avg<-.00003)&(r24>0)&(r6>0)
                if np.any(eligible):
                    j=int(np.argmin(np.where(eligible,avg,np.inf)))
                    rows[1]=0.;rows[1,j]=.10
                    expiry[1]=t+72;updates[t,1]=True;entries[t,0]=True
        if (t-WARMUP)%168==0 and good and expiry[2]<0 and 2 not in expired:
            high_j=int(np.argmax(r168));low_j=int(np.argmin(r168))
            if r168[high_j]>0 and r168[low_j]<0 and r168[high_j]-r168[low_j]>.12:
                rows[2]=0.;rows[2,high_j]=.04;rows[2,low_j]=-.04
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if (t-WARMUP)%72==0 and good and stress and expiry[3]<0 and 3 not in expired:
            j=int(np.argmin(r72))
            rows[3]=0.;rows[3,j]=-.06
            expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-10:
            raise ValueError('LE_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def static_check():
    n=2400;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .08*np.sin(t[:,None]/71.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e7);r=np.tile(np.array([-.0002,.00025,.00001,-.0001]),(n,1))
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,q,r,e)
    cc=c.copy();oo=o.copy();hh=h.copy();ll=l.copy();qq=q.copy();rr=r.copy();ee=e.copy()
    for z in (cc,oo,hh,ll):z[1700:]*=1.8
    qq[1700:]*=4.;rr[1700:]*=-1.;ee[1700:]=0.
    b=bundle(oo,hh,ll,cc,qq,rr,ee)
    for k in range(5):
        if not np.array_equal(a[k][:1700],b[k][:1700]):
            raise ValueError('LE_FUTURE_LEAK_'+str(k))
    changed=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changed&~a[1][1:]):raise ValueError('LE_SILENT_ROW_CHANGE')
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,bad,r,e)
    if g[3][744] or np.any(g[2][744]):raise ValueError('LE_BAD_QUOTE_ENTRY')
    if np.abs(a[0]).sum(axis=(1,2)).max()>.94+1e-10:
        raise ValueError('LE_OVERBUDGET')
    return True
if __name__=='__main__':
    assert static_check()
    print('LE_SYNTHETIC_CAUSAL_AND_BUDGET_PASS')
