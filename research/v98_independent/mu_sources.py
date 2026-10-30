#!/usr/bin/env python3
"""V98 MU frozen seven-slot source. Authenticated 2023-24 training only, no PnL."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(4,4,2)
BOOKS={'MU_full':(0,1,2,3),'MU_core_only':(0,),
       'MU_minus_opportunity':(0,2,3),'MU_minus_RV':(0,1,3),
       'MU_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MU_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MU_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MU_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MU_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    due=np.full(4,-1,int)
    last_rate=np.zeros(4)
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        expired=set()
        for slot in (1,2,3):
            if due[slot]>=0 and t>=due[slot]:
                state[slot]=0.
                due[slot]=-1
                expired.add(slot)
        if k%672==0:
            if not good:raise ValueError('MU_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            trend=p[t]-p[t-336]
            state[0]=0.
            if trend[0]>0 and trend[1]>0:
                state[0,0]=.46;state[0,1]=.22
            elif trend[0]>0:state[0,0]=.68
            elif trend[1]>0:state[0,0]=.28;state[0,1]=.36
            else:state[0,0]=.45;state[0,1]=.10
        if k%168==0:
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            leader=int(2+np.argmax(r168[2:]))
            if (good and 1 not in expired and due[1]<0 and
                c[t,leader]>np.max(c[t-168:t,leader]) and
                r72[leader]>.035 and r168[0]>-.03):
                state[1,leader]=.16
                due[1]=t+168
                entries[t,0]=True
            cross=r24[1:]
            weak=int(1+np.argmin(cross))
            strong=int(1+np.argmax(cross))
            if (good and 2 not in expired and due[2]<0 and weak!=strong and
                r24[strong]-r24[weak]>.055 and
                r168[weak]>0 and r168[strong]>0 and
                last_rate[weak]-last_rate[strong]<=.0002):
                state[2,weak]=.075;state[2,strong]=-.060
                due[2]=t+168
                entries[t,1]=True
            if (good and 3 not in expired and due[3]<0 and
                r72[0]<-.055 and r24[0]<0 and np.count_nonzero(r168<0)>=3):
                state[3,0]=-.13
                due[3]=t+168
                entries[t,2]=True
            constructive=bool(r168[0]>0 and np.count_nonzero(r168>0)>=2)
            factors[:]=[1.,.85,.60] if constructive else [.55,.70,1.]
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.5:
                factors[0]*=.5
                factors[2]=1.
        w=state.copy()
        for slot in (1,2,3):w[slot]*=factors[slot-1]
        remaining=.84-float(np.abs(w[0]).sum())
        if remaining<0:raise ValueError('MU_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>remaining and optional>0:w[1:]*=remaining/optional
        if float(np.abs(w).sum())>.84+1e-10:raise ValueError('MU_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
        if np.any(event[t]):last_rate=np.where(event[t],rate[t],last_rate)
    return target,updates,entries,valid
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
        raise ValueError('MU_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MU_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MU_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MU_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
