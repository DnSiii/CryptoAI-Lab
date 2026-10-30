#!/usr/bin/env python3
"""V98 NU preregistered 672h risk-adjusted trend, native funding-spread and breadth recovery source."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NU_full':(0,1,2,3),'NU_core_only':(0,),
       'NU_minus_opportunity':(0,2,3),'NU_minus_RV':(0,1,3),
       'NU_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NU_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NU_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NU_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NU_FUNDING_CALENDAR')
    p=np.log(c)
    ret=np.diff(p,axis=0,prepend=p[:1])
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%672==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NU_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r672=p[t]-p[t-672]
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r48=p[t]-p[t-48]
            volatility=np.std(ret[t-167:t+1],axis=0)
            score=np.maximum(r672,0.)/np.maximum(volatility,.001)
            ranking=sorted(range(4),key=lambda j:(-score[j],j))
            if score[ranking[0]]>0:
                held[0,ranking[0]]=.62
                if score[ranking[1]]>0:held[0,ranking[1]]=.18
            elif r672[0]<-.10:
                held[0,0]=-.35
            # Last 21 settled 8h events are observable at t close.
            funding=np.mean(rate[t-160:t+1:8],axis=0)
            median=float(np.median(funding))
            qualified=[j for j in range(4) if r168[j]>0 and funding[j]<median]
            if qualified:
                j=sorted(qualified,key=lambda k:(-r168[k],k))[0]
                held[1,j]=.14
            lowest=sorted(range(4),key=lambda j:(funding[j],j))[0]
            highest=sorted(range(4),key=lambda j:(-funding[j],j))[0]
            if funding[highest]-funding[lowest]>=.00008:
                held[2,lowest]=.10
                held[2,highest]=-.10
            if np.count_nonzero(r336>0)<=1 and r168[0]<0:
                held[3,0]=-.12
            elif r336[0]<-.06 and r48[0]>0:
                held[3,0]=.12
            risk_on=bool(r672[0]>0 and np.count_nonzero(r672>0)>=3)
            held[1:]*=np.array([1.,.8,.5] if risk_on else [.75,1.,1.])[:,None]
            if np.abs(held[0]).sum()>.80+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NU_RAW_BUDGET')
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
        raise ValueError('NU_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NU_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::672]):raise ValueError('NU_MISSING_DECISION')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NU_RISK_ADJUSTED_CARRY_SOURCE_SYNTHETIC_PASS_NOT_PNL')
