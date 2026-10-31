#!/usr/bin/env python3
"""OS preregistered signed beta-residual trend seven-slot source; 2023-24 training only."""
import numpy as np
from od_sources import load_oi
HOURS=18288
WARMUP=744
STEP=168
BOOKS={"OS_full":(0,1,2,3),"OS_core_only":(0,),
       "OS_minus_opportunity":(0,2,3),"OS_minus_RV":(0,1,3),
       "OS_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
def state(r336):
    if np.count_nonzero(r336>0)>=3:return "positive"
    if np.count_nonzero(r336<0)>=3:return "negative"
    return "mixed"
def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):raise ValueError("OS_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):raise ValueError("OS_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):raise ValueError("OS_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):raise ValueError("OS_FUNDING_CLOCK")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    eligible=np.ones(HOURS,bool)
    previous=np.zeros(4)
    for t in range(WARMUP,HOURS,STEP):
        if t%8 or not np.all(event[t]):raise ValueError("OS_DECISION_CLOCK")
        r336=p[t]-p[t-336];r168=p[t]-p[t-168]
        r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        residual=r336-.65*r336[0]+.5*r168
        sigma=np.std(np.diff(p[t-336:t+1],axis=0),axis=0)*np.sqrt(336)
        quality=residual/np.maximum(sigma,.03)
        held=np.zeros((4,4))
        if r336[0]>0:
            ranks=sorted(range(4),key=lambda j:(-quality[j],j))
            if quality[ranks[0]]>0:held[0,ranks[0]]=.30
            if quality[ranks[1]]>0:held[0,ranks[1]]=.18
        elif r336[0]<0:
            ranks=sorted(range(4),key=lambda j:(quality[j],j))
            if quality[ranks[0]]<0:held[0,ranks[0]]=-.24
            if quality[ranks[1]]<0:held[0,ranks[1]]=-.14
        updates[t,0]=not np.array_equal(previous,held[0])
        previous=held[0].copy()
        prior_range=np.log(h[t-335:t-167].max(axis=0)/l[t-335:t-167].min(axis=0))
        current_range=np.log(h[t-167:t+1].max(axis=0)/l[t-167:t+1].min(axis=0))
        oldvol=q[t-47:t-23].sum(axis=0)
        newvol=q[t-23:t+1].sum(axis=0)
        candidates=[j for j in range(4) if current_range[j]<.75*prior_range[j]
                    and c[t,j]>h[t-168:t,j].max()
                    and newvol[j]/max(oldvol[j],1e-12)>1.10]
        if candidates:
            j=sorted(candidates,key=lambda k:(-r24[k],k))[0]
            held[1,j]=.18
        relative=r168-.65*r168[0]
        hi=sorted(range(4),key=lambda j:(-relative[j],j))[0]
        lo=sorted(range(4),key=lambda j:(relative[j],j))[0]
        if relative[hi]-relative[lo]>.18 and r24[hi]<0 and r24[lo]>0:
            held[2,lo]=+.10;held[2,hi]=-.10
        if np.count_nonzero(r72<-.10)>=3 and r24[0]>0:held[3,0]=+.18
        elif np.count_nonzero(r72<-.10)>=3 and r24[0]<0:held[3,0]=-.18
        mult={"positive":(1.,.8,.6),"negative":(.5,1.,1.),
              "mixed":(.75,.8,.8)}[state(r336)]
        held[1:]*=np.asarray(mult)[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t:]=held
    return raw,updates,active,eligible
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00006*t*(1+j/9)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=1e6*(1+.15*np.sin(t/29+j));rate=np.zeros_like(c)
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    rate[::8]=np.array([.0001,-.0004,.0008,-.0002])
    oi=np.ones_like(c)
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4
    o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005;l2=np.minimum(o2,c2)*.995
    q2=q.copy();q2[14000:]*=4
    rate2=rate.copy();rate2[14000:]*=-4
    b=bundle(o2,h2,l2,c2,q2,rate2,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OS_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if not np.array_equal(a[0],z[0]):raise ValueError("OS_OI_UNEXPECTED_DEPENDENCY")
    if int(a[1][:,1].sum())!=105:raise ValueError("OS_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OS_CAUSAL_SOURCE_PASS_NOT_PNL")
