#!/usr/bin/env python3
"""V98 LW preregistered breadth-diversified seven-slot source. Training only; no benchmark/holdout."""
import numpy as np
HOURS=18288
WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
BOOKS={'LW_full':(0,1,2,3),'LW_core_only':(0,),
       'LW_minus_opportunity':(0,2,3),'LW_minus_RV':(0,1,3),
       'LW_minus_stress':(0,1,2)}

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LW_SOURCE_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(q<0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LW_SOURCE_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('LW_SOURCE_NATIVE_FUNDING')
    p=np.log(c);intents=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    entries=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool)
    regimes=np.full(HOURS,'NEUTRAL',dtype='<U8')
    rows=np.zeros((4,4));expiry=np.full(4,-1,int)
    for t in range(WARMUP,HOURS):
        r504=p[t]-p[t-504];r336=p[t]-p[t-336];r168=p[t]-p[t-168]
        r24=p[t]-p[t-24]
        breadth=int(np.count_nonzero(r168>0))
        btc168=float(r168[0]);btc24=float(r24[0])
        regimes[t]='GROWTH' if breadth>=2 else 'STRESS' if btc168<0 and btc24<0 else 'NEUTRAL'
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[t-k]>0) for k in (24,168,336,504)))
        valid[t]=good
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                if np.any(rows[k]):
                    rows[k]=0;updates[t,k]=True
                expiry[k]=-1;expired.add(k)
        if (t-WARMUP)%336==0 and good:
            new=np.zeros(4)
            if breadth>=2:
                rank=np.argsort(-r504,kind='stable')
                if r504[rank[0]]>0:new[rank[0]]=.42
                if r504[rank[1]]>0:new[rank[1]]=.24
            if not np.array_equal(rows[0],new):
                rows[0]=new;updates[t,0]=True
        if (t-WARMUP)%168==0 and good:
            if 1 not in expired and expiry[1]<0 and breadth>=2:
                j=int(np.argmax(r24))
                if r24[j]>0:
                    rows[1,j]=.10;expiry[1]=t+168
                    entries[t,0]=True;updates[t,1]=True
            if 2 not in expired and expiry[2]<0 and breadth>=2 and np.ptp(r24)>=.06:
                lo=int(np.argmin(r24));hi=int(np.argmax(r24))
                if lo!=hi:
                    rows[2,lo]=.035;rows[2,hi]=-.035
                    expiry[2]=t+168;entries[t,1]=True;updates[t,2]=True
            if 3 not in expired and expiry[3]<0 and btc168<0 and btc24<0:
                rows[3,0]=-.10;expiry[3]=t+168
                entries[t,2]=True;updates[t,3]=True
        intents[t]=rows
        if np.abs(rows).sum()>.93+1e-9:raise ValueError('LW_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    changed=[x.copy() for x in (o,h,l,c,q,r)]
    for x in changed[:4]:x[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,e)
    if not all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('LW_FUTURE_LEAK')
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=2)>0)&~a[1][1:]):
        raise ValueError('LW_SILENT_UPDATE')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('LW_SYNTHETIC_CAUSALITY_PASS')
