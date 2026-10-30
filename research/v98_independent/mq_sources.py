#!/usr/bin/env python3
"""V98 MQ regime-priority BTC/ETH growth + BTC acceleration + alt dispersion; training only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(6,4,2)
BOOKS={'MQ_full':(0,1,2,3),'MQ_core_only':(0,),
       'MQ_minus_opportunity':(0,2,3),'MQ_minus_RV':(0,1,3),
       'MQ_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MQ_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MQ_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MQ_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MQ_FUNDING_CALENDAR')
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
    breadth=0
    vol_ratio=1.
    btc_positive=False
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
            if not good:raise ValueError('MQ_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            r336=p[t]-p[t-336]
            state[0]=0.
            if r336[1]>0 and r336[1]>r336[0]:
                state[0,0]=.53
                state[0,1]=.17
            else:
                state[0,0]=.70
        if k%168==0:
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            breadth=int(np.count_nonzero(r168>0))
            btc_positive=bool(r168[0]>0)
            vol_ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if good and 1 not in expired and due[1]<0 and btc_positive and r24[0]>0:
                state[1,0]=.14
                due[1]=t+168
                entries[t,0]=True
            if good and 2 not in expired and due[2]<0:
                accel=r72[1:]-(72/168)*r168[1:]
                long=int(1+np.argmax(accel))
                short=int(1+np.argmin(accel))
                if (long!=short and accel[long-1]-accel[short-1]>.04
                    and r72[long]>0 and r72[short]<0
                    and last_rate[long]-last_rate[short]<=.0002):
                    state[2,long]=.065
                    state[2,short]=-.04
                    due[2]=t+168
                    entries[t,1]=True
            if (good and 3 not in expired and due[3]<0 and r168[0]<0
                and r24[0]<0 and int(np.count_nonzero(r168<0))>=2):
                state[3,0]=-.10
                due[3]=t+168
                entries[t,2]=True
        w=state.copy()
        w[1]*=1. if breadth>=2 else .65
        w[2]*=.75 if vol_ratio>1.5 else 1.
        w[3]*=.7 if breadth>=2 else 1.
        core=float(np.abs(w[0]).sum())
        if core>.89:raise ValueError('MQ_CORE_GROSS')
        remaining=.89-core
        priority=(1,2,3) if btc_positive else (3,2,1)
        for slot in priority:
            g=float(np.abs(w[slot]).sum())
            if g>0:
                factor=min(1.,max(0.,remaining/g))
                w[slot]*=factor
                remaining-=g*factor
        if float(np.abs(w).sum())>.89+1e-10:raise ValueError('MQ_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
        if np.any(event[t]):
            last_rate=np.where(event[t],rate[t],last_rate)
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
        raise ValueError('MQ_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MQ_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MQ_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MQ_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
