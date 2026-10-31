#!/usr/bin/env python3
"""OQ funding-dislocation cross-sectional source, preregistered, 2023-24 training only."""
import numpy as np
from od_sources import load_oi
HOURS=18288
WARMUP=744
STEP=168
BOOKS={"OQ_full":(0,1,2,3),"OQ_core_only":(0,),
       "OQ_minus_opportunity":(0,2,3),"OQ_minus_RV":(0,1,3),
       "OQ_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
def state(r168):
    if np.count_nonzero(r168>0)>=3:return "positive"
    if np.count_nonzero(r168<0)>=3:return "negative"
    return "mixed"
def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):raise ValueError("OQ_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):raise ValueError("OQ_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):raise ValueError("OQ_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):raise ValueError("OQ_FUNDING_CLOCK")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    eligible=np.ones(HOURS,bool) # OQ uses no OI; no imputation.
    previous=np.zeros(4)
    for t in range(WARMUP,HOURS,STEP):
        if t%8 or not np.all(event[t]):raise ValueError("OQ_DECISION_CLOCK")
        r168=p[t]-p[t-168]
        r48=p[t]-p[t-48]
        r24=p[t]-p[t-24]
        carry=rate[t-160:t+1:8].sum(axis=0)
        score=carry+.04*r168
        highest=max(range(4),key=lambda j:(score[j],-j))
        lowest=min(range(4),key=lambda j:(score[j],j))
        held=np.zeros((4,4))
        if score[highest]-score[lowest]>.004 and r168[highest]-r168[lowest]>.025:
            held[0,highest]=-.30
            held[0,lowest]=+.30
        updates[t,0]=not np.array_equal(previous,held[0])
        previous=held[0].copy()
        residual=r48-np.median(r48)
        j=max(range(4),key=lambda x:(abs(residual[x]),-x))
        last3=rate[t-16:t+1:8,j]
        if abs(residual[j])>.07 and np.all(last3*np.sign(residual[j])>0):
            held[1,j]=-.14*np.sign(residual[j])
        if abs(carry[0]-carry[1])>.0025 and abs(r168[0]-r168[1])<.20:
            high=0 if carry[0]>carry[1] else 1
            low=1-high
            held[2,high]=-.09
            held[2,low]=+.09
        if np.count_nonzero(r48<-.05)>=3 and r24[0]<-.04:
            held[3,0]=-.16
        elif np.count_nonzero(r168<-.10)>=3 and r48[0]>.035:
            held[3,0]=+.16
        mult={"positive":(.7,.8,.5),"negative":(1.,1.,1.),"mixed":(1.,1.,.8)}[state(r168)]
        held[1:]*=np.asarray(mult)[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t:]=held
    return raw,updates,active,eligible
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00006*t*(1+j/9)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005
    l=np.minimum(o,c)*.995
    q=1e6*(1+.15*np.sin(t/29+j))
    rate=np.zeros_like(c)
    event=np.zeros_like(c,dtype=bool)
    event[::8]=True
    rate[::8]=np.array([.0001,-.0004,.0008,-.0002])
    oi=np.ones_like(c)
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4
    o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005
    l2=np.minimum(o2,c2)*.995
    q2=q.copy();q2[14000:]*=4
    rate2=rate.copy();rate2[14000:]*=-4
    b=bundle(o2,h2,l2,c2,q2,rate2,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OQ_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if not np.array_equal(a[0],z[0]):raise ValueError("OQ_OI_UNEXPECTED_DEPENDENCY")
    if int(a[1][:,1].sum())!=105:raise ValueError("OQ_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OQ_CAUSAL_SOURCE_PASS_NOT_PNL")
