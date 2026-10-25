#!/usr/bin/env python3
"""EC: asynchronous 168/48/72/24-hour causal seven-slot source; training only."""
import numpy as np

WARMUP=1440
CLOCKS=(168,48,72,24)
BUDGETS={
    "TREND":(3.00,.20,.18,.15),
    "MIXED":(2.50,.16,.15,.25),
    "RISK_OFF":(1.40,.05,.22,.40),
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
        raise ValueError("EC_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=np.mean(lc,axis=1)
    market_hourly=np.mean(hourly,axis=1)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,24):
        native504=np.sum(r[t-503:t+1]*e[t-503:t+1],axis=0)
        native72=np.sum(r[t-71:t+1]*e[t-71:t+1],axis=0)
        net504=lc[t]-lc[t-504]-native504
        net72=lc[t]-lc[t-72]-native72
        m72=float(market[t]-market[t-72])
        m504=float(market[t]-market[t-504])
        m24=float(market[t]-market[t-24])
        m6=float(market[t]-market[t-6])
        breadth=int(np.count_nonzero(net504>0))
        regime=("RISK_OFF" if m504<0 and m72<0 else
                "TREND" if breadth>=3 and m72>0 else "MIXED")
        regimes[t]=regime
        vol72=float(np.std(market_hourly[t-71:t+1]))
        multiplier=float(np.clip(.008/max(vol72,1e-8),.35,1.25))
        for i,clock in enumerate(CLOCKS):
            if (t-WARMUP)%clock:continue
            updates[t,i]=True
            budgets[t,i]=BUDGETS[regime][i]*(1. if i==0 else multiplier)
            if i==0:
                vol504=np.std(hourly[t-503:t+1],axis=0)
                score=np.where(net72>0,np.maximum(net504,0.),0.)/np.maximum(vol504,1e-8)
                weights=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
                signals[t,0]=.25*np.full(4,.25)+.75*weights
            elif i==1:
                options=[]
                for j in (1,2,3):
                    last6=float(lc[t,j]-lc[t-6,j])
                    previous12=float(lc[t-6,j]-lc[t-18,j])
                    vol6=float(np.mean(q[t-5:t+1,j]))
                    volprior=float(np.mean(q[t-77:t-5,j]))
                    if (net504[j]>0 and net72[j]>0 and previous12<0 and
                        last6>0 and vol6>=.9*volprior):
                        denom=float(np.std(hourly[t-503:t+1,j]))
                        options.append((float(net504[j]/max(denom,1e-8)),j))
                if options:
                    _,j=max(options,key=lambda z:(z[0],-z[1]))
                    signals[t,1,j]=1.
            elif i==2:
                hi=int(np.argmax(net72));lo=int(np.argmin(net72))
                if (hi!=lo and float(net72[hi]-net72[lo])>.02 and
                    float(np.min(q[t-71:t+1,[hi,lo]]))>0):
                    signals[t,2,hi]=.5;signals[t,2,lo]=-.5
            else:
                if m24<-.02 and m6>0:
                    signals[t,3,0]=.5;signals[t,3,3]=.5
                elif m72<-.05 and m6<0:
                    signals[t,3,0]=-.5;signals[t,3,3]=-.5
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EC_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EC_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EC_BUDGET_INVALID")
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
    print("EC_ASYNCHRONOUS_CAUSAL_STATIC_PASS")
