#!/usr/bin/env python3
"""V98 Independent LI frozen breadth-routed seven-slot source; 2023/24 TRAIN ONLY."""
import numpy as np
from ko_source import load,HOURS,WARMUP
BUDGET=np.array([.78,.08,.06,.06])
PATHS=('LI_core_only','LI_full','LI_minus_opportunity','LI_minus_RV','LI_minus_stress')
NAMES=('Opportunity','Relative_Value','Stress_Recovery')

def bundle(o,h,l,c,q,r,e):
    o,h,l,c,q,r,e=[np.asarray(z,float) for z in (o,h,l,c,q,r,e)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(z.shape!=c.shape or not np.isfinite(z).all() for z in (o,h,l,c,q,r,e)) or
        np.any(o<=0) or np.any(l<=0) or np.any(c<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):raise ValueError('LI_INVALID_SOURCE')
    n=len(c);lc=np.log(c)
    intents=np.zeros((n,4,4));updates=np.zeros((n,4),bool);entries=np.zeros((n,3),bool)
    valid=np.zeros(n,bool);regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,n):
        good=bool(np.all(q[t-167:t+1]>0) and np.all(q[t-23:t+1]>0));valid[t]=good
        r720=lc[t]-lc[t-720];r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24]
        med168=float(np.median(r168));med72=float(np.median(r72))
        state='STRESS' if med72<0 else 'RECOVERY' if med168<0 and med72>0 else 'RISK_ON' if med168>0 else 'RANGE'
        regimes[t]=state
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if (t-WARMUP)%504==0 and good:
            eligible=(r720>0)&(r168>0)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(r720[j]+r336[j]),int(j)))
            rows[0]=0.
            if ranked:
                if int(np.sum(r168>0))>=2:
                    rows[0,ranked[0]]=.68
                    if len(ranked)>1:rows[0,ranked[1]]=.10
                else:rows[0,ranked[0]]=.58
            updates[t,0]=True
        if (t-WARMUP)%96==0 and good and state=='RISK_ON' and expiry[1]<0 and 1 not in expired:
            eligible=(r168>0)&(r24>0)
            if np.any(eligible):
                j=int(np.argmax(np.where(eligible,r168,-np.inf)))
                rows[1]=0.;rows[1,j]=.08;expiry[1]=t+96
                updates[t,1]=True;entries[t,0]=True
        if (t-WARMUP)%168==0 and good and state in ('RISK_ON','RECOVERY') and expiry[2]<0 and 2 not in expired:
            f168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            if float(np.max(f168)-np.min(f168))>.0005:
                lo=int(np.argmin(f168));hi=int(np.argmax(f168))
                rows[2]=0.;rows[2,lo]=.03;rows[2,hi]=-.03
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if (t-WARMUP)%96==0 and good and expiry[3]<0 and 3 not in expired:
            if state=='STRESS':
                rows[3]=0.;rows[3,0]=-.06
                expiry[3]=t+96;updates[t,3]=True;entries[t,2]=True
            elif state=='RECOVERY':
                j=int(np.argmax(r72));rows[3]=0.;rows[3,j]=.06
                expiry[3]=t+96;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.98+1e-9:raise ValueError('LI_HIDDEN_GROSS')
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
    assert all(np.array_equal(x[:1700],y[:1700]) for x,y in zip(a,b)),'LI_FUTURE_LEAK'
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changes&~a[1][1:]),'LI_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.98+1e-9
    bad=q.copy();bad[700,0]=0.
    assert not bundle(o,h,l,c,bad,r,e)[3][744]
    return True
if __name__=='__main__':
    assert static_check();print('LI_SOURCE_STATIC_CAUSAL_PASS')
