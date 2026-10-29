#!/usr/bin/env python3
"""V98 MD preregistered seven-slot slow carry-dispersion engine, TRAINING ONLY."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'MD_full':(0,1,2,3),'MD_core_only':(0,),
       'MD_minus_opportunity':(0,2,3),'MD_minus_RV':(0,1,3),
       'MD_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):
        raise ValueError('MD_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):
        raise ValueError('MD_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('MD_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('MD_FUNDING_CALENDAR')
    p=np.log(c)
    returns=np.diff(p,axis=0,prepend=p[:1])
    intents=np.zeros((HOURS,4,4))
    updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool)
    valid=np.zeros(HOURS,bool)
    regimes=np.full(HOURS,'BEAR',dtype='<U5')
    rows=np.zeros((4,4));prev=np.zeros((4,4))
    expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r672=p[t]-p[t-672];r336=p[t]-p[t-336]
        r168=p[t]-p[t-168];r72=p[t]-p[t-72]
        breadth=int(np.count_nonzero(r336>0))
        regimes[t]='BULL' if breadth>=3 else 'MIXED' if breadth else 'BEAR'
        good=bool(np.all(q[t-335:t+1]>0) and np.all(q[t-672]>0))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0.;expiry[k]=-1;expired.add(k)
        if (t-WARMUP)%672==0 and good:
            downside=np.minimum(returns[t-335:t+1],0.)
            semivol=np.sqrt(np.mean(downside**2,axis=0))
            scores=r672/(.08+3*semivol)
            rank=np.argsort(-scores,kind='stable')
            weights=(.52,.24) if breadth>=3 else ((.40,.12) if breadth else (0.,0.))
            core=np.zeros(4)
            for j,w in zip(rank[:2],weights):
                if r672[j]>0:core[j]=w
            rows[0]=core
        if (t-WARMUP)%336==0 and good and 1 not in expired and expiry[1]<0 and breadth>=2:
            eligible=np.flatnonzero((r336>0)&(r72>0))
            if eligible.size:
                j=int(eligible[np.argmax(r72[eligible])])
                if float(np.mean(q[t-71:t+1,j]))>float(np.mean(q[t-335:t-71,j])):
                    rows[1,j]=.14;expiry[1]=t+336;entries[t,0]=True
        if (t-WARMUP)%168==0 and good and 2 not in expired and expiry[2]<0:
            rates=rate[t-167:t+1];events=event[t-167:t+1]
            counts=np.sum(events,axis=0)
            if np.all(counts==21):
                avg=np.sum(rates,axis=0)/counts
                rank=np.argsort(avg,kind='stable')
                low,high=int(rank[0]),int(rank[-1])
                if float(avg[high]-avg[low])>.00015 and abs(float(r168[high]-r168[low]))<.10:
                    rows[2,low]=.07;rows[2,high]=-.07
                    expiry[2]=t+336;entries[t,1]=True
        if (t-WARMUP)%168==0 and good and 3 not in expired and expiry[3]<0:
            eligible=np.flatnonzero(r72>0)
            if np.count_nonzero(r336<0)>=2 and eligible.size>=2:
                j=int(eligible[np.argmax(r72[eligible])])
                rows[3,j]=.12;expiry[3]=t+168;entries[t,2]=True
        target=rows.copy()
        cg=float(np.abs(target[0]).sum())
        og=float(np.abs(target[1:]).sum())
        if cg>.88+1e-12:raise ValueError('MD_CORE_GROSS')
        if og>0:target[1:]*=min(1.,max(0.,(.88-cg)/og))
        if np.abs(target).sum()>.88+1e-9:raise ValueError('MD_TARGET_GROSS')
        updates[t]=np.any(np.abs(target-prev)>1e-12,axis=1)
        intents[t]=target;prev=target
    return intents,updates,entries,valid,regimes
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    rate[~event]=0.
    a=bundle(o,h,l,c,q,rate,event)
    changed=[x.copy() for x in (o,h,l,c,q,rate)]
    for x in changed[:4]:x[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('MD_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]):
        raise ValueError('MD_SILENT_UPDATE')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('MD_SYNTHETIC_CAUSALITY_PASS')
