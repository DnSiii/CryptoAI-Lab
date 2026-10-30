#!/usr/bin/env python3
"""V98 MR frozen shock-recovery, funding-aware rotation and proportional optional allocator."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(6,4,2)
BOOKS={'MR_full':(0,1,2,3),'MR_core_only':(0,),
       'MR_minus_opportunity':(0,2,3),'MR_minus_RV':(0,1,3),
       'MR_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MR_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MR_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MR_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MR_FUNDING_CALENDAR')
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
    vol_ratio=1.
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
            if not good:raise ValueError('MR_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            r168=p[t]-p[t-168]
            vbtc=float(np.std(r[t-167:t+1,0]))
            veth=float(np.std(r[t-167:t+1,1]))
            state[0]=0.
            if r168[1]>0 and r168[1]-r168[0]>.02 and veth<1.35*max(vbtc,1e-8):
                state[0,0]=.50
                state[0,1]=.18
            else:state[0,0]=.68
        if k%168==0:
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            previous24=p[t-24]-p[t-48]
            vol_ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            drawdown=float(p[t,0]-np.max(p[t-335:t+1,0]))
            if (good and 1 not in expired and due[1]<0 and r168[0]>0
                and previous24[0]<0 and r24[0]>0 and r24[0]>previous24[0]):
                state[1,0]=.15
                due[1]=t+168
                entries[t,0]=True
            if good and 2 not in expired and due[2]<0:
                score=r168[1:]-60.*last_rate[1:]
                long=int(1+np.argmax(score))
                short=int(1+np.argmin(score))
                if (long!=short and r168[long]-r168[short]>.06
                    and r168[long]>0 and r168[short]<0
                    and last_rate[long]-last_rate[short]<=.00015):
                    state[2,long]=.07
                    state[2,short]=-.04
                    due[2]=t+168
                    entries[t,1]=True
            if (good and 3 not in expired and due[3]<0 and drawdown<=-.10
                and r72[0]<0 and r24[0]>0 and int(np.count_nonzero(r168<0))>=2):
                state[3,0]=.12
                due[3]=t+168
                entries[t,2]=True
        w=state.copy()
        if vol_ratio>1.4:
            w[1]*=.70
            w[2]*=.70
        else:w[3]*=.80
        core=float(np.abs(w[0]).sum())
        if core>.89:raise ValueError('MR_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>0:
            w[1:]*=min(1.,max(0.,(.89-core)/optional))
        if float(np.abs(w).sum())>.89+1e-10:raise ValueError('MR_GROSS')
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
        raise ValueError('MR_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MR_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MR_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MR_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
