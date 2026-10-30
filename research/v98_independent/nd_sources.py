#!/usr/bin/env python3
"""V98 ND preregistered netted complete architecture, TRAINING only."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'ND_full':(0,1,2,3),'ND_core_only':(0,),
       'ND_minus_opportunity':(0,2,3),'ND_minus_RV':(0,1,3),
       'ND_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('ND_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('ND_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('ND_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('ND_FUNDING_CALENDAR')
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4));prev=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP;good=bool(np.all(q[t]>0));valid[t]=good
        if k%672==0:
            if not good:raise ValueError('ND_CORE_ZERO_VOLUME_'+str(t))
            downside=np.sqrt(np.mean(np.minimum(r[t-167:t+1],0.)**2,axis=0))
            score=(p[t]-p[t-504])/np.maximum(downside,.001)
            rank=np.argsort(-score,kind='stable')
            state[0]=0.
            if np.count_nonzero(score>0)>=2:
                state[0,int(rank[0])]=.44;state[0,int(rank[1])]=.18
            else:
                state[0,int(rank[0])]=.18;state[0,int(rank[-1])]=-.28
        if k%168==0:
            if not good:raise ValueError('ND_WEEKLY_ZERO_VOLUME_'+str(t))
            ret504=p[t]-p[t-504];ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72];ret48=p[t]-p[t-48];ret24=p[t]-p[t-24]
            state[1:]=0.
            volume_ratio=np.mean(q[t-47:t+1,1:],axis=0)/np.maximum(
                np.mean(q[t-167:t-47,1:],axis=0),1e-12)
            long_candidates=np.flatnonzero((ret168[1:]>0)&(ret48[1:]>0)&(volume_ratio>1.05))
            if len(long_candidates):
                j=1+int(long_candidates[np.argmax(ret48[1:][long_candidates])])
                state[1,j]=.14
            elif ret168[0]<0:
                short_candidates=np.flatnonzero((ret168[1:]<0)&(ret48[1:]<0)&(volume_ratio>1.05))
                if len(short_candidates):
                    j=1+int(short_candidates[np.argmin(ret48[1:][short_candidates])])
                    state[1,j]=-.14
            # 21 previously settled 8h events, excludes the current t event.
            history=rate[t-168:t:8]
            if history.shape!=(21,4):raise ValueError('ND_FUNDING_LOOKBACK')
            spread=history[:,1:].mean(axis=0)-history[:,0].mean()
            j=1+int(np.argmax(np.abs(spread)))
            if abs(float(spread[j-1]))>=.000025:
                direction=-1. if spread[j-1]>0 else 1.
                state[2,j]=direction*.08;state[2,0]=-direction*.08
            if ret72[0]<-.04 and np.count_nonzero(ret72[1:]<0)>=2:
                state[3,1+int(np.argmin(ret72[1:]))]=-.12
            elif ret72[0]>0 and ret168[0]<-.04 and np.count_nonzero(ret168[1:]<0)>=2:
                state[3,1+int(np.argmax(ret24[1:]))]=.12
            constructive=ret504[0]>0 and np.count_nonzero(ret168>0)>=2
            mult[:]=[1.,.8,.7] if constructive else [.85,1.,1.]
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.5:mult[0]*=.5;mult[2]=1.
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('ND_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('ND_VIRTUAL_GROSS')
        updates[t]=np.any(np.abs(w-prev)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w;prev=w
    return target,updates,active,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00007*t*(1+j/4)+.12*np.sin(t/43+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1+.3*np.sin(t/7+j))**2*np.ones_like(c)
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('ND_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('ND_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('ND_FORCED_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('ND_SYNTHETIC_CAUSALITY_PASS_NOT_PNL')
