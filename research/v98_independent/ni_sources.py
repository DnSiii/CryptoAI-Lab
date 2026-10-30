#!/usr/bin/env python3
"""V98 NI preregistered trend/volume continuation/dispersion/crash recovery. 2023-24 ONLY."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(8,8,4)
BOOKS={'NI_full':(0,1,2,3),'NI_core_only':(0,),
       'NI_minus_opportunity':(0,2,3),'NI_minus_RV':(0,1,3),
       'NI_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NI_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NI_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NI_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NI_FUNDING_CALENDAR')
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
        if k%336==0:
            if not good:raise ValueError('NI_CORE_ZERO_VOLUME_'+str(t))
            ret336=p[t]-p[t-336]
            ret168=p[t]-p[t-168]
            rms=np.sqrt(np.mean(r[t-167:t+1]**2,axis=0))
            score=np.where(ret336>0,ret336/np.maximum(rms,.001),-np.inf)
            ranking=np.argsort(-score,kind='stable')
            state[0]=0.
            eligible=[int(j) for j in ranking if ret336[j]>0]
            if eligible:
                state[0,eligible[0]]=.32
                if len(eligible)>1:state[0,eligible[1]]=.22
            elif ret168[0]<0:
                state[0,0]=-.30
        if k%168==0:
            if not good:raise ValueError('NI_WEEKLY_ZERO_VOLUME_'+str(t))
            ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72]
            ret24=p[t]-p[t-24]
            ret336=p[t]-p[t-336]
            state[1:]=0.
            # 24h volume confirmation versus the preceding 144h, not future volume.
            recent=q[t-23:t+1].mean(axis=0)
            older=q[t-167:t-23].mean(axis=0)
            eligible=[j for j in (1,2,3) if ret168[j]>0 and ret24[j]>0
                      and recent[j]>older[j]]
            if eligible:
                winner=max(eligible,key=lambda j:(ret72[j],-j))
                state[1,winner]=.14
            alt=np.array([1,2,3])
            leader=int(alt[np.argmax(ret168[1:])])
            laggard=int(alt[np.argmin(ret168[1:])])
            if leader!=laggard and ret168[leader]-ret168[laggard]>=.07 and ret168[0]>0:
                state[2,laggard]=.07
                state[2,leader]=-.07
            if ret168[0]<-.05 and np.count_nonzero(ret168[1:]<0)>=2:
                if ret24[0]<=0:
                    worst=int(alt[np.argmin(ret168[1:])])
                    state[3,worst]=-.12
                else:
                    rebound=int(alt[np.argmax(ret24[1:])])
                    state[3,rebound]=.12
            constructive=ret336[0]>0 and np.count_nonzero(ret168[1:]>0)>=2
            mult[:]=[1.,.75,.75] if constructive else [.7,1.,1.]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy()
        w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NI_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NI_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%336==0:updates[t,0]=True
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
        raise ValueError('NI_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NI_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::336,0]):raise ValueError('NI_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NI_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
