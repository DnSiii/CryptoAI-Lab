#!/usr/bin/env python3
"""V98 NQ raw seven-slot causal source. Independent of rejected NP candidates."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NQ_full':(0,1,2,3),'NQ_core_only':(0,),
       'NQ_minus_opportunity':(0,2,3),'NQ_minus_RV':(0,1,3),
       'NQ_minus_stress':(0,1,2)}
MINIMUM=(8,8,8)
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NQ_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NQ_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NQ_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NQ_FUNDING_CALENDAR')
    p=np.log(c)
    ret=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%168==0:
            if np.any(q[t]<=0):raise ValueError('NQ_ZERO_VOLUME_DECISION_'+str(t))
            r168=p[t]-p[t-168]
            r24=p[t]-p[t-24]
            held[:]=0.
            core=np.array([.20,.15,.12,.13])
            held[0]=np.where(r168>0,core,0.)
            volatility=np.maximum(np.std(ret[t-167:t+1],axis=0),.01)
            ranks=r24[1:]/volatility[1:]
            best=sorted((1,2,3),key=lambda j:(-ranks[j-1],j))[0]
            worst=sorted((1,2,3),key=lambda j:(ranks[j-1],j))[0]
            held[1,best if ranks[best-1]>0 else worst]=.14 if ranks[best-1]>0 else -.14
            if t%8 or not np.all(event[t-160:t+1:8]):
                raise ValueError('NQ_FUNDING_UNSETTLED_HISTORY')
            carry=rate[t-160:t+1:8].mean(axis=0)
            ranked=sorted(range(4),key=lambda j:(carry[j],j))
            held[2,ranked[0]]=.06
            held[2,ranked[-1]]=-.06
            dd=c[t,0]/float(np.max(c[t-168:t+1,0]))-1.
            if dd<=-.06:
                candidates=[j for j in (1,2,3) if r168[j]>0]
                j=max(candidates,key=lambda j:(r168[j],-j)) if candidates else 0
                held[3,j]=-.10
            else:held[3,0]=.07
            constructive=bool(r168[0]>0 and np.count_nonzero(r168>0)>=2)
            held[1:]*=np.array([1.,.8,.7] if constructive else [.7,1.,1.])[:,None]
            room=.84-float(np.abs(held[0]).sum())
            optional=float(np.abs(held[1:]).sum())
            if room<0:raise ValueError('NQ_CORE_GROSS')
            if optional>room and optional>0:held[1:]*=room/optional
            if np.abs(held).sum()>.84+1e-10:raise ValueError('NQ_RAW_GROSS')
            updates[t]=True
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        target[t]=held
    return target,updates,active
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00005*t*(1+j/5)+.10*np.sin(t/51+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=2.
    changed[5][14000:]*=-1.
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NQ_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NQ_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::168]):raise ValueError('NQ_MISSING_WEEKLY')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NQ_RAW_CAUSAL_SOURCE_SYNTHETIC_PASS_NOT_PNL')
