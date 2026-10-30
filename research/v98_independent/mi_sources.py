#!/usr/bin/env python3
"""V98 MI immutable preregistered 7-slot joint growth capital competition; TRAINING only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'MI_full':(0,1,2,3),'MI_core_only':(0,),
       'MI_minus_opportunity':(0,2,3),'MI_minus_RV':(0,1,3),
       'MI_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MI_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MI_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MI_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MI_FUNDING_CALENDAR')
    p=np.log(c)
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    raw=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    prior=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        r672=p[t]-p[t-672]
        r336=p[t]-p[t-336]
        r168=p[t]-p[t-168]
        r72=p[t]-p[t-72]
        breadth=int(np.count_nonzero(r168>0))
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                raw[k]=0.
                expiry[k]=-1
                expired.add(k)
        refresh=bool(good and (t-WARMUP)%672==0)
        if refresh:
            raw[0]=0.
            raw[0,0]=.54
        if good and (t-WARMUP)%336==0 and 1 not in expired and expiry[1]<0:
            if r672[0]>0 and r168[0]>0:
                raw[1,0]=.12
                expiry[1]=t+336
                entries[t,0]=True
        if good and (t-WARMUP)%336==0 and 2 not in expired and expiry[2]<0:
            alt=1+int(np.argmax(r672[1:]-r672[0]))
            if r672[alt]>r672[0] and r168[alt]>0 and r672[0]>0:
                raw[2,alt]=.12
                expiry[2]=t+336
                entries[t,1]=True
        if good and (t-WARMUP)%168==0 and 3 not in expired and expiry[3]<0:
            if r336[0]<0 and r72[0]>0 and np.count_nonzero(r72>0)>=2:
                raw[3,0]=.10
                expiry[3]=t+168
                entries[t,2]=True
        w=raw.copy()
        w[1:3]*=.5+breadth/8.
        w[3]*=.5+(4-breadth)/8.
        core_gross=float(np.abs(w[0]).sum())
        optional_gross=float(np.abs(w[1:]).sum())
        if optional_gross>0:
            w[1:]*=min(1.,max(0.,(.88-core_gross)/optional_gross))
        if np.abs(w).sum()>.88+1e-10:raise ValueError('MI_GROSS')
        updates[t]=np.any(np.abs(w-prior)>1e-12,axis=1)
        if refresh:updates[t,0]=True
        target[t]=w
        prior=w
    return target,updates,entries,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[x.copy() for x in (o,h,l,c,q,rate)]
    for x in changed[:4]:x[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MI_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]):
        raise ValueError('MI_SILENT_UPDATE')
    assert np.all(a[1][WARMUP::672,0])
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MI_SYNTHETIC_CAUSALITY_AND_FORCED_REFRESH_PASS')
