#!/usr/bin/env python3
"""DP strategic BTC liquidity-anchor plus conditional convex rotation; TRAINING ONLY.
Independent new seven-slot system; rejected DO/DN signals and parameters not imported.
"""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(2.8,.42,.30,.25),
         "MIXED":(2.3,.34,.30,.32),
         "RISK_OFF":(1.6,.18,.32,.50)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DP_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        ret168=lc[t]-lc[t-168]
        ret72=lc[t]-lc[t-72]
        ret24=lc[t]-lc[t-24]
        net168=ret168-native[t-167:t+1].sum(axis=0)
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if net168[0]>0 and breadth>=2 else
                "RISK_OFF" if net168[0]<-.05 and breadth<=1 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Growth: persistent, BTC-anchored liquid crypto risk premium.
        # Not a trend timing rule or equal-weight four-asset basket.
        signals[t,0]=([.70,.20,.10,0.] if regime!="RISK_OFF" else
                      [.80,.15,.05,0.])
        # Opportunity: convex SOL/BNB expansion above prior completed range,
        # with positive native-carry-adjusted momentum and quote participation.
        candidates=[]
        for j in (2,3):
            past_high=float(np.max(h[t-240:t-72,j]))
            recent_q=float(np.mean(q[t-71:t+1,j]))
            prior_q=float(np.mean(q[t-312:t-72,j]))
            if (c[t,j]>past_high and net168[j]>.01 and
                ret72[j]>.02 and recent_q>1.02*prior_q):
                candidates.append((float(ret72[j]*recent_q/max(prior_q,1.)),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # RV: signed *cross-sectional continuation* after 168h dispersion.
        # Neutral pair and carry veto, not DO's funding-spread mean bet.
        order=sorted(range(4),key=lambda j:(-float(net168[j]),j))
        winner,loser=order[0],order[-1]
        carry=native[t-167:t+1].sum(axis=0)
        if (net168[winner]-net168[loser]>.045 and
            net168[winner]>0 and
            carry[winner]-carry[loser]<.004):
            signals[t,2,winner]=.5;signals[t,2,loser]=-.5
        # Stress: direction-confirmed, short-lived crash continuation
        # versus post-crash recovery. Not a permanent beta overlay.
        if ret72[0]<-.045 and ret24[0]<-.01:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif ret72[0]<-.025 and ret24[0]>.015:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        elif breadth>=3 and ret24[0]>.025 and ret72[0]>0:
            signals[t,3,1]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DP_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DP_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DP_BUDGET_NONFINITE")
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
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("DP_LIQUIDITY_ANCHOR_CONVEX_ROTATION_SOURCE_STATIC_PASS")
