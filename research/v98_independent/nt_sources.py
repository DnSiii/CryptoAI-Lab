#!/usr/bin/env python3
"""V98 NT preregistered Donchian breakout and dispersion seven-slot source, not NS rescue."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NT_full':(0,1,2,3),'NT_core_only':(0,),
       'NT_minus_opportunity':(0,2,3),'NT_minus_RV':(0,1,3),
       'NT_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NT_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NT_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NT_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NT_FUNDING_CALENDAR')
    p=np.log(c)
    ret=np.diff(p,axis=0,prepend=p[:1])
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%168==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NT_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            high=np.max(h[t-671:t+1],axis=0)
            low=np.min(l[t-671:t+1],axis=0)
            location=np.clip((c[t]-low)/np.maximum(high-low,1e-12),0.,1.)
            strength=(location-.5)*np.maximum(r336,0.)
            candidates=[j for j in range(4) if r336[j]>0 and location[j]>.65]
            if candidates:
                j=sorted(candidates,key=lambda k:(-strength[k],k))[0]
                held[0,j]=.70
            elif r336[0]<-.10 and location[0]<.35:
                held[0,0]=-.35
            r168=p[t]-p[t-168]
            r48=p[t]-p[t-48]
            r24=p[t]-p[t-24]
            qualified=[j for j in range(4) if r168[j]>0 and r24[j]<0 and rate[t,j]<0]
            if qualified:
                j=sorted(qualified,key=lambda k:(-r168[k],k))[0]
                held[1,j]=.16
            relative=r168[1:]-r168[0]
            highest=sorted((1,2,3),key=lambda j:(-relative[j-1],j))[0]
            lowest=sorted((1,2,3),key=lambda j:(relative[j-1],j))[0]
            if relative[highest-1]-relative[lowest-1]>=.10:
                held[2,highest]=.12
                held[2,lowest]=-.12
            vol24=float(np.std(ret[t-23:t+1,0]))
            vol336=float(np.std(ret[t-335:t+1,0]))
            if r24[0]<-.055 and vol24>1.4*vol336:
                held[3,0]=-.14
            elif r168[0]<-.12 and r48[0]>.045:
                held[3,0]=.14
            risk_on=bool(r336[0]>0 and np.count_nonzero(r336>0)>=3)
            held[1:]*=np.array([1.,1.,.5] if risk_on else [.75,.75,1.])[:,None]
            if np.abs(held[0]).sum()>.70+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NT_RAW_BUDGET')
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
        raise ValueError('NT_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NT_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::168]):raise ValueError('NT_MISSING_WEEKLY')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NT_RANGE_BREAKOUT_DISPERSION_SOURCE_SYNTHETIC_PASS_NOT_PNL')
