#!/usr/bin/env python3
"""V98 MX frozen seven-slot leadership / low-carry / breadth strategy. Training 2023-24 only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'MX_full':(0,1,2,3),'MX_core_only':(0,),
       'MX_minus_opportunity':(0,2,3),'MX_minus_RV':(0,1,3),
       'MX_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MX_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MX_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MX_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MX_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active_weeks=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%672==0:
            if not good:raise ValueError('MX_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            r336=p[t]-p[t-336]
            v=np.std(r[t-335:t+1,1:4],axis=0)*np.sqrt(336.)
            scores=r336[1:4]/np.maximum(v,.03)
            leader=int(1+np.argmax(scores))
            state[0]=0.
            if r336[0]>0 and r336[leader]>0:
                state[0,0]=.48
                state[0,leader]=.24
            else:
                state[0,0]=.46
                state[0,1]=.10
        if k%168==0:
            if not good:raise ValueError('MX_WEEKLY_ZERO_VOLUME_'+str(t))
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            r336btc=p[t,0]-p[t-336,0]
            state[1:]=0.
            eligible=np.flatnonzero((r168[1:4]>0)&(r24[1:4]<0))+1
            if len(eligible):
                leader=int(eligible[np.argmin(r24[eligible])])
                state[1,leader]=.12
            carry=np.mean(rate[t-160:t+1:8,1:4],axis=0)
            lowcarry=int(1+np.argmin(carry))
            highcarry=int(1+np.argmax(carry))
            if r168[lowcarry]>0:
                state[2,lowcarry]=.08
            elif r168[highcarry]<0:
                state[2,highcarry]=-.07
            if np.count_nonzero(r72<0)>=3:
                if r24[0]>0:state[3,3]=.10
                else:state[3,1]=-.08
            constructive=bool(r336btc>0 and np.count_nonzero(r168>0)>=2)
            factors[:]=[1.,.9,.6] if constructive else [.8,1.,1.]
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.5:
                factors[0]*=.6
                factors[2]=1.
            active_weeks[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        for slot in (1,2,3):w[slot]*=factors[slot-1]
        remaining=.84-float(np.abs(w[0]).sum())
        if remaining<0:raise ValueError('MX_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>remaining and optional>0:w[1:]*=remaining/optional
        if float(np.abs(w).sum())>.84+1e-10:raise ValueError('MX_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
    return target,updates,active_weeks,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6)
    rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3
    changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MX_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MX_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MX_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MX_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
