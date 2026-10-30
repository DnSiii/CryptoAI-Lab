#!/usr/bin/env python3
"""HO causal native executed taker-flow complete seven-slot source, 2023-2024 only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.65}
PRIOR={"TREND":np.array([.52,.20,.18,.10]),
       "TRANSITION":np.array([.50,.20,.15,.15]),
       "STRESS":np.array([.42,.15,.13,.30])}
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
        raise ValueError("HO_INVALID_PINNED_NATIVE_SOURCE")
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
        n24,n72,n168,n336,n504=(net(t,w) for w in (24,72,168,336,504))
        hourly=np.diff(lc[t-336:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        core=np.argsort(-n504/semi,kind="stable")[:3]
        signals[t,0,core]=[.50,.30,.20]
        buy72=buyshare(t,72)
        absorption=(buy72-buy72.mean())-.25*(n72-n72.mean())
        signals[t,1,int(np.argmax(absorption))]=1.
        turnover336=q[t-335:t+1].sum(axis=0)
        liquid=np.argsort(-turnover336,kind="stable")[:3]
        burden=f[t+1]-f[t-335]
        signals[t,2,int(liquid[np.argmin(burden[liquid])])]=1.
        stress=float(np.median(n168))<0. or float(np.mean(buy72))<.49
        if stress:
            resilient=np.flatnonzero(n24>0)
            if not len(resilient):resilient=np.arange(4)
            signals[t,3,int(resilient[np.argmin(buy72[resilient])])]=1.
        else:
            signals[t,3,int(np.argmax(n72/semi))]=1.
        regimes[t]="STRESS" if stress else "TREND" if np.count_nonzero(n504>0)>=3 and float(np.mean(buy72))>=.50 else "TRANSITION"
        budgets[t]=PRIOR[regimes[t]]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or np.any(signals[t]<0) or np.any(budgets[t]<=0)
            or not np.isclose(signals[t,0].sum(),1.,atol=1e-12)
            or not np.isclose(signals[t,2].sum(),1.,atol=1e-12)
            or not all(np.isclose(signals[t,i].sum(),0.) or np.isclose(signals[t,i].sum(),1.) for i in (1,3))
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)):
            raise ValueError("HO_INVALID_EXPERT_BOOK")
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
    print("HO_CAUSAL_NATIVE_EXECUTED_TAKER_FLOW_SOURCE_PASS")
