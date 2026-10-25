#!/usr/bin/env python3
"""DT causal online shadow contribution and breadth growth.
Independent complete seven-slot V98 training only; no 2025 or external engines.
"""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(2.8,.32,.28,.30),
         "MIXED":(2.3,.28,.24,.32),
         "RISK_OFF":(.9,.18,.30,.42)}
SHADOW_WEEKS=8
SHADOW_SEVERE_ROUND_TRIP=.010
SHADOW_FLOOR=.12

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DT_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    # Prior completed weekly shadow outcomes only; never an executable PnL claim.
    past_shadow=[[] for _ in range(4)]
    last_signal=None
    last_t=None
    for t in range(WARMUP,n,GRID):
        if last_t is not None:
            price=np.log(c[t]/c[last_t])
            funding=native[last_t+1:t+1].sum(axis=0)
            for i in range(1,4):
                w=last_signal[i]
                if np.any(w):
                    outcome=float(w@(price-funding)-
                                  SHADOW_SEVERE_ROUND_TRIP*np.sum(abs(w)))
                    past_shadow[i].append(outcome)
                    past_shadow[i]=past_shadow[i][-SHADOW_WEEKS:]
        ret24=lc[t]-lc[t-24]
        ret72=lc[t]-lc[t-72]
        ret168=lc[t]-lc[t-168]
        carry168=native[t-167:t+1].sum(axis=0)
        net168=ret168-carry168
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if net168[0]>0 and breadth>=3 else
                "RISK_OFF" if net168[0]<-.06 and breadth<=1 else "MIXED")
        regimes[t]=regime
        hourly=np.diff(lc[t-336:t+1],axis=0)
        vol=np.maximum(np.std(hourly,axis=0),.002)
        positive=(net168>0).astype(float)
        if regime=="RISK_OFF":
            positive*=0.
        risk_weights=positive/vol
        if risk_weights.sum()>0:
            signals[t,0]=risk_weights/risk_weights.sum()
        # Opportunity: new 168h high plus volume-confirmed 72h alt continuation.
        candidates=[]
        for j in (2,3):
            prior_high=float(np.max(h[t-168:t,j]))
            qr=float(q[t-71:t+1,j].mean()/max(q[t-312:t-72,j].mean(),1.))
            if c[t,j]>prior_high and ret72[j]>.015 and ret24[j]>.005 and qr>1.:
                candidates.append((float(ret72[j]),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # RV: realized-volatility spread, not prior price or funding rank.
        if regime!="RISK_OFF":
            order=sorted(range(4),key=lambda j:(float(vol[j]),j))
            calm,turbulent=order[0],order[-1]
            if vol[turbulent]/vol[calm]>1.35 and ret168[calm]>-.12:
                signals[t,2,calm]=.5
                signals[t,2,turbulent]=-.5
        # Stress: BTC/ETH protection after prior drawdown, signed recovery.
        btc_drawdown=float(c[t,0]/np.max(h[t-336:t,0])-1.)
        if btc_drawdown<-.10 and ret24[0]<0 and breadth<=2:
            signals[t,3,0]=-.5
            signals[t,3,1]=-.5
        elif btc_drawdown<-.10 and ret24[0]>.01 and ret72[0]>-.03:
            signals[t,3,0]=.5
            signals[t,3,1]=.5
        budgets[t,0]=BUDGETS[regime][0]
        for i in range(1,4):
            hist=past_shadow[i]
            qualified=(len(hist)>=4 and sum(x>0 for x in hist)>=2
                       and sum(hist)>0.)
            budgets[t,i]=BUDGETS[regime][i]*(1. if qualified else SHADOW_FLOOR)
        updates[t,:]=True
        last_signal=signals[t].copy()
        last_t=t
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DT_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DT_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DT_BUDGET_NONFINITE")
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
    print("DT_VOL_NORMALIZED_RESIDUAL_REVERSION_STATIC_PASS")
