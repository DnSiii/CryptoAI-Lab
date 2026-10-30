#!/usr/bin/env python3
"""V98 MZ preregistered cross-sectional crash / two-leg funding portfolio; 2023-24 training only."""
import numpy as np

HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'MZ_full':(0,1,2,3),'MZ_core_only':(0,),
       'MZ_minus_opportunity':(0,2,3),'MZ_minus_RV':(0,1,3),
       'MZ_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MZ_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MZ_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MZ_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MZ_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active_weeks=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    base_factors=np.ones(3)
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%672==0:
            if not good:raise ValueError('MZ_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            r336=p[t]-p[t-336]
            vol336=np.std(r[t-335:t+1,1:4],axis=0)*np.sqrt(336.)
            leader=int(1+np.argmax(r336[1:4]/np.maximum(vol336,.03)))
            state[0]=0.
            if r336[0]>0 and r336[leader]>0:
                state[0,0]=.49
                state[0,leader]=.21
            else:
                state[0,0]=.42
                state[0,2]=.08
        if k%168==0:
            if not good:raise ValueError('MZ_WEEKLY_ZERO_VOLUME_'+str(t))
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            btc336=float(p[t,0]-p[t-336,0])
            vol336h=np.std(r[t-335:t+1,1:4],axis=0)
            vol72h=np.std(r[t-71:t+1,1:4],axis=0)
            # Opportunity: continuation after controlled volatility; persistent until trend invalidation.
            prior=np.flatnonzero(state[1]>0)
            state[1]=0.
            if len(prior)==1 and r168[prior[0]]>0 and btc336>0:
                state[1,prior[0]]=.12
            else:
                eligible=np.flatnonzero((r168[1:4]>0)&(r24[1:4]>0)&
                    (vol72h<=1.2*np.maximum(vol336h,1e-10)))+1
                if len(eligible):
                    scores=r168[eligible]/np.maximum(vol336h[eligible-1]*np.sqrt(336.),.03)
                    leader=int(eligible[np.argmax(scores)])
                    state[1,leader]=.12
            # RV: simultaneous low-carry long / high-carry short, never one-leg direction.
            carry=np.mean(rate[t-160:t+1:8,1:4],axis=0)
            low=int(1+np.argmin(carry))
            high=int(1+np.argmax(carry))
            spread=float(carry[high-1]-carry[low-1])
            old_long=np.flatnonzero(state[2]>0)
            old_short=np.flatnonzero(state[2]<0)
            same_pair=(len(old_long)==1 and len(old_short)==1 and
                       int(old_long[0])==low and int(old_short[0])==high)
            state[2]=0.
            if low!=high and (spread>.00002 or (same_pair and spread>.00001)):
                state[2,low]=.06
                state[2,high]=-.06
            # Stress/Recovery: rank assets rather than fixed ETH/SOL directional bets.
            state[3]=0.
            breadth=int(np.count_nonzero(r72<0))
            if breadth>=3 and r24[0]<0:
                worst=int(1+np.argmin(r72[1:4]))
                state[3,worst]=-.12
            elif breadth>=2 and r24[0]>0:
                best=int(1+np.argmax(r24[1:4]))
                state[3,best]=.12
            if k%672==0:
                constructive=bool(btc336>0 and np.count_nonzero(r168[1:4]>0)>=2)
                base_factors[:]=[1.,.75,.8] if constructive else [.65,1.,1.]
            factors[:]=base_factors
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.4:
                factors[0]*=.5
                factors[2]=1.
            active_weeks[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        w[1:]*=factors[:,None]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('MZ_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('MZ_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
    return target,updates,active_weeks,valid

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6)
    rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3
    changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MZ_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('MZ_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('MZ_MISSING_FORCED_CORE_REFRESH')
    return True

if __name__=='__main__':
    assert synthetic_causality()
    print('MZ_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
