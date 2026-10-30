#!/usr/bin/env python3
"""HP preregistered causal range-compression breakout and stress cash-reserve seven-slot source.
Pinned Clean-4 hourly OHLC/quote/native funding, December 2022 warmup, 2023-24 training only.
"""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":.74,"TRANSITION":.72,"STRESS":.66}
PRIOR={"TREND":np.array([.55,.25,.12,.08]),
       "TRANSITION":np.array([.58,.17,.15,.10]),
       "STRESS":np.array([.55,.10,.10,.25])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HP_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        n24,n72,n336,n504=(net(t,w) for w in (24,72,336,504))
        hourly336=np.diff(lc[t-336:t+1],axis=0)
        semi336=np.maximum(np.sqrt(np.mean(np.minimum(hourly336,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n504/semi336,kind="stable")[:3]
        signals[t,0,leaders]=[.50,.30,.20]
        hourly168=np.diff(lc[t-168:t+1],axis=0)
        vol168=np.maximum(np.std(hourly168,axis=0),.002)
        prev_high=np.max(h[t-72:t],axis=0)
        log_range=np.log(h/l)
        range48=np.median(log_range[t-47:t+1],axis=0)
        range336=np.median(log_range[t-335:t+1],axis=0)
        compression=np.clip(range336/np.maximum(range48,1e-8),.5,2.)
        breakout=np.log(c[t]/prev_high)/vol168*compression
        signals[t,1,int(np.argmax(breakout))]=1.
        turnover336=q[t-335:t+1].sum(axis=0)
        liquid=np.argsort(-turnover336,kind="stable")[:3]
        burden=funding[t+1]-funding[t-335]
        signals[t,2,int(liquid[np.argmin(burden[liquid])])]=1.
        stress=(float(np.median(n72))<-.06 or float(np.median(n336))<-.12)
        # Signal encodes the independently financed Stress/Recovery sleeve.
        # In STRESS the physical allocator reserves its budget as USD cash;
        # this candidate signal is NOT traded. It is nonzero for source viability.
        semi168=np.maximum(np.sqrt(np.mean(np.minimum(hourly168,0.)**2,axis=0)),.002)
        signals[t,3,int(np.argmax(n24/semi168))]=1.
        regimes[t]="STRESS" if stress else "TREND" if np.count_nonzero(n504>0)>=3 else "TRANSITION"
        budgets[t]=PRIOR[regimes[t]]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or np.any(signals[t]<0) or np.any(budgets[t]<=0)
            or not all(np.isclose(signals[t,i].sum(),1.,atol=1e-12) for i in range(4))
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)):
            raise ValueError("HP_INVALID_SEVEN_SLOT_BOOK")
    return signals,updates,regimes,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    ix=np.arange(WARMUP,n,CLOCK)
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][ix].all(axis=1))
    assert np.allclose(a[0][ix,0].sum(axis=1),1.)
    assert np.allclose(a[0][ix,2].sum(axis=1),1.)
    assert np.all(a[3][ix]>0)
    return True

if __name__=="__main__":
    assert static_check()
    print("HP_CAUSAL_RANGE_COMPRESSION_STRESS_CASH_SOURCE_PASS")
