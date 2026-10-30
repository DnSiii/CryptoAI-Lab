#!/usr/bin/env python3
"""V98 NF preregistered distinct long-biased cross-sectional seven-slot signals. TRAINING ONLY."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'NF_full':(0,1,2,3),'NF_core_only':(0,),
       'NF_minus_opportunity':(0,2,3),'NF_minus_RV':(0,1,3),
       'NF_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NF_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NF_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NF_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NF_FUNDING_CALENDAR')
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
            if not good:raise ValueError('NF_CORE_ZERO_VOLUME_'+str(t))
            ret504=p[t]-p[t-504]
            rms=np.sqrt(np.mean(r[t-167:t+1]**2,axis=0))
            score=ret504/np.maximum(rms,.001)
            ranking=np.argsort(-score,kind='stable')
            state[0]=0.
            state[0,0]=.14
            if int(np.count_nonzero(ret504>0))>=2:
                state[0,ranking[0]]+=.36
                state[0,ranking[1]]+=.12
            elif ret504[ranking[0]]>0:
                state[0,ranking[0]]+=.24
        if k%168==0:
            if not good:raise ValueError('NF_WEEKLY_ZERO_VOLUME_'+str(t))
            ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72]
            ret24=p[t]-p[t-24]
            state[1:]=0.
            excess=ret72[1:]-ret72[0]
            top=1+int(np.argmax(excess))
            if excess[top-1]>.02 and ret168[top]>0:
                state[1,top]=.14
            leader=1+int(np.argmax(ret168[1:]))
            laggard=1+int(np.argmin(ret168[1:]))
            if leader!=laggard and ret168[leader]-ret168[laggard]>.06:
                state[2,leader]=.06
                state[2,laggard]=-.06
            if ret24[0]<-.025 and ret72[0]<-.035:
                state[3,0]=-.10
            elif ret72[0]<-.035 and ret24[0]>0:
                state[3,1+int(np.argmax(ret24[1:]))]=.10
            constructive=ret168[0]>0 and int(np.count_nonzero(ret168[1:]>0))>=2
            mult[:]=[1.,.8,.7] if constructive else [.75,1.,1.]
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NF_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NF_VIRTUAL_GROSS')
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
        raise ValueError('NF_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NF_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('NF_FORCED_REFRESH')
    return True

if __name__=='__main__':
    assert synthetic_causality()
    print('NF_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
