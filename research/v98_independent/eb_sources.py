#!/usr/bin/env python3
"""EB joint causal analytical log-utility allocation for seven-slot physical portfolio."""
import numpy as np

WARMUP=1440
GRID=168
BUDGETS={
    "EXPANSION":(3.00,.30,.25,.25),
    "TRANSITION":(2.60,.25,.30,.30),
    "STRESS":(1.10,.18,.30,.45),
}
UTILITY_FRICTION=.005
UTILITY_SCALE=.020
MARGINAL_PROBE_SHARE=.10

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EB_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=np.mean(hourly,axis=1)
    clv=(c-l)/np.maximum(h-l,1e-10)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,GRID):
        f336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        f168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        f84=np.sum(r[t-83:t+1]*e[t-83:t+1],axis=0)
        net336=lc[t]-lc[t-336]-f336
        net168=lc[t]-lc[t-168]-f168
        net84=lc[t]-lc[t-84]-f84
        market24=float(np.sum(market[t-23:t+1]))
        vol48=float(np.std(market[t-47:t+1]))
        vol336=float(np.std(market[t-335:t+1]))
        ratio=vol48/max(vol336,1e-8)
        breadth=int(np.count_nonzero(net336>0))
        regime=("STRESS" if ratio>1.25 and market24<0 else
                "EXPANSION" if breadth>=3 and market24>0 else "TRANSITION")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Long-run 84/336h native carry-adjusted dual-horizon participation.
        score=np.maximum(.5*(net84+net336),0.)
        trend=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.50*np.full(4,.25)+.50*trend
        # Candle location + abnormal quote-volume pressure (not acceleration).
        opportunities=[]
        for j in (1,2,3):
            location=float(np.mean(clv[t-23:t+1,j]))
            recent=float(np.mean(q[t-23:t+1,j]))
            baseline=float(np.mean(q[t-167:t-23,j]))
            ratioq=recent/max(baseline,1.)
            if location>.55 and ratioq>1.05 and net168[j]>0:
                opportunities.append(((location-.5)*ratioq,j))
        if opportunities:
            _,j=max(opportunities,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Funding-carry spread market-neutral; price divergence guard.
        low_j=int(np.argmin(f168));high_j=int(np.argmax(f168))
        price_spread=float((lc[t,low_j]-lc[t-168,low_j])-
                           (lc[t,high_j]-lc[t-168,high_j]))
        if low_j!=high_j and float(f168[high_j]-f168[low_j])>.0004 and abs(price_spread)<.15:
            signals[t,2,low_j]=.5;signals[t,2,high_j]=-.5
        # Volatility term-structure response, directional crash/rebound.
        if ratio>1.25 and market24<0:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif ratio>1.10 and market24>0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        # Joint causal marginal expected-log-wealth auction. Probe each sleeve
        # sequentially in preregistered Opportunity -> RV -> Stress order,
        # including previously admitted sleeve/covariance interactions.
        expected=.5*net336
        cov=np.cov(hourly[t-335:t+1],rowvar=False)*168.
        current=signals[t,0].copy()
        for i in (1,2,3):
            if not np.any(signals[t,i]):
                budgets[t,i]=0.
                continue
            delta=MARGINAL_PROBE_SHARE*(signals[t,i]-signals[t,0])
            proposal=current+delta
            utility=float(delta@expected-
                          .5*(proposal@cov@proposal-current@cov@current)-
                          UTILITY_FRICTION)
            z=float(np.clip(utility/UTILITY_SCALE,-30.,30.))
            multiplier=1./(1.+np.exp(-z))
            budgets[t,i]*=multiplier
            current+=multiplier*delta
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EB_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EB_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EB_BUDGET_INVALID")
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
    assert np.all(np.isfinite(a[3]))
    return True

if __name__=="__main__":
    assert static_check()
    print("EB_JOINT_CAUSAL_LOG_UTILITY_STATIC_PASS")
