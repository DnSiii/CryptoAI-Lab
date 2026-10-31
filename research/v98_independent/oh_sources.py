#!/usr/bin/env python3
"""OH participation-weighted leadership and liquidity stress source, preregistered no PnL."""
import numpy as np
from od_sources import load_oi
HOURS=18288;WARMUP=744;STEP=168;CORE_STEP=672
BOOKS={"OH_full":(0,1,2,3),"OH_core_only":(0,),
       "OH_minus_opportunity":(0,2,3),"OH_minus_RV":(0,1,3),
       "OH_minus_stress":(0,1,2)}
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
def state(r168,v168):
    if np.count_nonzero(r168>0)>=3 and np.median(v168)>1:return "positive"
    if np.count_nonzero(r168<0)>=3 and np.median(v168)>1:return "negative"
    return "mixed"
def bundle(o,h,l,c,q,rate,event,oi):
    o,h,l,c,q,rate,event,oi=[np.asarray(x) for x in (o,h,l,c,q,rate,event,oi)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event,oi)):raise ValueError("OH_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):raise ValueError("OH_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):raise ValueError("OH_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):raise ValueError("OH_FUNDING_CLOCK")
    p=np.log(c);raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);held=np.zeros((4,4));eligible=np.zeros(HOURS,bool)
    for t in range(WARMUP,HOURS,STEP):
        if t%8 or not np.all(event[t]):raise ValueError("OH_DECISION_CLOCK")
        r336=p[t]-p[t-336];r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
        v168=q[t-167:t+1].sum(axis=0)/np.maximum(q[t-335:t-167].sum(axis=0),1e-9)
        v24=q[t-23:t+1].sum(axis=0)/np.maximum(q[t-47:t-23].sum(axis=0),1e-9)
        mode=state(r168,v168)
        if (t-WARMUP)%CORE_STEP==0:
            held[0]=0.
            leaders=[j for j in range(4) if r336[j]>0 and v168[j]>1.05]
            leaders.sort(key=lambda j:(-r336[j]*min(v168[j],3),j))
            if leaders:
                held[0,leaders[0]]=.58
                if len(leaders)>1:held[0,leaders[1]]=.18
            elif np.count_nonzero(r168<0)>=3:held[0,0]=-.30
            elif r336[0]>0:held[0,0]=.24
            elif r336[0]<0:held[0,0]=-.20
            updates[t,0]=True
        held[1:]=0.
        eligible[t]=bool(np.isfinite(oi[t-167:t+1]).all() and np.all(oi[t-167:t+1]>0))
        if eligible[t]:
            oi168=np.log(oi[t]/oi[t-167]);oi24=np.log(oi[t]/oi[t-24])
            picks=[j for j in range(4) if r72[j]>.05 and r24[j]>.015 and v24[j]>1.4 and oi168[j]>0]
            if picks:
                j=max(picks,key=lambda k:(r72[k]*min(v24[k],3),-k))
                held[1,j]=.22
            low=int(np.argmin(r168));high=int(np.argmax(r168))
            if low!=high and r168[high]-r168[low]>.12 and v168[low]>v168[high] and oi168[low]>0:
                held[2,low]=.12;held[2,high]=-.12
            if r24[0]<-.04 and v24[0]>2 and oi24[0]<-.02:
                held[3,0]=-.22;held[3,1]=-.10
            elif r168[0]<-.10 and r24[0]>.035 and v24[0]>1.6:
                held[3,0]=.20
            mult={"positive":(1.,.8,.4),"negative":(.6,.8,1.),"mixed":(.8,1.,.8)}[mode]
            held[1:]*=np.asarray(mult)[:,None]
        updates[t,1:]=True
        active[t]=np.abs(held[1:]).sum(axis=1)>1e-12
        raw[t:]=held
    return raw,updates,active,eligible
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00005*t*(1+j/9)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j));h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=1e6*(1+.15*np.sin(t/29+j));rate=np.tile(np.array([[-.0003,.0002,-.0001,.0005]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    oi=np.exp(7+.00001*t*(1+j/5)+.08*np.sin(t/38+j))
    a=bundle(o,h,l,c,q,rate,event,oi)
    oi2=oi.copy();oi2[14000:]*=3
    c2=c.copy();c2[14000:]*=1.4;o2=o.copy();o2[14000:]*=1.4
    h2=np.maximum(o2,c2)*1.005;l2=np.minimum(o2,c2)*.995
    q2=q.copy();q2[14000:]*=4
    b=bundle(o2,h2,l2,c2,q2,rate,event,oi2)
    if not np.array_equal(a[0][:14000],b[0][:14000]):raise ValueError("OH_FUTURE_LEAK")
    oi3=oi.copy();oi3[900,2]=np.nan
    z=bundle(o,h,l,c,q,rate,event,oi3)
    if z[3][WARMUP+168] or np.any(z[0][WARMUP+168,1:]):raise ValueError("OH_OI_QUARANTINE")
    if int(a[1][:,0].sum())!=27 or int(a[1][:,1].sum())!=105:raise ValueError("OH_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OH_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
