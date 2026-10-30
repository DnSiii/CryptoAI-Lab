#!/usr/bin/env python3
"""V98 NV preregistered volume-migration seven-slot source; 2023-24 development only."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=336
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NV_full':(0,1,2,3),'NV_core_only':(0,),
       'NV_minus_opportunity':(0,2,3),'NV_minus_RV':(0,1,3),
       'NV_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NV_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NV_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NV_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NV_FUNDING_CALENDAR')
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NV_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r504=p[t]-p[t-504]
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            avgclose=np.mean(c[t-167:t+1],axis=0)
            eligible=[j for j in range(4) if r504[j]>0 and r168[j]>0 and c[t,j]>avgclose[j]]
            ranked=sorted(eligible,key=lambda j:(-r504[j],j))
            if ranked:
                held[0,ranked[0]]=.72
                if len(ranked)>1:held[0,ranked[1]]=.08
            elif r168[0]<-.08:
                held[0,0]=-.28
            # Within-asset volume ratios only; never compare absolute BTC/SOL volumes.
            recent=np.mean(q[t-23:t+1],axis=0)
            prior=np.mean(q[t-191:t-23],axis=0)
            ratio=recent/np.maximum(prior,1e-12)
            opp=[j for j in range(4) if r72[j]>0 and r24[j]>0 and ratio[j]>1.05]
            if opp:
                j=min(opp,key=lambda k:(-r24[k]*ratio[k],k))
                held[1,j]=.14
            highest=min(range(4),key=lambda j:(-ratio[j],j))
            lowest=min(range(4),key=lambda j:(ratio[j],j))
            if ratio[highest]-ratio[lowest]>=.20:
                held[2,highest]=.10
                held[2,lowest]=-.10
            btc_down=(c[t-71:t+1,0]<o[t-71:t+1,0])
            total=float(np.sum(q[t-71:t+1,0]))
            down_fraction=float(np.sum(q[t-71:t+1,0][btc_down])/total) if total>0 else 0.5
            if down_fraction>.65 and r72[0]<-.07:
                held[3,0]=-.14
            elif down_fraction<.40 and r168[0]<-.10 and r24[0]>0:
                held[3,0]=.14
            risk_on=bool(r168[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.,.8,.5] if risk_on else [.75,.8,1.])[:,None]
            if np.abs(held[0]).sum()>.80+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NV_RAW_BUDGET')
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
    q=np.ones_like(c)*1e6*(1+.1*np.sin(t/17+j))
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    modified=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in modified[:4]:z[14000:]*=1.7
    modified[4][14000:]*=2.
    modified[5][14000:]*=-1.
    b=bundle(*modified,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NV_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NV_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::STEP]):raise ValueError('NV_MISSING_DECISION')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NV_LIQUIDITY_ROTATION_SOURCE_SYNTHETIC_PASS_NOT_PNL')
