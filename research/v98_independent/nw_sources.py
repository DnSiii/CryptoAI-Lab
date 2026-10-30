#!/usr/bin/env python3
"""V98 NW preregistered price-structure seven-slot signals, 2023-24 only."""
import numpy as np
HOURS=18288
WARMUP=744
STEP=336
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'NW_full':(0,1,2,3),'NW_core_only':(0,),
       'NW_minus_opportunity':(0,2,3),'NW_minus_RV':(0,1,3),
       'NW_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('NW_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError('NW_SOURCE_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NW_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NW_FUNDING_CALENDAR')
    p=np.log(c)
    raw=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool)
    held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if np.any(q[t]<=0) or t%8 or not np.all(event[t]):
                raise ValueError('NW_BAD_DECISION_CALENDAR_'+str(t))
            held[:]=0.
            r336=p[t]-p[t-336]
            r168=p[t]-p[t-168]
            r72=p[t]-p[t-72]
            r24=p[t]-p[t-24]
            ma168=c[t-167:t+1].mean(axis=0)
            eligible=[j for j in range(4) if r336[j]>0 and r168[j]>0 and c[t,j]>ma168[j]]
            ranked=sorted(eligible,key=lambda j:(-r336[j],j))
            if ranked:
                held[0,ranked[0]]=.72
                if len(ranked)>1:held[0,ranked[1]]=.08
            elif r168[0]<-.04 and c[t,0]<c[t-335:t+1,0].mean():
                held[0,0]=-.52
            # Prior high excludes decision hour. Compression uses only completed OHLC.
            vnow=np.mean((h[t-71:t+1]-l[t-71:t+1])/c[t-71:t+1],axis=0)
            vprev=np.mean((h[t-239:t-71]-l[t-239:t-71])/c[t-239:t-71],axis=0)
            breakout=[j for j in range(4) if c[t,j]>np.max(h[t-168:t,j])
                      and r72[j]>0 and vnow[j]<.90*vprev[j]]
            if breakout:
                j=min(breakout,key=lambda k:(-r72[k],k))
                held[1,j]=.18
            # Independent 336-hour rolling BTC-beta residual, not volume migration.
            hourly=p[t-335:t+1]-p[t-336:t]
            btc=hourly[:,0]
            vb=float(np.var(btc))
            beta=np.clip(np.mean((hourly-btc.mean())*(btc[:,None]-btc.mean()),axis=0)/max(vb,1e-12),0.,2.)
            residual=r72-beta*r72[0]
            others=(1,2,3)
            worst=min(others,key=lambda j:(residual[j],j))
            best=min(others,key=lambda j:(-residual[j],j))
            if worst!=best and residual[best]-residual[worst]>.035:
                held[2,worst]=.12
                held[2,best]=-.12
            drawdown=1.-c[t,0]/np.max(h[t-336:t,0])
            if drawdown>.12 and r24[0]>.015:
                held[3,0]=.18
            elif drawdown>.12 and r24[0]<-.07:
                held[3,0]=-.18
            risk_on=bool(r168[0]>0 and np.count_nonzero(r168>0)>=2)
            held[1:]*=np.array([1.,.7,.5] if risk_on else [.65,.8,1.])[:,None]
            if np.abs(held[0]).sum()>.80+1e-10 or np.abs(held[1:]).sum()>1.0:
                raise ValueError('NW_RAW_BUDGET')
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
        raise ValueError('NW_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~a[1][1:,0]):
        raise ValueError('NW_SILENT_CHANGE')
    if not np.all(a[1][WARMUP::STEP]):
        raise ValueError('NW_MISSING_DECISION')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NW_PRICE_STRUCTURE_CAUSAL_SYNTHETIC_PASS_NOT_PNL')
