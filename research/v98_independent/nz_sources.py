#!/usr/bin/env python3
"""V98 NZ NEW 2023-24 causal seven-slot raw sources. Never imports rejected candidates."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=336
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"NZ_full":(0,1,2,3),"NZ_core_only":(0,),
       "NZ_minus_opportunity":(0,2,3),"NZ_minus_RV":(0,1,3),
       "NZ_minus_stress":(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError("NZ_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("NZ_SOURCE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("NZ_SOURCE_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("NZ_FUNDING_CALENDAR")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),dtype=bool)
    active=np.zeros((HOURS,3),dtype=bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError("NZ_BAD_DECISION_CALENDAR_"+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r84=p[t]-p[t-84]
            r48=p[t]-p[t-48]
            r24=p[t]-p[t-24]
            eligible=sorted((j for j in range(4) if r336[j]>0 and r84[j]>0),
                            key=lambda j:(-r336[j],j))
            if eligible:
                held[0,eligible[0]]=.58
                if len(eligible)>1:held[0,eligible[1]]=.18
            elif np.count_nonzero(r336<0)>=3:
                held[0,0]=-.55
            recent=np.mean(q[t-47:t+1],axis=0)
            prior=np.mean(q[t-335:t-47],axis=0)
            volume_ratio=recent/np.maximum(prior,1e-12)
            candidates=[j for j in range(4) if r48[j]>.025 and r24[j]>.005 and volume_ratio[j]>1.35]
            if candidates:
                j=min(candidates,key=lambda k:(-r48[k]*volume_ratio[k],k))
                held[1,j]=.16
            alt=(1,2,3)
            weakest=min(alt,key=lambda j:(r336[j],j))
            strongest=min(alt,key=lambda j:(-r336[j],j))
            if weakest!=strongest and r336[strongest]-r336[weakest]>.12:
                held[2,weakest]=.11
                held[2,strongest]=-.11
            if np.count_nonzero(r168<0)>=3:
                if r24[0]<-.03:held[3,0]=-.14
                elif r24[0]>.015 and r168[0]<-.04:held[3,0]=.14
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=2)
            held[1:]*=np.array([1.,.65,.55] if risk_on else [.70,1.,1.])[:,None]
            if np.any(np.abs(held).sum(axis=1)>.84+1e-10):
                raise ValueError("NZ_RAW_MODULE_BUDGET")
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
        raise ValueError("NZ_FUTURE_LEAK")
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError("NZ_SILENT_CHANGE")
    if not np.all(a[1][WARMUP::STEP]):
        raise ValueError("NZ_MISSING_DECISION")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("NZ_NEW_SOURCE_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
