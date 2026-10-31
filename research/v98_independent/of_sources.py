#!/usr/bin/env python3
"""V98 OF preregistered breadth barbell / OI dislocation / persistent stress source, no PnL."""
import numpy as np
from od_sources import load_oi
HOURS=18288; WARMUP=744; STEP=168; CORE_STEP=672
BOOKS={"OF_full":(0,1,2,3),"OF_core_only":(0,),
       "OF_minus_opportunity":(0,2,3),"OF_minus_RV":(0,1,3),
       "OF_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")

def state(r672,r168):
    if np.count_nonzero(r672>0)>=3 and r168[0]>0:return "positive"
    if np.count_nonzero(r672<0)>=3 and r168[0]<0:return "negative"
    return "mixed"

def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):
        raise ValueError("OF_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("OF_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("OF_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("OF_FUNDING_CLOCK")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);held=np.zeros((4,4));eligible=np.zeros(HOURS,bool)
    for t in range(WARMUP,HOURS,STEP):
        if t%8 or not np.all(event[t]):raise ValueError("OF_DECISION_CALENDAR")
        r672=p[t]-p[t-672];r168=p[t]-p[t-168]
        r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        mode=state(r672,r168)
        if (t-WARMUP)%CORE_STEP==0:
            held[0]=0.
            if mode=="positive":
                j=1+int(np.argmax(r672[1:]))
                held[0,0]=.34;held[0,j]=.24
            elif mode=="negative":
                j=1+int(np.argmin(r672[1:]))
                held[0,0]=-.34;held[0,j]=-.16
            elif r672[0]>0:held[0,0]=.24
            elif r672[0]<0:held[0,0]=-.20
            updates[t,0]=True
        held[1:]=0.
        eligible[t]=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if eligible[t]:
            oi168=np.log(oi[t]/oi[t-167])
            picks=[j for j in range(4) if r72[j]>.035 and r24[j]>0 and oi168[j]>.025]
            if picks:
                j=max(picks,key=lambda k:(r72[k]*oi168[k],-k))
                held[1,j]=.24
            elif r168[0]<-.08 and oi168[0]>.03:
                held[1,0]=-.20
            scores=r168-.5*oi168
            low=int(np.argmin(scores));high=int(np.argmax(scores))
            if low!=high and scores[high]-scores[low]>.075 and oi168[low]>0 and oi168[high]>0:
                held[2,low]=.12;held[2,high]=-.12
            if np.count_nonzero(r168<0)>=3 and r72[0]<-.04:
                held[3,0]=-.24;held[3,1]=-.10
            elif r168[0]<-.12 and r24[0]>.025 and np.count_nonzero(r24>0)>=3:
                held[3,0]=.24
            mult={"positive":(1.,.8,.4),"negative":(.6,.6,1.),"mixed":(.8,1.,.8)}[mode]
            held[1:]*=np.asarray(mult)[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t:]=held
    return raw,updates,active,eligible

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00005*t*(1+j/9)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[-.0003,.0002,-.0001,.0005]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    oi=np.exp(7+.00001*t*(1+j/5)+.08*np.sin(t/38+j))
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4;o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005;l2=np.minimum(o2,c2)*.995
    rate2=rate.copy();rate2[14000:]*=-1
    b=bundle(o2,h2,l2,c2,q,rate2,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OF_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if z[3][WARMUP+168] or np.any(z[0][WARMUP+168,1:]):
        raise ValueError("OF_QUARANTINE_LEAK")
    if int(a[1][:,0].sum())!=27 or int(a[1][:,1].sum())!=105:
        raise ValueError("OF_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OF_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
