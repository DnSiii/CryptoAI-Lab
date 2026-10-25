#!/usr/bin/env python3
"""CV independent volatility-normalized breadth core, intratrend pullback,
cross-asset volatility dispersion and breadth-shock hedge. Training only.
"""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BUDGETS={
    "RISK_ON":np.array([2.25,.30,.25,.15]),
    "MIXED":np.array([1.70,.30,.35,.35]),
    "RISK_OFF":np.array([.60,.20,.40,.65]),
}
def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(a.shape!=c.shape for a in (r,e,q)) or
        any(not np.isfinite(a).all() for a in (c,r,e,q)) or
        np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CV_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        ret672=lc[t]-lc[t-672]
        ret336=lc[t]-lc[t-336]
        ret168=lc[t]-lc[t-168]
        ret72=lc[t]-lc[t-72]
        ret24=lc[t]-lc[t-24]
        ret6=lc[t]-lc[t-6]
        hourly=np.diff(lc[t-336:t+1],axis=0)
        vol=np.maximum(np.std(hourly,axis=0),.0005)
        vol72=float(np.std(hourly[-72:,0]))
        vol336=float(np.std(hourly[:,0]))
        breadth=int(np.count_nonzero(ret168>0))
        regime=("RISK_ON" if ret672[0]>0 and vol72<vol336 else
                "RISK_OFF" if ret672[0]<0 and vol72>=vol336 else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%336==0:
            eligible=np.array([(ret672[j]>0 and ret168[j]>0) for j in range(4)])
            if eligible.any():
                weights=np.where(eligible,1./vol,0.)
                signals[t,0]=weights/weights.sum()
            updates[t,0]=True
        candidates=[]
        for j in (2,3):
            recent=float(q[t-23:t+1,j].sum())
            prior=float(q[t-47:t-23,j].sum())
            if ret336[j]>0 and ret24[j]<0 and ret6[j]>0 and recent>=.6*prior:
                candidates.append(j)
        if candidates:
            best=sorted(candidates,key=lambda j:(-ret6[j],j))[0]
            signals[t,1,best]=1.
        updates[t,1]=True
        low=int(np.argmin(vol))
        high=int(np.argmax(vol))
        if low!=high and vol[high]/vol[low]>1.15:
            signals[t,2,low]=.5
            signals[t,2,high]=-.5
        updates[t,2]=True
        negative=int(np.count_nonzero(ret168<0))
        if negative>=3:
            weakest=int(np.argmin(ret72))
            signals[t,3,weakest]=-1.
        elif ret168[0]<0 and ret24[0]>0 and breadth>=2:
            signals[t,3,0]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CV_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CV_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes
def static_check():
    n=4000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c)
    e[::8]=1.
    s,m,z=bundle(c,r,e,q)
    changed=c.copy()
    changed[2900:]*=1.9
    rates=r.copy()
    rates[2900:]*=-1.
    volumes=q.copy()
    volumes[2900:]*=4.
    s2,m2,z2=bundle(changed,rates,e,volumes)
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
    print("CV_CAUSAL_SOURCE_STATIC_PASS")
