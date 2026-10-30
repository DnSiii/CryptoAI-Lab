#!/usr/bin/env python3
"""V98 MP: preregistered causal online sleeve productivity allocator. 2023-24 training only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(6,4,2)
BOOKS={'MP_full':(0,1,2,3),'MP_core_only':(0,),
       'MP_minus_opportunity':(0,2,3),'MP_minus_RV':(0,1,3),
       'MP_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MP_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MP_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MP_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MP_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    virtual=np.zeros((HOURS,3))
    raw=np.zeros((4,4))
    prev=np.zeros((4,4))
    due=np.full(4,-1,int)
    last_rate=np.zeros(4)
    breadth=0
    vol_ratio=1.
    productivity=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if t>WARMUP:
            simple=c[t]/c[t-1]-1.
            virtual[t]=np.sum(raw[1:]*simple[None,:],axis=1)
        expired=set()
        for slot in (1,2,3):
            if due[slot]>=0 and t>=due[slot]:
                raw[slot]=0.
                due[slot]=-1
                expired.add(slot)
        if k%672==0:
            if not good:raise ValueError('MP_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            raw[0]=[.69 if p[t,0]-p[t-336,0]>0 else .62,0,0,0]
        if k%168==0:
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            breadth=int(np.count_nonzero(r168>0))
            v72=float(np.std(r[t-71:t+1,0]))
            v336=float(np.std(r[t-335:t+1,0]))
            vol_ratio=v72/max(v336,1e-8)
            if good and 1 not in expired and due[1]<0 and r168[0]>0:
                candidates=[j for j in (1,2,3) if r168[j]>r168[0] and r72[j]>0 and r24[j]>0]
                if candidates:
                    j=max(candidates,key=lambda z:(float(r168[z]-r168[0]),-z))
                    raw[1,j]=.14
                    due[1]=t+168
                    entries[t,0]=True
            if good and 2 not in expired and due[2]<0:
                x=r[t-335:t+1,0]
                xc=x-x.mean()
                den=max(float(np.dot(xc,xc)),1e-8)
                beta=np.array([float(np.dot(xc,r[t-335:t+1,j]-np.mean(r[t-335:t+1,j]))/den)
                               for j in (1,2,3)])
                residual=r168[1:]-beta*r168[0]
                long=int(1+np.argmax(residual))
                short=int(1+np.argmin(residual))
                if (long!=short and residual[long-1]-residual[short-1]>.06
                    and r24[long]>r24[short]
                    and last_rate[long]-last_rate[short]<=.0002):
                    raw[2,long]=.07
                    raw[2,short]=-.04
                    due[2]=t+168
                    entries[t,1]=True
            if (good and 3 not in expired and due[3]<0 and r168[0]<0
                and r24[0]>0 and breadth<=2):
                raw[3,0]=.09
                due[3]=t+168
                entries[t,2]=True
            if k>=672:
                # t-close virtual return known; entry tax only on PAST activations.
                scores=np.sum(virtual[t-671:t+1],axis=0)-.002*np.sum(entries[t-672:t],axis=0)
                productivity=np.where(scores>0,1.,.25)
        w=raw.copy()
        w[1]*=(1. if breadth>=2 else .6)*productivity[0]
        w[2]*=(1. if vol_ratio<=1.5 else .6)*productivity[1]
        w[3]*=(1. if breadth<=1 else .7)*productivity[2]
        core=float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if core>.89:raise ValueError('MP_CORE_GROSS')
        if optional>0:w[1:]*=min(1.,max(0.,(.89-core)/optional))
        if float(np.abs(w).sum())>.89+1e-10:raise ValueError('MP_GROSS')
        updates[t]=np.any(np.abs(w-prev)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        prev=w
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
        raise ValueError('MP_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MP_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MP_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MP_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
