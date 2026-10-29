#!/usr/bin/env python3
"""V98 LO frozen composed source: trend, volatility continuation, signed funding carry, crash hedge."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LO_core_only','LO_full','LO_minus_opportunity','LO_minus_RV','LO_minus_stress')

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    n=len(c)
    if n!=HOURS or any(x.shape!=(n,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LO_INVALID_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or np.any(q<0):
        raise ValueError('LO_INVALID_NUMERIC_SOURCE')
    if np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LO_INVALID_OHLC')
    lc=np.log(c);intents=np.zeros((n,4,4));updates=np.zeros((n,4),bool)
    entries=np.zeros((n,3),bool);valid=np.zeros(n,bool);regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,n):
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-lag]>0) for lag in (0,24,72,168,336,720)))
        valid[t]=good
        r720=lc[t]-lc[t-720];r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24]
        m168=float(np.median(r168));m72=float(np.median(r72));m24=float(np.median(r24))
        stress=m168<0 and m72<-.01
        recovery=m168<0 and m24>.018
        risk_on=m168>.01
        regimes[t]='STRESS' if stress else 'RECOVERY' if recovery else 'RISK_ON' if risk_on else 'RANGE'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%336==0:
            eligible=(r720>0)&(r336>0)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(r336[j]),int(j)))
            rows[0]=0
            if ranked:
                rows[0,ranked[0]]=.60
                if len(ranked)>1:rows[0,ranked[1]]=.12
            updates[t,0]=True
        if good and (t-WARMUP)%72==0 and expiry[1]<0 and 1 not in expired and risk_on:
            v72=np.std(np.diff(lc[t-72:t+1],axis=0),axis=0)
            v336=np.std(np.diff(lc[t-336:t+1],axis=0),axis=0)
            eligible=(r24>.012)&(r168>.03)&(v72<v336)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r168,-np.inf)))
                rows[1]=0;rows[1,j]=.10;expiry[1]=t+72
                updates[t,1]=True;entries[t,0]=True
        if good and (t-WARMUP)%168==0 and expiry[2]<0 and 2 not in expired:
            if not np.all(event[t-56:t+1:8]):raise ValueError('LO_NATIVE_FUNDING_HISTORY_MISSING')
            f=np.mean(rate[t-56:t+1:8],axis=0)
            lowest=int(np.argmin(f));highest=int(np.argmax(f))
            if lowest!=highest and f[highest]>f[lowest]:
                rows[2]=0;rows[2,lowest]=.04;rows[2,highest]=-.04;expiry[2]=t+168
                updates[t,2]=True;entries[t,1]=True
        if good and (t-WARMUP)%72==0 and expiry[3]<0 and 3 not in expired:
            if stress:
                rows[3]=0;rows[3,0]=-.04;expiry[3]=t+72
                updates[t,3]=True;entries[t,2]=True
            elif recovery:
                j=int(np.argmax(r24));rows[3]=0;rows[3,j]=.04;expiry[3]=t+72
                updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-10:raise ValueError('LO_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    n=HOURS;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0001,.0002,.0003,.0004]])+.06*np.sin(t[:,None]/41+np.arange(4)))
    o=c*(1-.001*np.sin(t[:,None]/11+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.tile(np.array([[-.0001,.0001,.0002,.0003]]),(n,1));e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[z.copy() for z in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[14000:]*=1.7
    qq[14000:]*=3;rr[14000:]*=-1
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LO_FUTURE_LEAK'
    changed=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changed&~a[1][1:]),'LO_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-10
    q[1000,0]=0;bad=bundle(o,h,l,c,q,r,e)
    assert not bad[3][1001] and bad[3][1025] and not bad[3][1720]
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LO_SYNTHETIC_CAUSALITY_PASS')
