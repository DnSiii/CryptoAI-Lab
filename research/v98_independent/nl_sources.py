#!/usr/bin/env python3
"""V98 NL preregistered seven-slot multi-horizon growth engine, 2023-24 only."""
import numpy as np
HOURS=18288; WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(8,8,8)
BOOKS={'NL_full':(0,1,2,3),'NL_core_only':(0,),
       'NL_minus_opportunity':(0,2,3),'NL_minus_RV':(0,1,3),
       'NL_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):raise ValueError('NL_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):raise ValueError('NL_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NL_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NL_FUNDING_CALENDAR')
    p=np.log(c);target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool);active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool);state=np.zeros((4,4));previous=np.zeros((4,4))
    mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP;good=bool(np.all(q[t]>0));valid[t]=good
        if k%336==0:
            if not good:raise ValueError('NL_CORE_ZERO_VOLUME_'+str(t))
            r504=p[t]-p[t-504];r168=p[t]-p[t-168]
            eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0]
            state[0]=0.
            if eligible:
                ranked=sorted(eligible,key=lambda j:(-r504[j],j))
                state[0,ranked[0]]=.54
                if len(ranked)>1:state[0,ranked[1]]=.12
            else:
                worst=sorted(range(4),key=lambda j:(r504[j],j))[0]
                state[0,worst]=-.46
        if k%168==0:
            if not good:raise ValueError('NL_WEEKLY_ZERO_VOLUME_'+str(t))
            r48=p[t]-p[t-48];r168=p[t]-p[t-168];r24=p[t]-p[t-24]
            state[1:]=0.
            longs=[j for j in (1,2,3) if r48[j]>0 and r168[j]>0]
            shorts=[j for j in (1,2,3) if r48[j]<0 and r168[j]<0]
            if longs:state[1,sorted(longs,key=lambda j:(-r48[j],j))[0]]=.14
            elif shorts:state[1,sorted(shorts,key=lambda j:(r48[j],j))[0]]=-.14
            lead=sorted((1,2,3),key=lambda j:(-r168[j],j))[0]
            lag=sorted((1,2,3),key=lambda j:(r168[j],j))[0]
            if lead!=lag:
                state[2,lead]=.055;state[2,lag]=-.055
            if r168[0]<-.02:state[3,0]=-.10
            elif r168[0]>0 and r24[0]>0:state[3,0]=.09
            constructive=int(np.count_nonzero(r168>0))>=3
            mult[:]=[1.,.9,.8] if constructive else [.8,1.,1.]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum());optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NL_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NL_VIRTUAL_GROSS')
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
        raise ValueError('NL_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NL_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::336,0]):raise ValueError('NL_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NL_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
