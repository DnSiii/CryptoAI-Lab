#!/usr/bin/env python3
"""OP stateful BTC/ETH inventory and three independent sleeves; preregistered before OP PnL."""
import numpy as np
from od_sources import load_oi
HOURS=18288;WARMUP=744;STEP=168
BOOKS={"OP_full":(0,1,2,3),"OP_core_only":(0,),
       "OP_minus_opportunity":(0,2,3),"OP_minus_RV":(0,1,3),
       "OP_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
def state(r672,r168):
    if np.count_nonzero(r672>0)>=3 and r168[0]>=0:return "positive"
    if np.count_nonzero(r672<0)>=3 and r168[0]<0:return "negative"
    return "mixed"
def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):raise ValueError("OP_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):raise ValueError("OP_NOPFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):raise ValueError("OP_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):raise ValueError("OP_FUNDING_CLOCK")
    p=np.log(c);raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);eligible=np.zeros(HOURS,bool)
    leader=-1;prior_core=np.zeros(4)
    for t in range(WARMUP,HOURS,STEP):
        if t%8 or not np.all(event[t]):raise ValueError("OP_DECISIOP_CLOCK")
        r672=p[t]-p[t-672];r168=p[t]-p[t-168];r48=p[t]-p[t-48]
        mode=state(r672,r168)
        released=False
        if leader>=0 and (c[t,leader]<np.min(c[t-168:t,leader]) or r168[leader]<-.08):
            leader=-1;released=True
        if leader<0 and not released:
            candidates=[j for j in range(4) if c[t,j]>np.max(c[t-672:t,j]) and r168[j]>.04]
            if candidates:leader=max(candidates,key=lambda j:(r672[j],-j))
        held=np.zeros((4,4))
        if leader>=0:held[0,leader]=.58
        if leader<0 and r672[0]>.06 and r168[0]>0:held[0,0]=.14
        if leader>=0 and leader!=0 and r672[0]>0 and r168[0]>0:held[0,0]=.12
        updates[t,0]=not np.array_equal(held[0],prior_core)
        prior_core=held[0].copy()
        eligible[t]=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if eligible[t]:
            grow=np.log(oi[t]/oi[t-167])
            volume=q[t-47:t+1].sum(axis=0)/np.maximum(q[t-95:t-47].sum(axis=0),1e-9)
            picks=[j for j in range(4) if r48[j]>.035 and grow[j]>0 and volume[j]>1.10]
            if picks:held[1,max(picks,key=lambda j:(r48[j],-j))]=.14
        carry=rate[t-160:t+1:8].sum(axis=0)
        higher=max((1,2,3),key=lambda j:(carry[j],-j))
        lower=min((1,2,3),key=lambda j:(carry[j],j))
        if carry[higher]-carry[lower]>.004 and np.ptp(r168[1:])<.30:
            held[2,higher]=-.07;held[2,lower]=.07
        if np.count_nonzero(r48<0)>=3 and r48[0]<-.05:held[3,0]=-.16
        elif r168[0]<-.08 and r48[0]>.025:held[3,0]=.12
        mult={"positive":(1.,.75,.5),"negative":(.6,1.,1.),"mixed":(.8,1.,.8)}[mode]
        held[1:]*=np.asarray(mult)[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t:]=held
    return raw,updates,active,eligible
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00005*t*(1+j/9)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=1e6*(1+.15*np.sin(t/29+j))
    rate=np.tile(np.array([[-.0003,.0002,-.0001,.0005]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    oi=np.exp(7+.00001*t*(1+j/5)+.08*np.sin(t/38+j))
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4;o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005;l2=np.minimum(o2,c2)*.995
    q2=q.copy();q2[14000:]*=4;rate2=rate.copy();rate2[14000:]*=-4
    b=bundle(o2,h2,l2,c2,q2,rate2,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OP_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if z[3][WARMUP+168] or np.any(z[0][WARMUP+168,1]):raise ValueError("OP_OI_QUARANTINE")
    if int(a[1][:,1].sum())!=105:raise ValueError("OP_CLOCK_COUNT")
    if not np.any(a[1][:,0]):raise ValueError("OP_NO_CORE_STATE_TRANSITIOPS")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OP_CAUSAL_STATEFUL_SOURCE_PASS_NOT_PNL")
