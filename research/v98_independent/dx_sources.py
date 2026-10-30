#!/usr/bin/env python3
"""DX causal carry-divergence overlay with breakout opportunity and confirmed shock recovery.
All signals are from completed historical bars; no 2025+, no benchmarks.
"""
import numpy as np

WARMUP=1440
GRID=168
BUDGETS={
    "EXPANSION":(3.30,.32,.20,.18),
    "TRANSITION":(2.80,.24,.24,.24),
    "PANIC":(1.10,.12,.28,.40),
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
        raise ValueError("DX_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U10");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72]
        r24=lc[t]-lc[t-24]
        r6=lc[t]-lc[t-6]
        funding168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net168=r168-funding168
        breadth=int(np.count_nonzero(net168>0))
        market72=float(np.mean(r72))
        market6=float(np.mean(r6))
        regime=("PANIC" if market72<-.05 and breadth<=1 else
                "EXPANSION" if breadth>=3 else "TRANSITION")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Core: unconditional strategic market beta, not a selected former champion.
        signals[t,0]=[.40,.25,.15,.20]
        # Opportunity: capital into fresh 168h *closing* high, positive native
        # carry-adjusted leadership, and a current 72h liquidity confirmation.
        candidates=[]
        for j in (1,2,3):
            q_recent=float(np.mean(q[t-71:t+1,j]))
            q_prior=float(np.mean(q[t-143:t-71,j]))
            volume_ratio=q_recent/max(q_prior,1.)
            if (net168[j]>.015 and r72[j]>0 and r24[j]>0 and
                c[t,j]>np.max(c[t-168:t,j]) and volume_ratio>.85):
                candidates.append((float(net168[j]),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Relative value: native funding spread harvest only when relative
        # trend parity limits price-trend adverse selection. Not price reversion.
        cheap=min(range(4),key=lambda j:(float(funding168[j]),j))
        dear=max(range(4),key=lambda j:(float(funding168[j]),-j))
        if (cheap!=dear and float(funding168[dear]-funding168[cheap])>.001
            and float(net168[cheap]-net168[dear])>-.03
            and float(r72[cheap])>-.06):
            signals[t,2,cheap]=.5
            signals[t,2,dear]=-.5
        # Stress/recovery: after broad 72h drawdown, buy confirmed six-hour
        # rebound; only short a still-unconfirmed deep crash with weak breadth.
        if market72<-.008 and market6>0:
            signals[t,3,0]=.5;signals[t,3,1]=.5
        elif market72<-.04 and market6<0 and breadth<=1:
            signals[t,3,0]=-.5;signals[t,3,1]=-.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DX_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DX_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DX_BUDGET_INVALID")
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
    return True
if __name__=="__main__":
    assert static_check()
    print("DX_CARRY_DIVERGENCE_SHOCK_RECOVERY_STATIC_PASS")
