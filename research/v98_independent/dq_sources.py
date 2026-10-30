#!/usr/bin/env python3
"""DQ independent altcoin network-premium basket, BTC momentum opportunity,
BNB/SOL spread reversion and broad-stress overlay. TRAINING ONLY.
"""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(3.1,.35,.28,.24),
         "MIXED":(2.1,.28,.32,.38),
         "RISK_OFF":(1.2,.20,.38,.50)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DQ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    spread=lc[:,2]-lc[:,3]
    for t in range(WARMUP,n,GRID):
        ret336=lc[t]-lc[t-336]
        ret168=lc[t]-lc[t-168]
        ret72=lc[t]-lc[t-72]
        ret24=lc[t]-lc[t-24]
        net168=ret168-native[t-167:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(net168[1:]>0))
        regime=("RISK_ON" if ret336[0]>0 and breadth>=2 else
                "RISK_OFF" if ret336[0]<-.05 and breadth<=1 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Growth: diversified non-BTC high-beta network-adoption premium.
        # Equal-weight ETH/BNB/SOL is structural, no historical winner selection.
        signals[t,0]=[0.,1./3.,1./3.,1./3.]
        # Opportunity: BTC liquidity-led breakout above a *prior* 168h high.
        old_high=float(h[t-240:t-72,0].max())
        qratio=float(q[t-71:t+1,0].mean()/max(q[t-312:t-72,0].mean(),1.))
        if c[t,0]>old_high and net168[0]>.01 and ret72[0]>.015 and qratio>1.02:
            signals[t,1,0]=1.
        # RV: BNB/SOL relative price spread reverting after 24h turn,
        # carry veto. Not DP's cross-sectional momentum spread.
        base=spread[t-672:t-24]
        sd=float(base.std())
        z=float((spread[t]-base.mean())/sd) if sd>1e-8 else 0.
        turn=float(spread[t]-spread[t-24])
        carry=float((native[t-167:t+1,2]-native[t-167:t+1,3]).sum())
        if abs(z)>1.0 and z*turn<0 and abs(carry)<.004:
            direction=-float(np.sign(z))
            signals[t,2,2]=.5*direction
            signals[t,2,3]=-.5*direction
        # Stress: dynamic BTC/SOL defensive hedge or broad altcoin recovery.
        if ret72[0]<-.035 and breadth<=1:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif ret72[0]<-.025 and ret24[0]>.01:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        elif breadth>=2 and np.count_nonzero(ret24[1:]>0)>=2:
            signals[t,3,1]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DQ_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DQ_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DQ_BUDGET_NONFINITE")
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
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    return True
if __name__=="__main__":
    assert static_check()
    print("DQ_ALT_NETWORK_PREMIUM_SOURCE_STATIC_PASS")
