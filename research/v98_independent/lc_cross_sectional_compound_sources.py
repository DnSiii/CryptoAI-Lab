#!/usr/bin/env python3
"""V98 LC preregistered source: leadership + pullback + dispersion + downside semivol.
Causal completed-close intents only. No historical PnL or future validation access.
"""
from __future__ import annotations
import numpy as np
WARMUP=744
BUDGET=np.array([.65,.12,.10,.08],dtype=float)
PATHS=('LC_core_only','LC_full','LC_minus_opportunity','LC_minus_RV','LC_minus_stress')

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
        (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError('LC_INVALID_CANONICAL_SOURCE')
    n=len(c);lc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,'MIXED',dtype='<U12')
    current=np.zeros((4,4),dtype=float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        weekly=(t-WARMUP)%168==0
        monthly=(t-WARMUP)%672==0
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        r504=lc[t]-lc[t-504]
        r336=lc[t]-lc[t-336]
        r168=lc[t]-lc[t-168]
        r24=lc[t]-lc[t-24]
        r6=lc[t]-lc[t-6]
        m336=float(np.median(r336));m168=float(np.median(r168))
        regimes[t]='GROWTH' if m336>0 else 'DEFENSE' if m168<0 else 'MIXED'
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1;expired.add(k)
        if monthly and good:
            current[0]=0.
            eligible=np.flatnonzero(r168>0)
            ranked=sorted(eligible,key=lambda j:(-float(r504[j]),int(j)))
            if ranked:current[0,ranked[0]]=.53
            if len(ranked)>1:current[0,ranked[1]]=.12
            updates[t,0]=True
        if weekly and good and expiry[1]<0 and 1 not in expired and regimes[t]=='GROWTH':
            eligible=(r336>0)&(r24<0)&(r6>0)
            if np.any(eligible):
                j=int(np.argmin(np.where(eligible,r24,np.inf)))
                current[1]=0.;current[1,j]=.12
                expiry[1]=t+168;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0 and 2 not in expired:
            hi=int(np.argmax(r168));lo=int(np.argmin(r168))
            if hi!=lo and r168[hi]>0 and r168[hi]>r168[lo]:
                current[2]=0.;current[2,hi]=.05;current[2,lo]=-.05
                expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if weekly and good and expiry[3]<0 and 3 not in expired and regimes[t]=='DEFENSE':
            hourly=np.diff(lc[t-168:t+1],axis=0)
            downside=np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0))
            j=int(np.argmax(downside))
            if r168[j]<0:
                current[3]=0.;current[3,j]=-.08
                expiry[3]=t+168;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>.95+1e-10:raise ValueError('LC_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def static_check():
    n=2200;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .06*np.sin(t[:,None]/81.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.tile(np.array([-.00008,.00012,.00001,.00025]),(n,1))
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[1700:]*=1.8
    qq[1700:]*=4.;rr[1700:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1700],b[i][:1700]):
            raise ValueError('LC_FUTURE_LEAK_'+str(i))
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes&~a[1][1:]):raise ValueError('LC_SILENT_ROW_REBALANCE')
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError('LC_QUOTE_QUARANTINE')
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.95+1e-10
    assert not a[1][:WARMUP].any()
    return True
if __name__=='__main__':
    assert static_check()
    print('LC_SOURCE_SYNTHETIC_CAUSAL_PASS')
