#!/usr/bin/env python3
"""V98 LM frozen 7-slot TRAIN-only signal source. No PnL or future data."""
import numpy as np
HOURS=18288; WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LM_core_only','LM_full','LM_minus_opportunity','LM_minus_RV','LM_minus_stress')

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    n=len(c)
    if n!=HOURS or any(x.shape!=(n,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LM_INVALID_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or np.any(q<0):
        raise ValueError('LM_INVALID_NUMERIC_SOURCE')
    if np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LM_INVALID_OHLC')
    lc=np.log(c);intents=np.zeros((n,4,4));updates=np.zeros((n,4),bool)
    entries=np.zeros((n,3),bool);valid=np.zeros(n,bool);regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,n):
        endpoint=(t,t-24,t-72,t-168,t-336,t-504,t-672,t-720)
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[k]>0) for k in endpoint))
        valid[t]=good
        r720=lc[t]-lc[t-720];r672=lc[t]-lc[t-672];r504=lc[t]-lc[t-504]
        r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168];r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24]
        m336=float(np.median(r336));m168=float(np.median(r168));m72=float(np.median(r72));m24=float(np.median(r24))
        stress=m168<-.025 and m72<-.012
        recovery=m336<-.03 and m24>.025
        risk_on=m336>.04 and r168[0]>.025
        regimes[t]='STRESS' if stress else 'RECOVERY' if recovery else 'RISK_ON' if risk_on else 'RANGE'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%672==0:
            eligible=(r720>0)&(r336>0)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(r504[j]),int(j)))
            rows[0]=0
            if ranked:
                rows[0,ranked[0]]=.48
                if len(ranked)>1:rows[0,ranked[1]]=.16
            updates[t,0]=True
        if good and (t-WARMUP)%168==0 and expiry[1]<0 and 1 not in expired and risk_on:
            eligible=(r168>.04)&(r24>0)
            if np.any(eligible):
                acceleration=r168-(lc[t-168]-lc[t-336])
                j=int(np.argmax(np.where(eligible,acceleration,-np.inf)))
                rows[1]=0;rows[1,j]=.12;expiry[1]=t+168
                updates[t,1]=True;entries[t,0]=True
        if good and (t-WARMUP)%168==0 and expiry[2]<0 and 2 not in expired and m336>.015:
            ranked=sorted(range(4),key=lambda j:(-float(r168[j]),j))
            top,bottom=ranked[0],ranked[-1]
            if r168[top]>.03 and r168[bottom]<0 and r168[top]-r168[bottom]>.10:
                rows[2]=0;rows[2,top]=.05;rows[2,bottom]=-.05;expiry[2]=t+168
                updates[t,2]=True;entries[t,1]=True
        if good and (t-WARMUP)%168==0 and expiry[3]<0 and 3 not in expired:
            if stress:
                rows[3]=0;rows[3,0]=-.08;expiry[3]=t+168
                updates[t,3]=True;entries[t,2]=True
            elif recovery:
                j=int(np.argmax(r24));rows[3]=0;rows[3,j]=.08;expiry[3]=t+168
                updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-10:raise ValueError('LM_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    n=HOURS;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0001,.0002,.0003,.0004]])+.06*np.sin(t[:,None]/41+np.arange(4)))
    o=c*(1-.001*np.sin(t[:,None]/11+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.zeros_like(c);e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[z.copy() for z in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[14000:]*=1.7
    qq[14000:]*=3;rr[14000:]=-.001
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LM_FUTURE_LEAK'
    changed=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changed&~a[1][1:]),'LM_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-10
    q[1000,0]=0;bad=bundle(o,h,l,c,q,r,e)
    assert not bad[3][1001] and bad[3][1025] and not bad[3][1720]
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LM_SYNTHETIC_CAUSALITY_PASS')
