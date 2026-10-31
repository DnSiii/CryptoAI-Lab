#!/usr/bin/env python3
"""V98 OA: weekly state-transition sources; new economic hypothesis, training only."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=168
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"OA_full":(0,1,2,3),"OA_core_only":(0,),
       "OA_minus_opportunity":(0,2,3),"OA_minus_RV":(0,1,3),
       "OA_minus_stress":(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError("OA_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("OA_SOURCE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("OA_SOURCE_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("OA_FUNDING_CALENDAR")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),dtype=bool)
    active=np.zeros((HOURS,3),dtype=bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError("OA_BAD_DECISION_CALENDAR_"+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            eligible=sorted((j for j in range(4) if r336[j]>0 and r168[j]>0),
                            key=lambda j:(-r336[j],j))
            if eligible:
                held[0,eligible[0]]=.60
                if len(eligible)>1:held[0,eligible[1]]=.08
            elif r336[0]<0 and np.count_nonzero(r168<0)>=3:
                held[0,0]=-.55
            ups=[j for j in range(4) if r72[j]>.04 and r24[j]>.015]
            downs=[j for j in range(4) if r72[j]<-.05 and r24[j]<-.025]
            if ups:
                j=min(ups,key=lambda k:(-r24[k],k))
                held[1,j]=.16
            elif downs:
                j=min(downs,key=lambda k:(r24[k],k))
                held[1,j]=-.16
            alt=(1,2,3)
            weak=min(alt,key=lambda j:(r168[j],j))
            strong=min(alt,key=lambda j:(-r168[j],j))
            if weak!=strong and r168[strong]-r168[weak]>.10 and r168[strong]>0:
                held[2,strong]=.09
                held[2,weak]=-.09
            if r72[0]<-.05 and np.count_nonzero(r168<0)>=3:
                held[3,0]=-.18
            elif r336[0]<-.08 and r72[0]<0 and r24[0]>.025:
                held[3,0]=.18
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=2)
            held[1:]*=np.array([1.,1.,.45] if risk_on else [.8,.65,1.])[:,None]
            if np.any(np.abs(held).sum(axis=1)>.84+1e-10):
                raise ValueError("OA_RAW_MODULE_BUDGET")
            updates[t]=True
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        raw[t]=held
    return raw,updates,active
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005
    l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=2.
    changed[5][14000:]*=-1.
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError("OA_FUTURE_LEAK")
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError("OA_SILENT_CHANGE")
    if not np.all(a[1][WARMUP::STEP]) or len(np.arange(WARMUP,HOURS,STEP))!=105:
        raise ValueError("OA_MISSING_DECISION")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OA_NEW_WEEKLY_CAUSAL_SOURCE_SYNTHETIC_PASS_NOT_PNL")
