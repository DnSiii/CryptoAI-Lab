#!/usr/bin/env python3
"""V98 LS seven-slot asymmetric regime bundle; frozen prereg 57930eb."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LS_core_only','LS_full','LS_minus_opportunity','LS_minus_RV','LS_minus_stress')

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LS_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(q<0) or np.any(np.minimum(o,c)<=0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LS_INVALID_SOURCE')
    if np.any(event[::8]!=True) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('LS_NATIVE_FUNDING_EVENTS')
    p=np.log(c)
    intents=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool)
    regimes=np.full(HOURS,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r672=p[t]-p[t-672];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        m168=float(np.median(r168));m72=float(np.median(r72));m24=float(np.median(r24))
        regimes[t]='RISK_ON' if m168>0 else 'STRESS' if m168<0 and m24<0 else 'RECOVERY' if m168<0 and m24>0 else 'RANGE'
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,72,168,672)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%672==0:
            j=int(np.argmax(r672));rows[0]=0
            if m168>0 and r672[j]>0:rows[0,j]=.72
            updates[t,0]=True
        if good and (t-WARMUP)%168==0:
            if 1 not in expired and expiry[1]<0 and m168>0 and m72<0 and m24>0:
                j=int(np.argmax(r168))
                if r168[j]>0:
                    rows[1]=0;rows[1,j]=.08;expiry[1]=t+168
                    updates[t,1]=True;entries[t,0]=True
            if 2 not in expired and expiry[2]<0 and abs(m168)<=.035:
                if not np.all(event[t-48:t+1:8]):raise ValueError('LS_NATIVE_FUNDING_MISSING')
                f=np.mean(rate[t-48:t+1:8],axis=0)
                lo=int(np.argmin(f));hi=int(np.argmax(f))
                if lo!=hi and f[hi]>f[lo] and abs(r168[lo]-r168[hi])<=.12:
                    rows[2]=0;rows[2,lo]=.025;rows[2,hi]=-.025
                    expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
            if 3 not in expired and expiry[3]<0 and m168<0:
                if m24<0:
                    rows[3]=0;rows[3,0]=-.06
                    expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
                elif m24>0:
                    rows[3]=0;rows[3,int(np.argmax(r24))]=.06
                    expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.91+1e-9:raise ValueError('LS_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    t=np.arange(HOURS,dtype=float);j=np.arange(4,dtype=float)
    c=100*np.exp(.00008*t[:,None]*(1+j[None,:]/4)+.10*np.sin(t[:,None]/40+j[None,:]))
    o=c*(1-.001*np.sin(t[:,None]/11+j[None,:]));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[x.copy() for x in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[14000:]*=1.7
    qq[14000:]*=3;rr[14000:]*=-1
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LS_FUTURE_LEAK'
    changed=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changed&~a[1][1:]),'LS_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.91+1e-9
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LS_SYNTHETIC_CAUSALITY_PASS')
