#!/usr/bin/env python3
"""V98 NK fixed regime-switch composed engine signals. TRAINING 2023-24 ONLY."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(8,8,4)
BOOKS={'NK_full':(0,1,2,3),'NK_core_only':(0,),
       'NK_minus_opportunity':(0,2,3),'NK_minus_RV':(0,1,3),
       'NK_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NK_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NK_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NK_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NK_FUNDING_CALENDAR')
    p=np.log(c);target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool);active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool);state=np.zeros((4,4));previous=np.zeros((4,4))
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP;good=bool(np.all(q[t]>0));valid[t]=good
        if k%336==0:
            if not good:raise ValueError('NK_CORE_ZERO_VOLUME_'+str(t))
            r336=p[t]-p[t-336];r168=p[t]-p[t-168]
            topalt=1+int(np.argmax(r336[1:]))
            state[0]=0.
            if r336[0]>0 and np.count_nonzero(r168[1:]>0)>=2:
                state[0,0]=.18;state[0,topalt]=.40
            elif r336[0]<0 and np.count_nonzero(r168[1:]<0)>=2:
                state[0,0]=-.36
                if r336[topalt]>0:state[0,topalt]=.14
            else:
                best=int(np.argmax(r336))
                if r336[best]>0:state[0,best]=.38
                else:state[0,0]=-.35
        if k%168==0:
            if not good:raise ValueError('NK_WEEKLY_ZERO_VOLUME_'+str(t))
            r72=p[t]-p[t-72];r168=p[t]-p[t-168]
            r24=p[t]-p[t-24];r336=p[t]-p[t-336]
            state[1:]=0.
            longs=[j for j in (1,2,3) if r72[j]>0 and r168[j]>0]
            shorts=[j for j in (1,2,3) if r72[j]<0 and r168[j]<0]
            if longs:
                state[1,max(longs,key=lambda j:(r72[j],-j))]=.16
            elif shorts:
                state[1,min(shorts,key=lambda j:(r72[j],j))]=-.16
            lag=1+int(np.argmin(r72[1:]));lead=1+int(np.argmax(r72[1:]))
            if lag!=lead:
                state[2,lag]=.05;state[2,lead]=-.05
            if r168[0]<-.03:
                if r24[0]<0:state[3,0]=-.10
                elif r24[0]>0:state[3,0]=.10
            constructive=r336[0]>0 and np.count_nonzero(r168[1:]>0)>=2
            mult[:]=[1.,.75,.65] if constructive else [.75,1.,1.]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum());optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NK_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NK_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%336==0:updates[t,0]=True
        target[t]=w;previous=w
    return target,updates,active,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00007*t*(1+j/4)+.12*np.sin(t/43+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1+.3*np.sin(t/7+j))**2*np.ones_like(c)
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NK_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NK_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::336,0]):raise ValueError('NK_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NK_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
