#!/usr/bin/env python3
"""MK native funding-carry seven-slot source; t-1 decisions, training only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(6,4,2)
BOOKS={'MK_full':(0,1,2,3),'MK_core_only':(0,),
       'MK_minus_opportunity':(0,2,3),'MK_minus_RV':(0,1,3),
       'MK_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MK_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MK_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MK_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MK_FUNDING_CALENDAR')
    p=np.log(c)
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    prior=np.zeros((4,4))
    due=np.full(4,-1,int)
    breadth=0
    for t in range(WARMUP,HOURS):
        elapsed=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if due[k]>=0 and t>=due[k]:
                state[k]=0.
                due[k]=-1
                expired.add(k)
        refresh=elapsed%672==0
        if refresh:
            if not good:raise ValueError('MK_CORE_SCHEDULED_ZERO_QUOTE_'+str(t))
            state[0]=[.72,0.,0.,0.]
        if elapsed%168==0:
            r168=p[t]-p[t-168]
            breadth=int(np.count_nonzero(r168>0))
            if good and 1 not in expired and due[1]<0:
                r336=p[t]-p[t-336]
                r72=p[t]-p[t-72]
                if r336[3]>r336[0] and r72[3]>0 and r168[0]>0:
                    state[1,3]=.10
                    due[1]=t+168
                    entries[t,0]=True
            if good and 3 not in expired and due[3]<0:
                v72=float(np.std(np.diff(p[t-72:t+1,0])))
                v336=float(np.std(np.diff(p[t-336:t+1,0])))
                if v336>0 and v72>1.4*v336 and p[t,0]>p[t-24,0]:
                    state[3,0]=.08
                    due[3]=t+168
                    entries[t,2]=True
        if elapsed%336==0 and good and 2 not in expired and due[2]<0:
            carry=np.mean(rate[t-160:t+1:8,1:4],axis=0)
            low=1+int(np.argmin(carry))
            high=1+int(np.argmax(carry))
            if low!=high and carry[high-1]-carry[low-1]>=.0001:
                state[2,low]=.045
                state[2,high]=-.045
                due[2]=t+336
                entries[t,1]=True
        w=state.copy()
        w[1]*=1. if breadth>=3 else .5
        w[2]*=1. if breadth<=2 else .8
        w[3]*=1. if breadth<=2 else .7
        optional=float(np.abs(w[1:]).sum())
        if optional>0:
            w[1:]*=min(1.,max(0.,(.88-float(np.abs(w[0]).sum()))/optional))
        if np.abs(w).sum()>.88+1e-10:raise ValueError('MK_GROSS')
        updates[t]=np.any(np.abs(w-prior)>1e-12,axis=1)
        if refresh:updates[t,0]=True
        target[t]=w
        prior=w
    return target,updates,entries,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
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
        raise ValueError('MK_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MK_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):
        raise ValueError('MK_MISSING_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MK_CAUSALITY_NATIVE_FUNDING_HISTORY_AND_FORCED_REFRESH_PASS')
