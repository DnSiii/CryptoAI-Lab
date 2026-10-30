#!/usr/bin/env python3
"""HM causal native executed taker-flow complete seven-slot source, 2023-2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.65}
PRIOR={"TREND":np.array([.55,.25,.15,.05]),
       "TRANSITION":np.array([.55,.20,.15,.10]),
       "STRESS":np.array([.50,.10,.15,.25])}
def bundle(opening,high,low,close,rate,event,quote,taker_buy_quote,taker_total_quote):
    o,h,l,c,r,e,q,b,v=[np.asarray(x,dtype=float) for x in
                       (opening,high,low,close,rate,event,quote,taker_buy_quote,taker_total_quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,b,v)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q,b,v)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any(b<0) or np.any(v<0) or
        np.any(b>v+1e-5) or not np.allclose(q,v,rtol=1e-9,atol=1e-7) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("HM_INVALID_PINNED_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    f=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(f[t+1]-f[t-w+1])
    def buyshare(t,w):
        return b[t-w+1:t+1].sum(axis=0)/np.maximum(v[t-w+1:t+1].sum(axis=0),1e-9)
    for t in range(WARMUP,n,CLOCK):
        n24,n96,n168,n336=(net(t,w) for w in (24,96,168,336))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        vol=np.maximum(np.std(hourly,axis=0),.002)
        core=np.argsort(-n336/semi,kind="stable")[:2]
        signals[t,0,core]=[.60,.40]
        current=buyshare(t,24)
        baseline=b[t-191:t-23].sum(axis=0)/np.maximum(v[t-191:t-23].sum(axis=0),1e-9)
        accel=current-baseline
        eligible=np.flatnonzero((accel>.02)&(n168>0))
        if len(eligible):
            j=int(eligible[np.argmax(accel[eligible])])
            signals[t,1,j]=1.
        burden=f[t+1]-f[t-167]
        signals[t,2,int(np.argmin(burden/vol))]=1.
        stress=float(np.median(n168))<0. or float(np.mean(current))<.47
        if stress:
            candidates=np.flatnonzero(n24>n96/4.)
            if not len(candidates):candidates=np.arange(4)
            j=int(candidates[np.argmax(current[candidates])])
            signals[t,3,j]=1.
        regimes[t]="STRESS" if stress else "TREND" if np.count_nonzero(n336>0)>=3 and float(np.mean(current))>.50 else "TRANSITION"
        budgets[t]=PRIOR[regimes[t]]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or np.any(signals[t]<0) or np.any(budgets[t]<=0)
            or not np.isclose(signals[t,0].sum(),1.,atol=1e-12)
            or not np.isclose(signals[t,2].sum(),1.,atol=1e-12)
            or not all(np.isclose(signals[t,i].sum(),0.) or np.isclose(signals[t,i].sum(),1.) for i in (1,3))
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)):
            raise ValueError("HM_INVALID_EXPERT_BOOK")
    return signals,updates,regimes,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    b=q*(.50+.07*np.sin(t[:,None]/19.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,b,q)
    c2,o2,h2,l2,q2,r2,b2=[x.copy() for x in (c,o,h,l,q,r,b)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;b2[3200:]*=4.;r2[3200:]*=-1.
    z=bundle(o2,h2,l2,c2,r2,e,q2,b2,q2)
    for i in range(4):assert np.array_equal(a[i][:3200],z[i][:3200]),i
    ix=np.arange(WARMUP,n,CLOCK)
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][ix].all(axis=1))
    assert np.allclose(a[0][ix,0].sum(axis=1),1.)
    assert np.allclose(a[0][ix,2].sum(axis=1),1.)
    assert np.all(a[3][ix]>=0)
    return True
if __name__=="__main__":
    assert static_check()
    print("HM_CAUSAL_NATIVE_EXECUTED_TAKER_FLOW_SOURCE_PASS")
