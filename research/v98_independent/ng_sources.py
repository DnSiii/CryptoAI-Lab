#!/usr/bin/env python3
"""V98 NG preregistered funding-squeeze, two-winner and compression-breakout signals; TRAINING ONLY."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(10,12,4)
BOOKS={'NG_full':(0,1,2,3),'NG_core_only':(0,),
       'NG_minus_opportunity':(0,2,3),'NG_minus_RV':(0,1,3),
       'NG_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NG_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NG_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NG_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NG_FUNDING_CALENDAR')
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4));previous=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0));valid[t]=good
        if k%672==0:
            if not good:raise ValueError('NG_CORE_ZERO_VOLUME_'+str(t))
            ret504=p[t]-p[t-504]
            downside=np.sqrt(np.mean(np.minimum(r[t-335:t+1],0)**2,axis=0))
            score=ret504/np.maximum(downside,.001)
            ranking=np.argsort(-score,kind='stable')
            state[0]=0.
            if ret504[ranking[0]]>0:state[0,ranking[0]]=.42
            if ret504[ranking[0]]>0 and ret504[ranking[1]]>0:
                state[0,ranking[1]]=.22
        if k%168==0:
            if not good:raise ValueError('NG_WEEKLY_ZERO_VOLUME_'+str(t))
            ret504=p[t]-p[t-504];ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72];ret24=p[t]-p[t-24]
            state[1:]=0.
            vol72=np.std(r[t-71:t+1],axis=0)
            vol336=np.std(r[t-335:t+1],axis=0)
            eligible=(ret168>.05)&(ret24>0)&(vol72<.90*np.maximum(vol336,1e-8))
            if np.any(eligible):
                scores=np.where(eligible,ret168,-np.inf)
                state[1,int(np.argmax(scores))]=.14
            settled=rate[t-168:t:8]
            if settled.shape!=(21,4):raise ValueError('NG_SETTLED_FUNDING_LOOKBACK')
            carry=np.mean(settled[:,1:],axis=0)
            cheap=1+int(np.argmin(carry));dear=1+int(np.argmax(carry))
            if cheap!=dear and carry[dear-1]-carry[cheap-1]>=.00003:
                state[2,cheap]=.06;state[2,dear]=-.06
            btc_carry=float(np.mean(settled[:,0]))
            if ret72[0]<-.03 and btc_carry>0:
                state[3,0]=-.12
            elif ret72[0]<-.03 and ret24[0]>0 and btc_carry<=0:
                state[3,0]=.12
            constructive=int(np.count_nonzero(ret504>0))>=2 and ret168[0]>0
            mult[:]=[1.,.8,.7] if constructive else [.7,1.,1.]
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NG_CORE_GROSS')
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NG_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w;previous=w
    return target,updates,active,valid

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00007*t*(1+j/4)+.12*np.sin(t/43+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1+.3*np.sin(t/7+j))**2*np.ones_like(c)
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NG_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NG_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('NG_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NG_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
