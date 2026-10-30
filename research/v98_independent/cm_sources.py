#!/usr/bin/env python3
"""CM preregistered seven-slot downside semivariance and conditional downside beta.
No rejected architecture imports. Completed t close, trade earliest t+1 open.
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.90,.50,.25,.10]),
 "MIXED":np.array([1.40,.35,.30,.30]),
 "RISK_OFF":np.array([.65,.30,.40,.50]),
}
def semivar(returns):
    a=np.asarray(returns,dtype=float)
    up=np.mean(np.maximum(a,0.)**2,axis=0)
    down=np.mean(np.minimum(a,0.)**2,axis=0)
    return up,down,up/np.maximum(down,1e-12)

def bundle(close,rate,event):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or r.shape!=c.shape or e.shape!=c.shape
        or len(c)<=WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c<=0)
        or np.any((e!=0)&(e!=1))):
        raise ValueError("CM_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r504=np.diff(lc[t-504:t+1],axis=0)
        up,down,asym=semivar(r504)
        r168=lc[t]-lc[t-168]
        r672=lc[t]-lc[t-672]
        r24=lc[t]-lc[t-24]
        btc_negative=r504[:,0]<0
        if int(np.count_nonzero(btc_negative))>=10:
            b=r504[btc_negative,0]
            beta=(r504[btc_negative].T@b)/max(float(b@b),1e-12)
        else:
            beta=np.ones(4)
        regime=("RISK_ON" if r168[0]>0 and float(np.mean(up))>float(np.mean(down)) else
                "RISK_OFF" if r168[0]<0 and float(np.mean(down))>float(np.mean(up))
                else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%336==0:
            eligible=[j for j in range(4) if r672[j]>0 and asym[j]>1.]
            ranked=sorted(eligible,key=lambda j:(-asym[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.65
                signals[t,0,ranked[1]]=.35
            updates[t,0]=True
        candidates=[j for j in (2,3) if r168[j]<0 and r24[j]>0]
        if candidates:
            up168,down168,asym168=semivar(np.diff(lc[t-168:t+1],axis=0))
            winner=sorted(candidates,key=lambda j:(-asym168[j],j))[0]
            signals[t,1,winner]=1.
        updates[t,1]=True
        ranked=sorted(range(4),key=lambda j:(beta[j],j))
        if int(np.count_nonzero(btc_negative))>=10 and beta[ranked[-1]]-beta[ranked[0]]>.05:
            signals[t,2,ranked[0]]=.5
            signals[t,2,ranked[-1]]=-.5
        updates[t,2]=True
        if int(np.count_nonzero(r168<0))>=2:
            most_sensitive=ranked[-1]
            market24=float(np.mean(r24))
            if market24>0:signals[t,3,most_sensitive]=1.
            elif market24<0:signals[t,3,most_sensitive]=-1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CM_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CM_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    s2,m2,z2=bundle(changed,rates,e)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True
if __name__=="__main__":
    assert static_check()
    print("CM_CAUSAL_DOWNSIDE_SEMIVARIANCE_SOURCE_PASS")
