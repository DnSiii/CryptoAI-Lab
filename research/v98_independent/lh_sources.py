#!/usr/bin/env python3
"""V98 Independent LH frozen 7-slot source. Only pinned 2023/24 training allowed."""
import numpy as np
from ko_source import load,HOURS,WARMUP
BUDGET=np.array([.74,.10,.08,.06])
PATHS=('LH_core_only','LH_full','LH_minus_opportunity','LH_minus_RV','LH_minus_stress')
NAMES=('Opportunity','Relative_Value','Stress_Recovery')

def bundle(o,h,l,c,q,r,e):
    o,h,l,c,q,r,e=[np.asarray(z,float) for z in (o,h,l,c,q,r,e)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(z.shape!=c.shape or not np.isfinite(z).all() for z in (o,h,l,c,q,r,e)) or
        np.any(o<=0) or np.any(l<=0) or np.any(c<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):raise ValueError('LH_INVALID_SOURCE')
    n=len(c);lc=np.log(c);returns=np.zeros_like(c);returns[1:]=np.diff(lc,axis=0)
    intents=np.zeros((n,4,4));updates=np.zeros((n,4),bool);entries=np.zeros((n,3),bool)
    valid=np.zeros(n,bool);regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,n):
        good=bool(np.all(q[t-167:t+1]>0) and np.all(q[t-23:t+1]>0));valid[t]=good
        r720=lc[t]-lc[t-720];r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24]
        med168=float(np.median(r168));med72=float(np.median(r72));med24=float(np.median(r24))
        stress=med72<-.06;recovery=med168<-.06 and med24>.025
        state='STRESS' if stress else 'RECOVERY' if recovery else 'RISK_ON' if med168>0 else 'RANGE'
        regimes[t]=state
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if (t-WARMUP)%504==0 and good:
            downside=np.sqrt(np.mean(np.minimum(returns[t-335:t+1],0.)**2,axis=0))*np.sqrt(336.)
            eligible=(r720>0)&(r336>0)&(c[t]>np.median(c[t-336:t],axis=0))
            score=r720/np.maximum(.05,downside)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(score[j]),int(j)))
            rows[0]=0.
            if ranked:rows[0,ranked[0]]=.62
            if len(ranked)>1:rows[0,ranked[1]]=.12
            updates[t,0]=True
        if (t-WARMUP)%72==0 and good and state=='RISK_ON' and expiry[1]<0 and 1 not in expired:
            eligible=(r72>.06)&(r24>.02)&(r168>0)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r72,-np.inf)))
                rows[1]=0.;rows[1,j]=.10;expiry[1]=t+72
                updates[t,1]=True;entries[t,0]=True
        if (t-WARMUP)%120==0 and good and state!='STRESS' and expiry[2]<0 and 2 not in expired:
            funding240=np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
            if float(np.max(funding240)-np.min(funding240))>.0025:
                lo=int(np.argmin(funding240));hi=int(np.argmax(funding240))
                rows[2]=0.;rows[2,lo]=.04;rows[2,hi]=-.04
                expiry[2]=t+120;updates[t,2]=True;entries[t,1]=True
        if (t-WARMUP)%72==0 and good and expiry[3]<0 and 3 not in expired:
            if state=='STRESS':
                j=int(np.argmin(r72));rows[3]=0.;rows[3,j]=-.06
                expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
            elif state=='RECOVERY':
                j=int(np.argmax(r24));rows[3]=0.;rows[3,j]=.06
                expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.98+1e-9:raise ValueError('LH_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def static_check():
    n=2400;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+.08*np.sin(t[:,None]/73.+np.arange(4)))
    o=c*(1-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e7);r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[x.copy() for x in (o,h,l,c,q,r)]
    for x in (oo,hh,ll,cc):x[1700:]*=1.7
    qq[1700:]*=3;rr[1700:]=-.002
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:1700],y[:1700]) for x,y in zip(a,b)),'LH_FUTURE_LEAK'
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changes&~a[1][1:]),'LH_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.98+1e-9
    bad=q.copy();bad[700,0]=0.
    assert not bundle(o,h,l,c,bad,r,e)[3][744]
    return True
if __name__=='__main__':
    assert static_check();print('LH_SOURCE_STATIC_CAUSAL_PASS')
