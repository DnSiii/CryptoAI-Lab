#!/usr/bin/env python3
"""V98 MA frozen seven-slot capital/carry/recovery source. TRAINING ONLY, no PnL."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'MA_full':(0,1,2,3),'MA_core_only':(0,),
       'MA_minus_opportunity':(0,2,3),'MA_minus_RV':(0,1,3),
       'MA_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('MA_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('MA_NONFINITE')
    if np.any(q<0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('MA_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MA_NATIVE_FUNDING_CALENDAR')
    p=np.log(c)
    intents=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    regimes=np.full(HOURS,'BEAR',dtype='<U5')
    rows=np.zeros((4,4))
    prev=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r672=p[t]-p[t-672]
        r168=p[t]-p[t-168]
        r48=p[t]-p[t-48]
        r24=p[t]-p[t-24]
        breadth=int(np.count_nonzero(r168>0))
        regimes[t]='BULL' if breadth>=3 else 'MIXED' if breadth>=1 else 'BEAR'
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,48,168,504,672)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.
                expiry[k]=-1
                expired.add(k)
        if (t-WARMUP)%504==0 and good:
            core=np.zeros(4)
            if breadth:
                rank=np.argsort(-r672,kind='stable')
                w=(.50,.25) if breadth>=3 else (.36,.14)
                for j,v in zip(rank[:2],w):
                    if r672[j]>0:core[j]=v
            rows[0]=core
        if (t-WARMUP)%168==0 and good and 1 not in expired and expiry[1]<0 and breadth>=2:
            eligible=np.flatnonzero(r672>0)
            if len(eligible):
                acceleration=r48-r168/3.
                j=int(eligible[np.argmax(acceleration[eligible])])
                if acceleration[j]>0:
                    rows[1,j]=.10
                    expiry[1]=t+168
                    entries[t,0]=True
        if (t-WARMUP)%336==0 and good and 2 not in expired and expiry[2]<0 and breadth>=2:
            slot=(t//8)*8
            funding_mean=np.mean(rate[slot-56:slot+1:8],axis=0)
            rank=np.argsort(funding_mean,kind='stable')
            lo,hi=int(rank[0]),int(rank[-1])
            if lo!=hi and funding_mean[hi]>funding_mean[lo]:
                rows[2,lo]=.055
                rows[2,hi]=-.055
                expiry[2]=t+336
                entries[t,1]=True
        if (t-WARMUP)%72==0 and good and 3 not in expired and expiry[3]<0:
            eligible=np.flatnonzero(r24>0)
            if np.count_nonzero(r168<0)>=2 and len(eligible)>=2:
                j=int(eligible[np.argmax(r24[eligible])])
                rows[3,j]=.075
                expiry[3]=t+144
                entries[t,2]=True
        target=rows.copy()
        cg=float(np.abs(target[0]).sum())
        og=float(np.abs(target[1:]).sum())
        if cg>.93+1e-12:raise ValueError('MA_CORE_GROSS')
        if og>0:
            target[1:]*=min(1.,max(0.,(.93-cg)/og))
        if np.abs(target).sum()>.93+1e-9:raise ValueError('MA_TARGET_GROSS')
        updates[t]=np.any(np.abs(target-prev)>1e-12,axis=1)
        intents[t]=target
        prev=target
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6)
    rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool)
    event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[x.copy() for x in (o,h,l,c,q,rate)]
    for x in changed[:4]:x[14000:]*=1.7
    changed[4][14000:]*=3
    changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MA_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]):
        raise ValueError('MA_SILENT_UPDATE')
    return True

if __name__=='__main__':
    assert synthetic_causality()
    print('MA_SYNTHETIC_CAUSALITY_PASS')
