#!/usr/bin/env python3
"""V98 MB frozen-source candidate: joint capital competition, 2023-24 TRAINING ONLY."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'MB_full':(0,1,2,3),'MB_core_only':(0,),
       'MB_minus_opportunity':(0,2,3),'MB_minus_RV':(0,1,3),
       'MB_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):raise ValueError('MB_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):raise ValueError('MB_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MB_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MB_FUNDING_CALENDAR')
    p=np.log(c)
    hourly=np.diff(p,axis=0,prepend=p[:1])
    intents=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    regimes=np.full(HOURS,'BEAR',dtype='<U5')
    rows=np.zeros((4,4))
    prev=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r504=p[t]-p[t-504];r168=p[t]-p[t-168];r72=p[t]-p[t-72]
        r48=p[t]-p[t-48];prev72=p[t-72]-p[t-144]
        breadth=int(np.sum(r168>0))
        regimes[t]='BULL' if breadth>=3 else 'MIXED' if breadth else 'BEAR'
        good=bool(np.all(q[t-167:t+1]>0) and np.all(q[t-504]>0))
        valid[t]=good
        vol=np.std(hourly[t-167:t+1],axis=0)
        denom=.08+3*vol
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;expired.add(k)
        if (t-WARMUP)%336==0 and good:
            core=np.zeros(4)
            rank=np.argsort(-(r504/denom),kind='stable')
            weights=(.44,.22) if breadth>=3 else ((.30,.12) if breadth else (0.,0.))
            for j,v in zip(rank[:2],weights):
                if r504[j]>0:core[j]=v
            rows[0]=core
        if (t-WARMUP)%168==0 and good and 1 not in expired and expiry[1]<0 and breadth>=2:
            eligible=np.flatnonzero(r168>0)
            if eligible.size:
                accel=r72-prev72
                j=int(eligible[np.argmax(accel[eligible])])
                if accel[j]>0 and r72[j]>0:
                    score=max(0.,float(accel[j]/denom[j]))
                    rows[1,j]=.13*(.5+.5*np.tanh(score))
                    expiry[1]=t+168;entries[t,0]=True
        if (t-WARMUP)%336==0 and good and 2 not in expired and expiry[2]<0:
            residual=r168-np.median(r168)
            rank=np.argsort(-residual,kind='stable')
            j,k=int(rank[0]),int(rank[-1])
            spread=float(residual[j]-residual[k])
            if spread>.06:
                score=spread/(.08+3*float(np.mean(vol)))
                size=.08*(.5+.5*np.tanh(score))
                rows[2,j]=size;rows[2,k]=-size
                expiry[2]=t+336;entries[t,1]=True
        if (t-WARMUP)%72==0 and good and 3 not in expired and expiry[3]<0:
            eligible=np.flatnonzero(r48>0)
            if np.count_nonzero(r168<0)>=2 and len(eligible)>=2:
                j=int(eligible[np.argmax(r48[eligible])])
                score=max(0.,float(r48[j]/denom[j]))
                rows[3,j]=.11*(.5+.5*np.tanh(score))
                expiry[3]=t+144;entries[t,2]=True
        target=rows.copy()
        cg=float(np.abs(target[0]).sum())
        og=float(np.abs(target[1:]).sum())
        if cg>.90+1e-12:raise ValueError('MB_CORE_GROSS')
        if og>0:target[1:]*=min(1.,max(0.,(.90-cg)/og))
        if np.abs(target).sum()>.90+1e-9:raise ValueError('MB_TARGET_GROSS')
        updates[t]=np.any(np.abs(target-prev)>1e-12,axis=1)
        intents[t]=target
        prev=target
    return intents,updates,entries,valid,regimes
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[x.copy() for x in (o,h,l,c,q,rate)]
    for x in changed[:4]:x[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MB_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]):
        raise ValueError('MB_SILENT_UPDATE')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MB_SYNTHETIC_CAUSALITY_PASS')
