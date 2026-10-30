#!/usr/bin/env python3
"""V98 NS persistent leadership seven-slot source, separate from rejected NR/NQ."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NS_full':(0,1,2,3),'NS_core_only':(0,),
       'NS_minus_opportunity':(0,2,3),'NS_minus_RV':(0,1,3),
       'NS_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NS_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NS_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NS_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NS_FUNDING_CALENDAR')
    p=np.log(c)
    ret=np.diff(p,axis=0,prepend=p[:1])
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    incumbent=None
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%336==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NS_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            ranking=sorted(range(4),key=lambda j:(-r336[j],j))
            leader=ranking[0]
            if incumbent is not None and r336[incumbent]>0 and r336[leader]-r336[incumbent]<=.10:
                leader=incumbent
            runner=next(j for j in ranking if j!=leader)
            if r336[leader]>0:
                held[0,leader]=.42
                if r336[runner]>0:held[0,runner]=.24
            incumbent=leader if r336[leader]>0 else None
            r168=p[t]-p[t-168]
            # Last settled native rate is known at the t close.
            qualified=[j for j in range(4) if r168[j]>0 and rate[t,j]<0]
            if qualified:
                chosen=sorted(qualified,key=lambda j:(-r168[j],j))[0]
                held[1,chosen]=.18
            r48=p[t]-p[t-48]
            residual=r48[1:]-r48[0]
            highest=sorted((1,2,3),key=lambda j:(-residual[j-1],j))[0]
            lowest=sorted((1,2,3),key=lambda j:(residual[j-1],j))[0]
            if residual[highest-1]-residual[lowest-1]>=.08:
                held[2,lowest]=.12
                held[2,highest]=-.12
            r72=float(p[t,0]-p[t-72,0])
            vol24=float(np.std(ret[t-23:t+1,0]))
            vol336=float(np.std(ret[t-335:t+1,0]))
            if r72<-.07 and vol24>vol336:
                held[3,0]=-.16
            elif r72<-.07 and p[t,0]-p[t-24,0]>0:
                held[3,0]=.12
            risk_on=bool(r336[0]>0 and np.count_nonzero(r336>0)>=3)
            held[1:]*=np.array([1.,.75,.5] if risk_on else [.75,1.,1.25])[:,None]
            if np.abs(held[0]).sum()>.66+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NS_RAW_BUDGET')
            updates[t]=True
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        raw[t]=held
    return raw,updates,active
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005
    l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    modified=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in modified[:4]:z[14000:]*=1.7
    modified[4][14000:]*=2.
    modified[5][14000:]*=-1.
    b=bundle(*modified,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NS_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NS_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::336]):raise ValueError('NS_MISSING_BIWEEKLY')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NS_PERSISTENT_LEADERSHIP_SOURCE_SYNTHETIC_PASS_NOT_PNL')
