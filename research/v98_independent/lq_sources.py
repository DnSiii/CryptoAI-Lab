#!/usr/bin/env python3
"""V98 LQ seven-slot volatility-scaled dual leader; prereg 2c86a036."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LQ_core_only','LQ_full','LQ_minus_opportunity','LQ_minus_RV','LQ_minus_stress')
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):raise ValueError('LQ_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)) or np.any(np.minimum(o,c)<=0) or np.any(q<0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LQ_INVALID_SOURCE')
    p=np.log(c);intents=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool);regimes=np.full(HOURS,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r720=p[t]-p[t-720];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        med168=float(np.median(r168));med24=float(np.median(r24))
        regime='RISK_ON' if med168>0 else 'STRESS' if med168<0 and med24<0 else 'RECOVERY' if med168<0 else 'RANGE'
        regimes[t]=regime
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,72,168,336,720)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%504==0:
            v=np.std(np.diff(p[t-336:t+1],axis=0),axis=0)
            eligible=[j for j in range(4) if r720[j]>0 and v[j]>0]
            ranked=sorted(eligible,key=lambda j:(-float(r720[j]/v[j]),j))
            rows[0]=0
            if ranked:
                rows[0,ranked[0]]=.52
                if len(ranked)>1:rows[0,ranked[1]]=.20
            updates[t,0]=True
        if good and (t-WARMUP)%72==0:
            if 1 not in expired and expiry[1]<0 and med168>0 and np.count_nonzero(r72>0)>=3:
                rows[1]=0;rows[1,int(np.argmax(r72))]=.08;expiry[1]=t+72;updates[t,1]=True;entries[t,0]=True
            if 2 not in expired and expiry[2]<0 and med168>0 and np.ptp(r72)>.05:
                rows[2]=0;rows[2,int(np.argmax(r72))]=.04;rows[2,int(np.argmin(r72))]=-.04
                expiry[2]=t+72;updates[t,2]=True;entries[t,1]=True
            if 3 not in expired and expiry[3]<0 and med168<0:
                if med24<-.015:
                    rows[3]=0;rows[3,0]=-.04;expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
                elif med24>.012:
                    rows[3]=0;rows[3,int(np.argmax(r24))]=.04;expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.92+1e-9:raise ValueError('LQ_HIDDEN_GROSS')
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
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LQ_FUTURE_LEAK'
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changes&~a[1][1:]),'LQ_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.92+1e-9
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LQ_CAUSALITY_PASS')
