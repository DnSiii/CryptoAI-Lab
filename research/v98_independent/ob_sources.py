#!/usr/bin/env python3
"""V98 OB independent two-clock raw sources; no rejected alpha imports."""
import numpy as np
HOURS=18288;WARMUP=744;STEP=336;CORE_STEP=672
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"OB_full":(0,1,2,3),"OB_core_only":(0,),
       "OB_minus_opportunity":(0,2,3),"OB_minus_RV":(0,1,3),
       "OB_minus_stress":(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError("OB_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("OB_SOURCE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("OB_SOURCE_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("OB_FUNDING_CALENDAR")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if t%8 or np.any(q[t]<=0) or not np.all(event[t]):
                raise ValueError("OB_DECISION_CALENDAR_"+str(t))
            r672=p[t]-p[t-672]
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r24=p[t]-p[t-24]
            if (t-WARMUP)%CORE_STEP==0:
                held[0]=0.
                elig=sorted((j for j in range(4) if r672[j]>0 and r168[j]>0),
                            key=lambda j:(-r672[j],j))
                if elig:
                    held[0,elig[0]]=.60
                    if len(elig)>1:held[0,elig[1]]=.10
                elif np.count_nonzero(r336<0)>=3:
                    held[0,0]=-.52
                updates[t,0]=True
            held[1:]=0.
            meanrate=np.mean(rate[t-160:t+1:8],axis=0)
            volume=np.mean(q[t-167:t+1],axis=0)/np.maximum(
                np.mean(q[t-335:t-167],axis=0),1e-12)
            longs=[j for j in range(4) if r168[j]>.06 and volume[j]>1.15 and meanrate[j]<.00005]
            shorts=[j for j in range(4) if r168[j]<-.07 and volume[j]>1.15 and meanrate[j]>.0001]
            if longs:
                j=min(longs,key=lambda k:(-r168[k]*volume[k],k));held[1,j]=.16
            elif shorts:
                j=min(shorts,key=lambda k:(r168[k]*volume[k],k));held[1,j]=-.16
            relative=r336-r336[0]
            alt=np.array((1,2,3))
            med=float(np.median(meanrate[alt]))
            strong=min(alt,key=lambda j:(-relative[j],j))
            weak=min(alt,key=lambda j:(relative[j],j))
            if (strong!=weak and relative[strong]>0 and relative[weak]<0
                and relative[strong]-relative[weak]>.10
                and meanrate[strong]<=med and meanrate[weak]>=med):
                held[2,strong]=.10;held[2,weak]=-.10
            if r168[0]<-.08 and np.count_nonzero(r168<0)>=3:
                held[3,0]=-.16
            elif r336[0]<-.10 and r24[0]>.02:
                held[3,0]=.16
            risk_on=bool(r672[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.,.75,.5] if risk_on else [.7,1.,1.])[:,None]
            if np.any(np.abs(held).sum(axis=1)>.84+1e-10):
                raise ValueError("OB_RAW_BUDGET")
            updates[t,1:]=True
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        raw[t]=held
    return raw,updates,active
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=2;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError("OB_FUTURE_LEAK")
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~np.any(a[1][1:],axis=1)):
        raise ValueError("OB_SILENT_CHANGE")
    if int(a[1][:,0].sum())!=27 or int(a[1][:,1].sum())!=53:
        raise ValueError("OB_TWO_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OB_TWO_CLOCK_CAUSAL_SOURCE_SYNTHETIC_PASS_NOT_PNL")
