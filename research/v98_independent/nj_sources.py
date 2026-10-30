#!/usr/bin/env python3
"""V98 NJ preregistered directional rotation, residual reversion, vol shock; 2023-24 only."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(8,8,4)
BOOKS={'NJ_full':(0,1,2,3),'NJ_core_only':(0,),
       'NJ_minus_opportunity':(0,2,3),'NJ_minus_RV':(0,1,3),
       'NJ_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NJ_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NJ_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NJ_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NJ_FUNDING_CALENDAR')
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4));previous=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP;good=bool(np.all(q[t]>0));valid[t]=good
        if k%168==0:
            if not good:raise ValueError('NJ_WEEKLY_ZERO_VOLUME_'+str(t))
            ret336=p[t]-p[t-336];ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72];ret24=p[t]-p[t-24]
            state[:]=0.
            best=int(np.argmax(ret336));worst=int(np.argmin(ret336))
            selected=best if ret336[best]>0 else worst
            state[0,selected]=.52 if ret336[best]>0 else -.45
            others=[j for j in range(4) if j!=selected]
            eligible_long=[j for j in others if ret72[j]>0 and ret168[j]>0]
            eligible_short=[j for j in others if ret72[j]<0 and ret168[j]<0]
            if eligible_long:
                state[1,max(eligible_long,key=lambda j:(ret72[j],-j))]=.16
            elif eligible_short:
                state[1,min(eligible_short,key=lambda j:(ret72[j],j))]=-.16
            residual=ret24[1:]-ret24[0]
            lag=1+int(np.argmin(residual));lead=1+int(np.argmax(residual))
            if lag!=lead and residual[lead-1]-residual[lag-1]>=.05 and (
                residual[lag-1]<-.025 or residual[lead-1]>.025):
                state[2,lag]=.07;state[2,lead]=-.07
            recent=np.sqrt(np.mean(r[t-71:t+1,0]**2))
            prior=np.sqrt(np.mean(r[t-407:t-71,0]**2))
            if recent>1.35*max(prior,1e-8) and abs(ret72[0])>.035:
                if ret24[0]<0:state[3,0]=-.12
                elif ret24[0]>0:state[3,0]=.12
            constructive=np.count_nonzero(ret168>0)>=3
            mult[:]=[1.,.75,.7] if constructive else [.75,1.,1.]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NJ_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NJ_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%168==0:updates[t,0]=True
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
        raise ValueError('NJ_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NJ_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::168,0]):raise ValueError('NJ_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NJ_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
