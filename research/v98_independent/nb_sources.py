#!/usr/bin/env python3
"""V98 NB preregistered seven-slot acceleration / funding-velocity / volatility response."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'NB_full':(0,1,2,3),'NB_core_only':(0,),
       'NB_minus_opportunity':(0,2,3),'NB_minus_RV':(0,1,3),
       'NB_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NB_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NB_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NB_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NB_FUNDING_CALENDAR')
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4));previous=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%672==0:
            if not good:raise ValueError('NB_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            ret504=p[t]-p[t-504]
            ret168=p[t]-p[t-168]
            state[0]=0.
            if ret504[0]>0 and np.count_nonzero(ret168[1:]>0)>=2:
                best=1+int(np.argmax(ret504[1:]))
                state[0,0]=.48;state[0,best]=.22
            else:
                calm=1+int(np.argmin(np.std(r[t-167:t+1,1:],axis=0)))
                state[0,0]=-.32;state[0,calm]=.12
        if k%168==0:
            if not good:raise ValueError('NB_WEEKLY_ZERO_VOLUME_'+str(t))
            ret504=p[t]-p[t-504]
            ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72]
            state[1:]=0.
            acceleration=ret72[1:]/72.-ret168[1:]/168.
            if ret168[0]>0:
                eligible=np.flatnonzero((ret72[1:]>0)&(acceleration>0))
                if len(eligible):
                    j=int(1+eligible[np.argmax(acceleration[eligible])])
                    state[1,j]=.14
            elif ret168[0]<0:
                eligible=np.flatnonzero((ret72[1:]<0)&(acceleration<0))
                if len(eligible):
                    j=int(1+eligible[np.argmin(acceleration[eligible])])
                    state[1,j]=-.14
            # Two simultaneous legs, ranking *change* in signed funding pressure.
            recent=np.mean(rate[t-48:t+1:8,1:],axis=0)
            older=np.mean(rate[t-104:t-55:8,1:],axis=0)
            velocity=recent-older
            cheap=1+int(np.argmin(velocity))
            rich=1+int(np.argmax(velocity))
            if cheap!=rich and float(np.max(velocity)-np.min(velocity))>.00001:
                state[2,cheap]=.07;state[2,rich]=-.07
            btc72=float(ret72[0])
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.20:
                if btc72<0:state[3,0]=-.12
                elif btc72>0:state[3,0]=.12
            constructive=ret504[0]>0 and np.count_nonzero(ret168[1:]>0)>=2
            mult[:]=[1.,.85,.70] if constructive else [.80,1.,1.]
            if ratio>1.5:mult[0]*=.5;mult[2]=1.
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('NB_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NB_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w;previous=w
    return target,updates,active,valid
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
        raise ValueError('NB_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NB_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('NB_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NB_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
