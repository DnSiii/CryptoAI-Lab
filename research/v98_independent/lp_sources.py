#!/usr/bin/env python3
"""V98 LP seven-slot persistent cross-sectional spread; frozen prereg 64990cf9."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LP_core_only','LP_full','LP_minus_opportunity','LP_minus_RV','LP_minus_stress')

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    n=len(c)
    if n!=HOURS or any(z.shape!=(n,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('LP_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)) or np.any(np.minimum(o,c)<=0) or np.any(q<0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LP_INVALID_INPUT')
    lc=np.log(c);intents=np.zeros((n,4,4));updates=np.zeros((n,4),bool)
    entries=np.zeros((n,3),bool);valid=np.zeros(n,bool);regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,n):
        r720=lc[t]-lc[t-720];r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168];r24=lc[t]-lc[t-24]
        med168=float(np.median(r168));med24=float(np.median(r24))
        regime='RISK_ON' if med168>0 else 'RECOVERY' if med168<0 and med24>0 else 'STRESS' if med168<0 else 'RANGE'
        regimes[t]=regime
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,168,336,720)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%672==0:
            candidates=sorted((int(j) for j in range(4) if r336[j]>0 and r720[j]>0),key=lambda j:(-float(r336[j]),j))
            rows[0]=0
            if candidates:
                rows[0,candidates[0]]=.72
                if len(candidates)>1:rows[0,candidates[1]]=.04
            updates[t,0]=True
        if good and (t-WARMUP)%168==0:
            if 1 not in expired and expiry[1]<0 and np.count_nonzero(r168>0)>=3:
                j=int(np.argmax(r336))
                if r24[j]>.01:
                    rows[1]=0;rows[1,j]=.06;expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
            if 2 not in expired and expiry[2]<0 and regime=='RISK_ON' and np.ptp(r336)>.08:
                j=int(np.argmax(r336));k=int(np.argmin(r336))
                rows[2]=0;rows[2,j]=.04;rows[2,k]=-.04;expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
            if 3 not in expired and expiry[3]<0 and med168<0:
                if med24>0:
                    j=int(np.argmax(r24));rows[3]=0;rows[3,j]=.04;expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
                elif med24<-.03:
                    j=int(np.argmin(r24));rows[3]=0;rows[3,j]=-.04;expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-9:raise ValueError('LP_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    t=np.arange(HOURS,dtype=float);j=np.arange(4,dtype=float)
    c=100*np.exp(.00007*t[:,None]*(1+j[None,:]/4)+.08*np.sin(t[:,None]/33+j[None,:]))
    o=c*(1-.001*np.sin(t[:,None]/11+j[None,:]));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.zeros_like(c);e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[z.copy() for z in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[14000:]*=1.7
    qq[14000:]*=3;rr[14000:]=.001
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LP_FUTURE_LEAK'
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changes&~a[1][1:]),'LP_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-9
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LP_CAUSALITY_PASS')
