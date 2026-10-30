#!/usr/bin/env python3
"""V98 NA independent breakout / residual-reversion / BTC-shock seven-slot source.
Training-only 2022-12 warmup and 2023-24; never touches validation or holdout.
"""
import numpy as np

HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'NA_full':(0,1,2,3),'NA_core_only':(0,),
       'NA_minus_opportunity':(0,2,3),'NA_minus_RV':(0,1,3),
       'NA_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('NA_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('NA_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NA_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NA_FUNDING_CALENDAR')
    p=np.log(c)
    r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4))
    previous=np.zeros((4,4))
    factors=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP
        good=bool(np.all(q[t]>0))
        valid[t]=good
        if k%672==0:
            if not good:raise ValueError('NA_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            btc504=float(p[t,0]-p[t-504,0])
            trend168=p[t]-p[t-168]
            state[0]=0.
            if btc504>0 and np.count_nonzero(trend168[1:]>0)>=2:
                leader=int(1+np.argmax((p[t]-p[t-504])[1:]))
                state[0,0]=.50
                state[0,leader]=.20
            else:
                calm=int(1+np.argmin(np.std(r[t-167:t+1,1:],axis=0)))
                state[0,0]=-.40
                state[0,calm]=.10
        if k%168==0:
            if not good:raise ValueError('NA_WEEKLY_ZERO_VOLUME_'+str(t))
            btc504=float(p[t,0]-p[t-504,0])
            trend168=p[t]-p[t-168]
            trend72=p[t]-p[t-72]
            btc24=float(p[t,0]-p[t-24,0])
            state[1:]=0.
            # Volume-confirmed range breakout. Exclude current bar from prior extreme.
            q24=np.sum(q[t-23:t+1,1:],axis=0)
            q168=np.sum(q[t-167:t+1,1:],axis=0)
            volume_ratio=q24/np.maximum(q168/7.,1e-10)
            previous_hi=np.max(h[t-96:t,1:],axis=0)
            previous_lo=np.min(l[t-96:t,1:],axis=0)
            candidates=[]
            for z in range(3):
                if volume_ratio[z]<=1.20:continue
                j=z+1
                if c[t,j]>previous_hi[z]:
                    candidates.append(((c[t,j]/previous_hi[z]-1.),j,1.))
                elif c[t,j]<previous_lo[z]:
                    candidates.append(((1.-c[t,j]/previous_lo[z]),j,-1.))
            if candidates:
                # Stable tie-breaker favors lower asset index, not result-driven choice.
                strength,j,side=max(candidates,key=lambda a:(a[0],-a[1]))
                state[1,j]=.14*side
            # Beta-neutral residual mean reversion, two legs at all times when active.
            rb=r[t-335:t+1,0]
            xb=rb-rb.mean()
            vb=float(np.mean(xb*xb))
            alt=r[t-335:t+1,1:]
            xa=alt-alt.mean(axis=0)
            beta=np.clip(np.mean(xa*xb[:,None],axis=0)/max(vb,1e-12),0.,3.)
            residual=trend168[1:]-beta*trend168[0]
            cheap=int(1+np.argmin(residual))
            rich=int(1+np.argmax(residual))
            if rich!=cheap and float(np.max(residual)-np.min(residual))>.045:
                state[2,cheap]=.08
                state[2,rich]=-.08
            # BTC shock continuation / recovery, distinct from ranked alt stress.
            negative=int(np.count_nonzero(trend72<0))
            if btc24<-.035 and negative>=3:
                state[3,0]=-.14
            elif btc24>.020 and trend72[0]<0 and negative>=2:
                state[3,0]=.14
            constructive=btc504>0 and np.count_nonzero(trend168[1:]>0)>=2
            factors[:]=[1.,.9,.6] if constructive else [.8,1.,1.]
            v72=float(np.std(r[t-71:t+1,0]))
            v336=float(np.std(r[t-335:t+1,0]))
            if v72/max(v336,1e-8)>1.5:
                factors[0]*=.5
                factors[2]=1.
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy()
        w[1:]*=factors[:,None]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('NA_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NA_GROSS')
        updates[t]=np.any(np.abs(w-previous)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w
        previous=w
    return target,updates,active,valid

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
        raise ValueError('NA_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NA_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):
        raise ValueError('NA_MISSING_FORCED_CORE_REFRESH')
    return True

if __name__=='__main__':
    assert synthetic_causality()
    print('NA_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
