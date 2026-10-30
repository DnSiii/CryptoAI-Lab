#!/usr/bin/env python3
"""V98 NN preregistered signed BTC/SOL trend, lagged funding carry, crisis router."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(8,8,8)
BOOKS={'NN_full':(0,1,2,3),'NN_core_only':(0,),
       'NN_minus_opportunity':(0,2,3),'NN_minus_RV':(0,1,3),
       'NN_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NN_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NN_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NN_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NN_FUNDING_CALENDAR')
    p=np.log(c)
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    multipliers=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%336==0:
            if not good:raise ValueError('NN_CORE_ZERO_VOLUME_'+str(t))
            r336=p[t]-p[t-336]
            if r336[0]>0 and r336[3]>0:
                state[0]=[.36,.08,.04,.24]
            elif r336[0]>0:
                state[0]=[.40,.12,.06,.08]
            else:
                state[0]=[-.20,-.06,-.04,-.10]
        if k%168==0:
            if not good:raise ValueError('NN_WEEKLY_ZERO_VOLUME_'+str(t))
            r24=p[t]-p[t-24]
            r72=p[t]-p[t-72]
            r168=p[t]-p[t-168]
            state[1:]=0.
            leader=sorted((1,2,3),key=lambda j:(-r72[j],j))[0]
            laggard=sorted((1,2,3),key=lambda j:(r72[j],j))[0]
            if r72[leader]>=0:state[1,leader]=.14
            else:state[1,laggard]=-.14
            # The 21 events (t-168,t] have settled by this hourly close.
            if t%8!=0 or not np.all(event[t-160:t+1:8]):
                raise ValueError('NN_FUNDING_HISTORY_NOT_SETTLED')
            carry=np.mean(rate[t-160:t+1:8],axis=0)
            ranking=sorted(range(4),key=lambda j:(carry[j],j))
            state[2,ranking[0]]=.05
            state[2,ranking[-1]]=-.05
            state[3,0]=.10 if r24[0]>0 and r168[0]>0 else -.10
            constructive=(r168[0]>0 and np.count_nonzero(r168>0)>=2)
            multipliers[:]=[1.,1.,.8] if constructive else [.7,1.,1.]
            active[t]=np.any(np.abs(state[1:])>1e-12,axis=1)
        w=state.copy()
        w[1:]*=multipliers[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NN_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NN_VIRTUAL_GROSS')
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
        raise ValueError('NN_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NN_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::336,0]):raise ValueError('NN_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NN_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
