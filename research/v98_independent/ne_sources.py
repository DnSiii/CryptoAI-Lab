#!/usr/bin/env python3
"""V98 NE distinct preregistered seven-slot signal source; 2023-24 training only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'NE_full':(0,1,2,3),'NE_core_only':(0,),
       'NE_minus_opportunity':(0,2,3),'NE_minus_RV':(0,1,3),
       'NE_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NE_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NE_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%672==0:
            if not good:raise ValueError('NE_CORE_ZERO_VOLUME_'+str(t))
            ret336=p[t]-p[t-336]
            ret504=p[t]-p[t-504]
            risk=np.sqrt(np.mean(r[t-335:t+1]**2,axis=0))
            score=ret504/np.maximum(risk,.001)
            state[0]=0.
            if ret336[0]>0:
                state[0,0]=.36
                j=1+int(np.argmax(score[1:]))
                state[0,j]=.26
            else:
                state[0,0]=-.32
                j=1+int(np.argmin(score[1:]))
                state[0,j]=-.26
        if k%168==0:
            if not good:raise ValueError('NE_WEEKLY_ZERO_VOLUME_'+str(t))
            ret168=p[t]-p[t-168]
            ret336=p[t]-p[t-336]
            ret72=p[t]-p[t-72]
            ret24=p[t]-p[t-24]
            state[1:]=0.
            accel=ret72[1:]-(72./168.)*ret168[1:]
            jhi=1+int(np.argmax(accel))
            jlo=1+int(np.argmin(accel))
            if accel[jhi-1]>0 and ret168[jhi]>0:
                state[1,jhi]=.12
            elif accel[jlo-1]<0 and ret168[jlo]<0:
                state[1,jlo]=-.12
            settled=rate[t-168:t:8,1:]
            if settled.shape!=(21,3):raise ValueError('NE_SETTLED_FUNDING_LOOKBACK')
            means=np.mean(settled,axis=0)
            cheap=1+int(np.argmin(means))
            expensive=1+int(np.argmax(means))
            if cheap!=expensive and means[expensive-1]-means[cheap-1]>=.000025:
                state[2,cheap]=.07
                state[2,expensive]=-.07
            if ret168[0]<0 and ret24[0]>0:
                state[3,1+int(np.argmax(ret24[1:]))]=.12
            else:
                vol72=float(np.std(r[t-71:t+1,0]))
                vol336=float(np.std(r[t-335:t+1,0]))
                if ret24[0]<0 and vol72>1.15*max(vol336,1e-8):
                    state[3,1+int(np.argmin(ret72[1:]))]=-.12
            constructive=ret336[0]>0 and np.count_nonzero(ret168>0)>=2
            mult[:]=[1.,.85,.85] if constructive else [.75,1.,1.]
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NE_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NE_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
    return target,updates,active,valid

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00007*t*(1+j/4)+.12*np.sin(t/43+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1+.3*np.sin(t/7+j))**2*np.ones_like(c)
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool)
    event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3
    changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NE_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NE_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('NE_FORCED_REFRESH')
    return True

if __name__=='__main__':
    assert synthetic_causality()
    print('NE_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
