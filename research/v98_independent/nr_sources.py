#!/usr/bin/env python3
"""V98 NR distinct causal seven-slot raw source. Development 2023-24 only."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NR_full':(0,1,2,3),'NR_core_only':(0,),
       'NR_minus_opportunity':(0,2,3),'NR_minus_RV':(0,1,3),
       'NR_minus_stress':(0,1,2)}
def _core(r48,r336,vol):
    good=(r48>0)&(r336>0)
    w=np.zeros(4)
    available=np.flatnonzero(good).tolist()
    remaining=.70
    for _ in range(4):
        if not available or remaining<=1e-12:break
        inv=1./np.maximum(vol[available],.001)
        proposal=remaining*inv/inv.sum()
        hit=[j for j,v in zip(available,proposal) if v>=.28-w[j]-1e-12]
        if not hit:
            for j,v in zip(available,proposal):w[j]+=v
            remaining=0.
            break
        for j in hit:
            add=max(0.,.28-w[j]);w[j]+=add;remaining-=add
        available=[j for j in available if j not in hit]
    return w

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NR_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NR_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NR_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NR_FUNDING_CALENDAR')
    p=np.log(c)
    ret=np.diff(p,axis=0,prepend=p[:1])
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%168==0:
            if np.any(q[t]<=0):raise ValueError('NR_ZERO_VOLUME_DECISION_'+str(t))
            held[:]=0.
            r48=p[t]-p[t-48]
            r72=p[t]-p[t-72]
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            history=ret[t-335:t+1]
            vol=np.std(history,axis=0)
            held[0]=_core(r48,r336,vol)
            day=p[t]-p[t-24]
            prior_volume=q[t-359:t-23].reshape(14,24,4).sum(axis=1)
            median_volume=np.median(prior_volume,axis=0)
            last_volume=q[t-23:t+1].sum(axis=0)
            previous_high=np.max(h[t-72:t],axis=0)
            qualified=(c[t]>previous_high)&(last_volume>median_volume)&(day>0)
            choices=np.flatnonzero(qualified)
            if len(choices):
                best=sorted(choices,key=lambda j:(-day[j],int(j)))[0]
                held[1,best]=.18
            btc=history[:,0]
            denom=float(np.dot(btc-btc.mean(),btc-btc.mean()))
            if denom<=1e-18:beta=np.zeros(3)
            else:
                beta=np.array([np.clip(np.dot(btc-btc.mean(),history[:,j]-history[:,j].mean())/denom,-1.5,1.5)
                               for j in (1,2,3)])
            residual=r72[1:]-beta*r72[0]
            best=sorted((1,2,3),key=lambda j:(-residual[j-1],j))[0]
            worst=sorted((1,2,3),key=lambda j:(residual[j-1],j))[0]
            if residual[best-1]-residual[worst-1]>=.015:
                held[2,best]=.12;held[2,worst]=-.12
            btc48=float(np.std(ret[t-47:t+1,0]))
            btc336=float(max(vol[0],1e-6))
            if r48[0]<-.045 and p[t,0]-p[t-12,0]>0:
                held[3,0]=.14
            elif btc48>1.5*btc336 and r48[0]<0:
                held[3,0]=-.12
            risk_on=bool(r168[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.25,.75,.5] if risk_on else [.75,1.,1.25])[:,None]
            if np.abs(held[0]).sum()>.70+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NR_RAW_BUDGET')
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
    modified=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in modified[:4]:z[14000:]*=1.7
    modified[4][14000:]*=2.
    modified[5][14000:]*=-1.
    b=bundle(*modified,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NR_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NR_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::168]):raise ValueError('NR_MISSING_WEEKLY')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NR_DISTINCT_RAW_SOURCE_SYNTHETIC_PASS_NOT_PNL')
