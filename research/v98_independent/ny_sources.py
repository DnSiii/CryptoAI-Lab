#!/usr/bin/env python3
"""V98 NY preregistered downside-efficiency/channel-dispersion seven-slot source, 2023-24."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=336
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"NY_full":(0,1,2,3),"NY_core_only":(0,),
       "NY_minus_opportunity":(0,2,3),"NY_minus_RV":(0,1,3),
       "NY_minus_stress":(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError("NY_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("NY_SOURCE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("NY_SOURCE_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("NY_FUNDING_CALENDAR")
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),dtype=bool)
    active=np.zeros((HOURS,3),dtype=bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError("NY_BAD_DECISION_CALENDAR_"+str(t))
            held[:]=0.
            r504=p[t]-p[t-504]
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            hourly=np.diff(p[t-504:t+1],axis=0)
            downside=np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0))
            eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0]
            ranked=sorted(eligible,key=lambda j:(-r504[j]/max(float(downside[j]),.001),j))
            if ranked:
                held[0,ranked[0]]=.72
                if len(ranked)>1:held[0,ranked[1]]=.08
            elif np.count_nonzero(r168<0)>=3:
                held[0,0]=-.58
            recent=np.mean((h[t-23:t+1]-l[t-23:t+1])/c[t-23:t+1],axis=0)
            earlier=np.mean((h[t-191:t-23]-l[t-191:t-23])/c[t-191:t-23],axis=0)
            expansion=recent/np.maximum(earlier,1e-12)
            opp=[j for j in range(4) if r24[j]>.03 and r72[j]>.05 and expansion[j]>1.15]
            if opp:
                best=min(opp,key=lambda j:(-r24[j]/expansion[j],j))
                held[1,best]=.18
            channel_hi=np.max(h[t-167:t+1],axis=0)
            channel_lo=np.min(l[t-167:t+1],axis=0)
            channel=(c[t]-channel_lo)/np.maximum(channel_hi-channel_lo,1e-12)
            low=min((1,2,3),key=lambda j:(channel[j],j))
            high=min((1,2,3),key=lambda j:(-channel[j],j))
            if low!=high and channel[high]-channel[low]>.40:
                held[2,low]=.12
                held[2,high]=-.12
            btc=np.diff(p[t-168:t+1,0])
            down=np.sqrt(np.mean(np.minimum(btc,0.)**2))
            up=np.sqrt(np.mean(np.maximum(btc,0.)**2))
            if down/max(float(up),.001)>1.50 and r168[0]<-.04:
                if r24[0]>.01:held[3,0]=.18
                elif r24[0]<-.04:held[3,0]=-.18
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.,.7,.5] if risk_on else [.75,1.,1.])[:,None]
            if np.abs(held[0]).sum()>.80+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError("NY_RAW_BUDGET")
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
        raise ValueError("NY_FUTURE_LEAK")
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError("NY_SILENT_CHANGE")
    if not np.all(a[1][WARMUP::STEP]):
        raise ValueError("NY_MISSING_DECISION")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("NY_DOWNSIDE_EFFICIENCY_SOURCE_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
