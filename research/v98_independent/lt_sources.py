#!/usr/bin/env python3
"""V98 LT volatility impulse and dispersion portfolio; prereg 435137f."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LT_core_only','LT_full','LT_minus_opportunity','LT_minus_RV','LT_minus_stress')
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LT_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(q<0) or np.any(np.minimum(o,c)<=0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LT_INVALID_SOURCE')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('LT_FUNDING_EVENTS')
    p=np.log(c);intents=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool);regimes=np.full(HOURS,'RANGE',dtype='<U12')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r504=p[t]-p[t-504];r336=p[t]-p[t-336];r168=p[t]-p[t-168];r24=p[t]-p[t-24]
        m168=float(np.median(r168));m24=float(np.median(r24))
        regimes[t]='RISK_ON' if m168>0 else 'STRESS' if m168<0 and m24<0 else 'RECOVERY' if m168<0 and m24>0 else 'RANGE'
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,168,336,504)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%504==0:
            j=int(np.argmax(r504));rows[0]=0
            if m168>0 and r504[j]>0:rows[0,j]=.74
            updates[t,0]=True
        if good and (t-WARMUP)%96==0:
            if 1 not in expired and expiry[1]<0 and m168>0 and int(np.count_nonzero(r24>0))>=2:
                rows[1]=0;rows[1,int(np.argmax(r24))]=.07
                expiry[1]=t+96;updates[t,1]=True;entries[t,0]=True
            if 2 not in expired and expiry[2]<0 and float(np.ptp(r336))>.08:
                rows[2]=0;rows[2,int(np.argmax(r336))]=.03;rows[2,int(np.argmin(r336))]=-.03
                expiry[2]=t+96;updates[t,2]=True;entries[t,1]=True
            if 3 not in expired and expiry[3]<0 and m24!=0:
                vol24=float(np.std(np.diff(p[t-24:t+1,0])))
                vol168=float(np.std(np.diff(p[t-168:t+1,0])))
                if vol168>0 and vol24>1.1*vol168:
                    rows[3]=0;rows[3,0]=-.06 if m24<0 else .06
                    expiry[3]=t+96;updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.93+1e-9:raise ValueError('LT_HIDDEN_GROSS')
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
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LT_FUTURE_LEAK'
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changes&~a[1][1:]),'LT_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.93+1e-9
    return True
if __name__=='__main__':
    assert synthetic_causality();print('LT_SYNTHETIC_CAUSALITY_PASS')
