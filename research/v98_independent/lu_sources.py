#!/usr/bin/env python3
"""V98 LU mutually gated regime-reserve seven-slot source; prereg b734bc2."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LU_core_only','LU_full','LU_minus_opportunity','LU_minus_RV','LU_minus_stress')
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):raise ValueError('LU_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(q<0) or np.any(np.minimum(o,c)<=0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LU_INVALID_SOURCE')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):raise ValueError('LU_FUNDING_EVENTS')
    p=np.log(c);intents=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool);regimes=np.full(HOURS,'CASH',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r504=p[t]-p[t-504];r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        m168=float(np.median(r168));m24=float(np.median(r24))
        regime='RISK_ON' if m168>0 and m24>=0 else 'RANGE' if m168>0 and m24<0 else 'RECOVERY' if m168<0 and m24>0 else 'STRESS' if m168<0 and m24<0 else 'CASH'
        regimes[t]=regime
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,168,504)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if (t-WARMUP)%72==0:
            if m168<=0 and np.any(rows[0]):
                rows[0]=0;updates[t,0]=True
            if good and m168>0 and ((t-WARMUP)%504==0 or not np.any(rows[0])):
                j=int(np.argmax(r504));rows[0]=0
                if r504[j]>0:rows[0,j]=.82
                updates[t,0]=True
            if good:
                if 1 not in expired and expiry[1]<0 and regime=='RECOVERY':
                    rows[1]=0;rows[1,int(np.argmax(r24))]=.12
                    expiry[1]=t+72;updates[t,1]=True;entries[t,0]=True
                if 2 not in expired and expiry[2]<0 and regime=='RANGE':
                    if not np.all(event[t-48:t+1:8]):raise ValueError('LU_NATIVE_FUNDING_MISSING')
                    f=np.mean(rate[t-48:t+1:8],axis=0);lo=int(np.argmin(f));hi=int(np.argmax(f))
                    if lo!=hi and f[hi]>f[lo]:
                        rows[2]=0;rows[2,lo]=.05;rows[2,hi]=-.05
                        expiry[2]=t+72;updates[t,2]=True;entries[t,1]=True
                if 3 not in expired and expiry[3]<0 and regime=='STRESS':
                    rows[3]=0;rows[3,0]=-.12
                    expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.92+1e-9:raise ValueError('LU_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    t=np.arange(HOURS,dtype=float);j=np.arange(4,dtype=float)
    c=100*np.exp(.00008*t[:,None]*(1+j[None,:]/4)+.10*np.sin(t[:,None]/40+j[None,:]))
    o=c*(1-.001*np.sin(t[:,None]/11+j[None,:]));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    changed=[x.copy() for x in (o,h,l,c,q,r)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LU_FUTURE_LEAK'
    changed_rows=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changed_rows&~a[1][1:]),'LU_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.92+1e-9
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LU_SYNTHETIC_CAUSALITY_PASS')
