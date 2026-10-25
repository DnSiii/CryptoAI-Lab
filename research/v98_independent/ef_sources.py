#!/usr/bin/env python3
"""EF: liquidity-flow opportunity, beta-residual leadership and shock dispersion hedge; causal training only."""
import numpy as np
WARMUP=1440
CLOCKS=(168,72,96,24)
BUDGETS={"TREND":(3.10,.14,.12,.15),"MIXED":(2.60,.17,.16,.20),"RISK_OFF":(1.60,.09,.18,.25)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EF_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=np.mean(lc,axis=1)
    market_hourly=np.mean(hourly,axis=1)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,24):
        native240=np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
        native168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        net240=lc[t]-lc[t-240]-native240
        net168=lc[t]-lc[t-168]-native168
        m48=float(market[t]-market[t-48])
        breadth=int(np.count_nonzero(net240>0))
        regime=("RISK_OFF" if m48<0 and breadth<=1 else
                "TREND" if breadth>=3 and m48>0 else "MIXED")
        regimes[t]=regime
        vol168=float(np.std(market_hourly[t-167:t+1]))
        multiplier=float(np.clip(.008/max(vol168,1e-8),.35,1.20))
        for i,clock in enumerate(CLOCKS):
            if (t-WARMUP)%clock:continue
            updates[t,i]=True
            budgets[t,i]=BUDGETS[regime][i]*(1. if i==0 else multiplier)
            if i==0:
                h240=hourly[t-239:t+1]
                downside=np.sqrt(np.mean(np.minimum(h240,0.)**2,axis=0))
                score=np.where(lc[t]-lc[t-48]>0,np.maximum(net240,0.),0.)/np.maximum(downside,1e-6)
                weights=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
                signals[t,0]=.15*np.full(4,.25)+.85*weights
            elif i==1:
                options=[]
                for j in (1,2,3):
                    price24=float(lc[t,j]-lc[t-24,j])
                    v24=q[t-23:t+1,j]
                    pressure=float(np.sum(hourly[t-23:t+1,j]*v24)/max(np.sum(v24),1e-8))
                    prior=float(np.mean(q[t-191:t-23,j]))
                    if (net168[j]>0 and price24>0 and pressure>.00015 and
                        float(np.mean(v24))>=.80*prior):
                        vol=float(np.std(hourly[t-167:t+1,j]))
                        options.append((pressure/max(vol,1e-8),j))
                if options:
                    _,j=max(options,key=lambda z:(z[0],-z[1]))
                    signals[t,1,j]=1.
            elif i==2:
                x=hourly[t-335:t+1,0]
                x0=x-float(np.mean(x))
                var=float(x0@x0)
                beta=np.zeros(4)
                for j in (1,2,3):
                    y=hourly[t-335:t+1,j]
                    beta[j]=float(x0@(y-float(np.mean(y))))/max(var,1e-12)
                residual96=np.array([(lc[t,j]-lc[t-96,j])-beta[j]*(lc[t,0]-lc[t-96,0]) for j in range(4)])
                residual24=np.array([(lc[t,j]-lc[t-24,j])-beta[j]*(lc[t,0]-lc[t-24,0]) for j in range(4)])
                hi=max((1,2,3),key=lambda j:(residual96[j],-j))
                lo=min((1,2,3),key=lambda j:(residual96[j],j))
                if (hi!=lo and residual96[hi]-residual96[lo]>.012 and
                    residual24[hi]-residual24[lo]>0):
                    signals[t,2,hi]=.5;signals[t,2,lo]=-.5
            else:
                vol24=float(np.std(market_hourly[t-23:t+1]))
                price24=lc[t]-lc[t-24]
                hi=int(np.argmax(price24));lo=int(np.argmin(price24))
                if (vol24>1.2*max(vol168,1e-8) and hi!=lo and
                    float(price24[hi]-price24[lo])>.025):
                    signals[t,3,hi]=.5;signals[t,3,lo]=-.5
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EF_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EF_RV_NOT_NEUTRAL")
    if not np.allclose(signals[:,3,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EF_STRESS_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EF_BUDGET_INVALID")
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
    print("EF_FLOW_RESIDUAL_DISPERSION_CAUSAL_STATIC_PASS")
