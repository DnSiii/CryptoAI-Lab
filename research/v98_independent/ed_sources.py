#!/usr/bin/env python3
"""ED: native funding dispersion, breakout and volatility-shock seven-slot causal source; training only."""
import numpy as np
WARMUP=1440
CLOCKS=(168,48,72,24)
BUDGETS={"TREND":(3.20,.18,.12,.08),"MIXED":(2.80,.18,.16,.15),"RISK_OFF":(1.70,.10,.18,.28)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("ED_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=np.mean(lc,axis=1)
    market_hourly=np.mean(hourly,axis=1)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,24):
        native336=np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        native168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net336=lc[t]-lc[t-336]-native336
        net168=lc[t]-lc[t-168]-native168
        m168=float(market[t]-market[t-168])
        breadth=int(np.count_nonzero(net336>0))
        regime=("RISK_OFF" if m168<0 and breadth<=1 else
                "TREND" if breadth>=3 and m168>0 else "MIXED")
        regimes[t]=regime
        vol168=float(np.std(market_hourly[t-167:t+1]))
        multiplier=float(np.clip(.008/max(vol168,1e-8),.40,1.20))
        for i,clock in enumerate(CLOCKS):
            if (t-WARMUP)%clock:continue
            updates[t,i]=True
            budgets[t,i]=BUDGETS[regime][i]*(1. if i==0 else multiplier)
            if i==0:
                vol336=np.std(hourly[t-335:t+1],axis=0)
                price48=lc[t]-lc[t-48]
                score=np.where(price48>0,np.maximum(net336,0.),0.)/np.maximum(vol336,1e-8)
                weights=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
                signals[t,0]=.35*np.full(4,.25)+.65*weights
            elif i==1:
                options=[]
                for j in (1,2,3):
                    price24=float(lc[t,j]-lc[t-24,j])
                    volume24=float(np.mean(q[t-23:t+1,j]))
                    volumeprior=float(np.mean(q[t-119:t-23,j]))
                    prior96high=float(np.max(h[t-96:t,j]))
                    if (net168[j]>0 and price24>0 and c[t,j]>prior96high and
                        volume24>=.75*volumeprior):
                        denom=float(np.std(hourly[t-167:t+1,j]))
                        options.append((float(net168[j]/max(denom,1e-8)),j))
                if options:
                    _,j=max(options,key=lambda z:(z[0],-z[1]))
                    signals[t,1,j]=1.
            elif i==2:
                carry=native168
                lo=int(np.argmin(carry));hi=int(np.argmax(carry))
                relative24=float((lc[t,lo]-lc[t-24,lo])-(lc[t,hi]-lc[t-24,hi]))
                if lo!=hi and float(carry[hi]-carry[lo])>.00025 and relative24>0:
                    signals[t,2,lo]=.5;signals[t,2,hi]=-.5
            else:
                vol24=float(np.std(market_hourly[t-23:t+1]))
                m12=float(market[t]-market[t-12])
                if vol24>1.25*max(vol168,1e-8):
                    if m12>.006:
                        signals[t,3,0]=.5;signals[t,3,3]=.5
                    elif m12<-.006:
                        signals[t,3,0]=-.5;signals[t,3,3]=-.5
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("ED_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("ED_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("ED_BUDGET_INVALID")
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
    for i,clock in enumerate(CLOCKS):
        assert np.array_equal(np.flatnonzero(a[1][:,i]),np.arange(WARMUP,n,clock))
    return True

if __name__=="__main__":
    assert static_check()
    print("ED_CARRY_BREAKOUT_SHOCK_CAUSAL_STATIC_PASS")
