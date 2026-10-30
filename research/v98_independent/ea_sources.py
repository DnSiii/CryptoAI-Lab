#!/usr/bin/env python3
"""EA: preregistered causal cross-horizon growth, acceleration, beta-residual fade and drawdown response.
No V99, future holdout, rejected architecture signals, or actual realized sleeve PnL.
"""
import numpy as np

WARMUP=1440
GRID=168
BUDGETS={
    "EXPANSION":(3.10,.30,.20,.20),
    "TRANSITION":(2.70,.25,.22,.30),
    "CRISIS":(1.20,.15,.25,.45),
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
        raise ValueError("EA_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=np.mean(lc,axis=1)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,GRID):
        native336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        native168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net336=lc[t]-lc[t-336]-native336
        net168=lc[t]-lc[t-168]-native168
        r24=lc[t]-lc[t-24]
        prev24=lc[t-24]-lc[t-48]
        market24=float(market[t]-market[t-24])
        dd336=float(market[t]-np.max(market[t-335:t+1]))
        breadth=int(np.count_nonzero(net336>0))
        regime=("CRISIS" if dd336<-.08 and market24<0 else
                "EXPANSION" if breadth>=3 and market24>0 else "TRANSITION")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Long-run growth: realized-risk-adjusted positive native net 336h trend.
        vol336=np.std(hourly[t-335:t+1],axis=0)
        score=np.maximum(net336,0.)/np.maximum(vol336,1e-6)
        trend=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.20*np.full(4,.25)+.80*trend
        # Intraday acceleration sleeve: volume-supported acceleration in a
        # positive weekly native net trend. No price breakout high or PnL fit.
        accel=(r24-prev24)/np.maximum(vol336*np.sqrt(24.),1e-6)
        valid=[]
        for j in (1,2,3):
            recent=float(np.mean(q[t-23:t+1,j]))
            prior=float(np.mean(q[t-47:t-23,j]))
            if net168[j]>0 and r24[j]>0 and accel[j]>0 and recent>=.50*prior:
                valid.append((float(accel[j]),j))
        if valid:
            _,j=max(valid,key=lambda v:(v[0],-v[1]))
            signals[t,1,j]=1.
        # 336 completed-hour BTC beta, clipped and fully gross-normalized.
        btc=hourly[t-335:t+1,0]
        variance=float(np.mean((btc-btc.mean())**2))
        residual=[]
        for j in (1,2,3):
            alt=hourly[t-335:t+1,j]
            beta=float(np.mean((alt-alt.mean())*(btc-btc.mean()))/
                       max(variance,1e-12))
            beta=float(np.clip(beta,.25,2.))
            residual.append((float(r24[j]-beta*r24[0]),j,beta))
        val,j,beta=max(residual,key=lambda v:(abs(v[0]),-v[1]))
        if abs(val)>.01:
            # Fade positive residual: short alt / long beta-weighted BTC.
            side=-1. if val>0 else 1.
            signals[t,2,j]=side/(1.+beta)
            signals[t,2,0]=-side*beta/(1.+beta)
        # Path-dependent stress/recovery with distinct directional exposures.
        if dd336<-.06 and market24<0:
            signals[t,3,1]=-.5;signals[t,3,3]=-.5
        elif dd336<-.04 and market24>0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EA_SOURCE_GROSS")
    if np.any(np.abs(signals[:,2,:].sum(axis=1))>1.+1e-12):
        raise ValueError("EA_RV_INVALID")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EA_BUDGET_INVALID")
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
    assert np.all(a[1][a[1]>0]>=0)
    return True

if __name__=="__main__":
    assert static_check()
    print("EA_CROSS_HORIZON_SEVENSLOT_STATIC_PASS")
