#!/usr/bin/env python3
"""V98 LJ preregistered seven-slot source, 2023/24 TRAIN only; no system PnL."""
from __future__ import annotations
import numpy as np
from v98_clean4_training_reader import HOURS,WARMUP
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
PATHS=('LJ_core_only','LJ_full','LJ_minus_opportunity','LJ_minus_RV','LJ_minus_stress')

def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    n=len(c)
    if n!=HOURS or any(x.shape!=(n,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError('LJ_INVALID_SHAPE')
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)) or np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or np.any(q<0):
        raise ValueError('LJ_INVALID_NUMERIC_SOURCE')
    if np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)):
        raise ValueError('LJ_INVALID_OHLC')
    lc=np.log(c)
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    regimes=np.full(n,'RANGE',dtype='<U12')
    rows=np.zeros((4,4),float)
    expiry=np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        # The 24-hour cooldown plus all price feature endpoint quotes are strictly historical.
        endpoint=(t,t-24,t-72,t-144,t-168,t-336,t-720)
        good=bool(np.all(q[t-23:t+1]>0) and all(np.all(q[k]>0) for k in endpoint))
        valid[t]=good
        r720=lc[t]-lc[t-720];r336=lc[t]-lc[t-336];r168=lc[t]-lc[t-168]
        r144=lc[t]-lc[t-144];r72=lc[t]-lc[t-72];r24=lc[t]-lc[t-24]
        m168=float(np.median(r168));m72=float(np.median(r72));m24=float(np.median(r24))
        state=('STRESS' if m168<-.035 and m72<-.015 else
               'RECOVERY' if m168<0 and m24>.015 else
               'RISK_ON' if m168>.02 else 'RANGE')
        regimes[t]=state
        expired=set()
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                rows[k]=0;expiry[k]=-1;updates[t,k]=True;expired.add(k)
        if good and (t-WARMUP)%336==0:
            eligible=(r720>0)&(r168>0)
            ranked=sorted(np.flatnonzero(eligible),key=lambda j:(-float(r336[j]),int(j)))
            rows[0]=0
            if ranked:
                rows[0,ranked[0]]=.40
                if len(ranked)>1:rows[0,ranked[1]]=.24
            updates[t,0]=True
        if good and (t-WARMUP)%72==0 and expiry[1]<0 and 1 not in expired and state=='RISK_ON':
            eligible=(r72>.025)&(r24>.005)
            if np.any(eligible):
                acceleration=r72-(r144-r72)
                j=int(np.argmax(np.where(eligible,acceleration,-np.inf)))
                rows[1]=0;rows[1,j]=.12;expiry[1]=t+72
                updates[t,1]=True;entries[t,0]=True
        if good and (t-WARMUP)%168==0 and expiry[2]<0 and 2 not in expired and m168>0:
            ranked=sorted(range(4),key=lambda j:(-float(r168[j]),j))
            top,bottom=ranked[0],ranked[-1]
            if float(r168[top]-r168[bottom])>.08:
                rows[2]=0;rows[2,top]=.06;rows[2,bottom]=-.06;expiry[2]=t+168
                updates[t,2]=True;entries[t,1]=True
        if good and (t-WARMUP)%72==0 and expiry[3]<0 and 3 not in expired:
            if state=='STRESS':
                rows[3]=0;rows[3,0]=-.06;expiry[3]=t+72
                updates[t,3]=True;entries[t,2]=True
            elif state=='RECOVERY':
                j=int(np.argmax(r24));rows[3]=0;rows[3,j]=.06;expiry[3]=t+72
                updates[t,3]=True;entries[t,2]=True
        intents[t]=rows
        if np.abs(rows).sum()>.94+1e-10:raise ValueError('LJ_HIDDEN_GROSS')
    return intents,updates,entries,valid,regimes

def synthetic_causality():
    n=HOURS;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0001,.0002,.0003,.0004]])+.06*np.sin(t[:,None]/41+np.arange(4)))
    o=c*(1-.001*np.sin(t[:,None]/11+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);r=np.zeros_like(c);e=np.zeros_like(c,dtype=bool);e[::8]=True
    a=bundle(o,h,l,c,q,r,e)
    oo,hh,ll,cc,qq,rr=[z.copy() for z in (o,h,l,c,q,r)]
    for z in (oo,hh,ll,cc):z[14000:]*=1.7
    qq[14000:]*=3;rr[14000:]=-.001
    b=bundle(oo,hh,ll,cc,qq,rr,e)
    assert all(np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)),'LJ_FUTURE_LEAK'
    changed=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    assert not np.any(changed&~a[1][1:]),'LJ_SILENT_UPDATE'
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.94+1e-10
    q[1000,0]=0;bad=bundle(o,h,l,c,q,r,e)
    assert not bad[3][1001] and bad[3][1025] and not bad[3][1720]
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('LJ_SYNTHETIC_CAUSALITY_PASS')
