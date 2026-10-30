#!/usr/bin/env python3
"""CZ causal cross-horizon relative trend, range escape, breadth acceleration,
and prior-only net directional shadow allocator. TRAINING 2022-2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BASE_BUDGETS={
 "RISK_ON":np.array([2.1,.45,.50,.25]),
 "MIXED":np.array([1.6,.40,.55,.40]),
 "RISK_OFF":np.array([.55,.30,.55,.70]),
}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("CZ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    prev=np.zeros((4,4))
    pending=np.zeros(4)
    shadow=np.zeros((n,4))
    for t in range(1,n):
        # Previous completed-close signal, prior-only native funding, and delayed cost.
        shadow[t]=prev@(hourly[t]-native[t])-pending
        pending[:]=0.
        if t<WARMUP or (t-WARMUP)%GRID:
            continue
        ret168=lc[t]-lc[t-168]
        ret336=lc[t]-lc[t-336]
        f336=native[t-335:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(ret336-f336>0))
        regime=("RISK_ON" if breadth>=3 and ret168[0]>0 else
                "RISK_OFF" if breadth<=1 and ret168[0]<0 else "MIXED")
        regimes[t]=regime
        score=shadow[t-335:t+1].sum(axis=0) if t>=WARMUP+336 else None
        scales=np.ones(4) if score is None else np.array(
            [1.,*np.where(score[1:]>0,1.15,.35)])
        budgets[t]=BASE_BUDGETS[regime]*scales
        if (t-WARMUP)%336==0:
            net504=lc[t]-lc[t-504]-native[t-503:t+1].sum(axis=0)
            net168=ret168-native[t-167:t+1].sum(axis=0)
            strength=np.sqrt(np.maximum(net504[[0,1,3]],0.)*
                             np.maximum(net168[[0,1,3]],0.))
            if strength.sum()>0:
                signals[t,0,[0,1,3]]=strength/strength.sum()
            updates[t,0]=True
        # Range escape uses prior 240 hours ending 48 hours before the signal.
        options=[]
        for j in (2,3):
            hi=float(np.max(h[t-288:t-48,j]))
            lo=float(np.min(l[t-288:t-48,j]))
            displacement=(float(c[t,j])-hi) if c[t,j]>hi else (
                float(c[t,j])-lo if c[t,j]<lo else 0.)
            v_new=float(q[t-47:t+1,j].mean())
            v_old=float(q[t-288:t-48,j].mean())
            ret48=float(lc[t,j]-lc[t-48,j])
            if (displacement>0 and ret48>0 or displacement<0 and ret48<0) and v_new>v_old:
                options.append((abs(displacement)/max(hi-lo,1e-9),j,
                                1. if displacement>0 else -1.))
        if options:
            _,j,direction=max(options,key=lambda x:(x[0],-x[1]))
            signals[t,1,j]=direction
        updates[t,1]=True
        # BTC/SOL beta spread: same-sign 168h and 504h carry-adjusted ratio drift.
        rel504=(lc[t,3]-lc[t-504,3])-(lc[t,0]-lc[t-504,0])
        rel504-=float((native[t-503:t+1,3]-native[t-503:t+1,0]).sum())
        rel168=(lc[t,3]-lc[t-168,3])-(lc[t,0]-lc[t-168,0])
        rel168-=float((native[t-167:t+1,3]-native[t-167:t+1,0]).sum())
        if rel504*rel168>0:
            direction=float(np.sign(rel168))
            signals[t,2,3]=.5*direction
            signals[t,2,0]=-.5*direction
        updates[t,2]=True
        # Breadth acceleration: not static crisis state.
        now=lc[t]-lc[t-72]
        before=lc[t-72]-lc[t-144]
        change=int(np.count_nonzero(now>0))-int(np.count_nonzero(before>0))
        if change<=-2 and ret168[0]<0:
            signals[t,3,int(np.argmin(now))]=-1.
        elif change>=2 and ret168[0]>0:
            signals[t,3,int(np.argmax(now))]=1.
        updates[t,3]=True
        for i in np.flatnonzero(updates[t]):
            pending[i]=.002*np.sum(np.abs(signals[t,i]-prev[i]))
            prev[i]=signals[t,i].copy()
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CZ_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CZ_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("CZ_BUDGET_NONFINITE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2=c.copy();o2=o.copy();h2=h.copy();l2=l.copy()
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2=q.copy();q2[3200:]*=4.
    r2=r.copy();r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    return True
if __name__=="__main__":
    assert static_check()
    print("CZ_CAUSAL_SOURCE_STATIC_PASS")
