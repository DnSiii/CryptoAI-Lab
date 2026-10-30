#!/usr/bin/env python3
"""MJ preregistered seven-slot V98 architecture; 2023/24 training only, causal t-1."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'MJ_full':(0,1,2,3),'MJ_core_only':(0,),
       'MJ_minus_opportunity':(0,2,3),'MJ_minus_RV':(0,1,3),
       'MJ_minus_stress':(0,1,2)}
MINIMUM=(6,4,2)
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MJ_SOURCE_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MJ_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MJ_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MJ_FUNDING_CALENDAR')
    p=np.log(c)
    targets=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    rows=np.zeros((4,4))
    prior=np.zeros((4,4))
    due=np.full(4,-1,int)
    breadth=0
    for t in range(WARMUP,HOURS):
        good=bool(np.all(q[t]>0))
        valid[t]=good
        elapsed=t-WARMUP
        r336=p[t]-p[t-336]
        r168=p[t]-p[t-168]
        r72=p[t]-p[t-72]
        r24=p[t]-p[t-24]
        expired=set()
        for k in (1,2,3):
            if due[k]>=0 and t>=due[k]:
                rows[k]=0.
                due[k]=-1
                expired.add(k)
        refresh=(elapsed%672==0)
        if refresh:
            if not good:
                raise ValueError('MJ_CORE_SCHEDULED_ZERO_CURRENT_QUOTE_'+str(t))
            rows[0]=0.
            rows[0,0]=.66 if r336[0]>0 else .50
        if elapsed%168==0:
            breadth=int(np.count_nonzero(r168>0))
            if good and 1 not in expired and due[1]<0 and r168[0]>0:
                best=1+int(np.argmax(r336[1:]))
                if r336[best]>0 and r72[best]>0:
                    rows[1,best]=.14
                    due[1]=t+168
                    entries[t,0]=True
            if good and 3 not in expired and due[3]<0 and r168[0]<0 and r24[0]>0:
                rows[3,0]=.08
                due[3]=t+168
                entries[t,2]=True
        if elapsed%336==0 and good and 2 not in expired and due[2]<0:
            best=1+int(np.argmax(r336[1:]))
            worst=1+int(np.argmin(r336[1:]))
            if best!=worst and r336[best]-r336[worst]>.12 and r168[best]>0:
                rows[2,best]=.055
                rows[2,worst]=-.055
                due[2]=t+336
                entries[t,1]=True
        w=rows.copy()
        w[1]*=1. if breadth>=3 else .7
        w[2]*=1. if breadth>=2 else .6
        w[3]*=1.2 if breadth<=1 else .7
        core=float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if core>.88:raise ValueError('MJ_CORE_GROSS')
        if optional>0:
            w[1:]*=min(1.,max(0.,(.88-core)/optional))
        if float(np.abs(w).sum())>.88+1e-10:raise ValueError('MJ_GROSS')
        updates[t]=np.any(np.abs(w-prior)>1e-12,axis=1)
        if refresh:updates[t,0]=True
        targets[t]=w
        prior=w
    return targets,updates,entries,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6)
    rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool)
    event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3
    changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MJ_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MJ_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):
        raise ValueError('MJ_MISSING_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MJ_SYNTHETIC_CAUSALITY_AND_27_FORCED_REFRESH_PASS')
