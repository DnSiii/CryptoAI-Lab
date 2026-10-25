#!/usr/bin/env python3
"""DY cross-sectional growth and flight-to-quality spread engine, training-only."""
import numpy as np

WARMUP=1440
GRID=168
BUDGETS={
    "EXPANSION":(3.10,.32,.20,.24),
    "TRANSITION":(2.90,.28,.24,.24),
    "FLIGHT":(2.00,.16,.22,.38),
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
        raise ValueError("DY_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U10");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72]
        funding168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net168=r168-funding168
        breadth=int(np.count_nonzero(net168>0))
        market72=float(np.mean(r72))
        btc_sol_spread72=float(r72[0]-r72[3])
        regime=("FLIGHT" if market72<-.02 and btc_sol_spread72>.01 else
                "EXPANSION" if breadth>=3 and market72>0 else "TRANSITION")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Growth Core: asset-agnostic equal-weight long four-asset risk premium.
        signals[t,0]=[.25,.25,.25,.25]
        # Opportunity: native-carry-adjusted medium-horizon alt trend with
        # prior/current completed-hour volume confirmation, not a new-high
        # trigger or short-term acceleration.
        candidates=[]
        for j in (1,2,3):
            q_recent=float(np.mean(q[t-71:t+1,j]))
            q_prior=float(np.mean(q[t-143:t-71,j]))
            if (net168[j]>.01 and r72[j]>0 and
                q_recent/max(q_prior,1.)>.75):
                candidates.append((float(net168[j]),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Relative value: market-neutral cross-sectional medium-horizon
        # persistence (not native funding spread or 24h price reversal).
        strong=max(range(4),key=lambda j:(float(net168[j]),-j))
        weak=min(range(4),key=lambda j:(float(net168[j]),j))
        if (strong!=weak and float(net168[strong]-net168[weak])>.04
            and net168[strong]>.02):
            signals[t,2,strong]=.5
            signals[t,2,weak]=-.5
        # Stress/recovery: BTC-versus-SOL relative quality rotation, neutral
        # to the common market, rather than an outright short or crash bounce.
        if market72<0 and btc_sol_spread72>.01:
            signals[t,3,0]=.5;signals[t,3,3]=-.5
        elif market72>0 and btc_sol_spread72<-.01:
            signals[t,3,0]=-.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DY_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DY_RV_NOT_NEUTRAL")
    if not np.allclose(signals[:,3,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DY_STRESS_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DY_BUDGET_INVALID")
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
    print("DY_FLIGHT_QUALITY_CROSS_SECTIONAL_STATIC_PASS")
