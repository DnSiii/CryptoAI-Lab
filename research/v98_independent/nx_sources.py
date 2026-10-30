#!/usr/bin/env python3
"""V98 NX preregistered trend/carry/volatility seven-slot signals; development only."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=336
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NX_full':(0,1,2,3),'NX_core_only':(0,),
       'NX_minus_opportunity':(0,2,3),'NX_minus_RV':(0,1,3),
       'NX_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NX_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NX_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NX_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NX_FUNDING_CALENDAR')
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NX_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=2)
            if risk_on:
                held[0,0]=.62
                top=min((1,2,3),key=lambda j:(-r168[j],j))
                if r168[top]>0:held[0,top]=.18
            else:
                held[0,0]=-.62
                bottom=min((1,2,3),key=lambda j:(r168[j],j))
                if r168[bottom]<0:held[0,bottom]=-.12
            j=min(range(4),key=lambda k:(-abs(r24[k]),k))
            if abs(r24[j])>.025 and r24[j]*r72[j]>0:
                held[1,j]=.18 if r24[j]>0 else -.18
            hist=rate[t-160:t+1:8]
            if hist.shape!=(21,4) or not np.all(event[t-160:t+1:8]):
                raise ValueError('NX_FUNDING_LOOKBACK')
            mean=hist.mean(axis=0)
            low=min(range(4),key=lambda k:(mean[k],k))
            high=min(range(4),key=lambda k:(-mean[k],k))
            if low!=high and mean[high]-mean[low]>.00001:
                held[2,low]=.12
                held[2,high]=-.12
            if r168[0]<0 and r24[0]<0:held[3,0]=-.18
            elif r168[0]<0 and r24[0]>0:held[3,0]=.12
            elif r168[0]>=0 and r24[0]<-.04:held[3,0]=-.18
            held[1:]*=np.array([1.,.7,.4] if risk_on else [.8,1.,1.])[:,None]
            if np.abs(held[0]).sum()>.80+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NX_RAW_BUDGET')
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
        raise ValueError('NX_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NX_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::STEP]):
        raise ValueError('NX_MISSING_DECISION')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NX_TREND_CARRY_CAUSAL_SYNTHETIC_PASS_NOT_PNL')
