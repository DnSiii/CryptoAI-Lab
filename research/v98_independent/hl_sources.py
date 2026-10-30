#!/usr/bin/env python3
"""HL orthogonal risk-budget composed engine source; 2023-2024 training only."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.65}
PRIOR={"TREND":np.array([.50,.25,.15,.10]),
       "TRANSITION":np.array([.55,.15,.15,.15]),
       "STRESS":np.array([.45,.10,.15,.30])}
CAP=.50

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HL_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    f=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def net(t,w):
        return lc[t]-lc[t-w]-(f[t+1]-f[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        n24,n96,n168,n336,n672=(net(t,w) for w in (24,96,168,336,672))
        hourly168=np.diff(lc[t-168:t+1],axis=0)
        hourly336=np.diff(lc[t-336:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(hourly168,0.)**2,axis=0)),.002)
        vol=np.maximum(np.std(hourly168,axis=0),.002)
        core=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,core]=[.60,.40]
        outside=np.array([j for j in range(4) if j not in core],dtype=int)
        rel24=n24-n24.mean()
        rel96=n96-n96.mean()
        reversal=outside[rel96[outside]<0.]
        candidates=reversal if len(reversal) else outside
        opp=int(candidates[np.argmax(rel24[candidates])])
        signals[t,1,opp]=1.
        burden=f[t+1]-f[t-335]
        signals[t,2,int(np.argmin(burden/vol))]=1.
        market=np.mean(hourly168,axis=1)
        market96=market[-96:]
        market336=np.mean(hourly336,axis=1)
        down96=np.sqrt(np.mean(np.minimum(market96,0.)**2))
        down336=np.sqrt(np.mean(np.minimum(market336,0.)**2))
        stress=(float(np.median(n168))<0. or down96>1.5*max(down336,1e-6))
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0)>=3 else "TRANSITION"
        regimes[t]=regime
        if regime=="TREND":
            chosen=int(np.argmax(n96/semi))
        else:
            down_market=np.minimum(market,0.)
            cov=np.mean((np.minimum(hourly168,0.)-np.minimum(hourly168,0.).mean(axis=0))*
                        (down_market-down_market.mean())[:,None],axis=0)
            beta=cov/max(float(np.var(down_market)),1e-6)
            chosen=int(np.argmin(beta))
        signals[t,3,chosen]=1.
        budgets[t]=PRIOR[regime]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or np.any(signals[t]<0) or np.any(budgets[t]<=0)
            or not np.allclose(signals[t].sum(axis=1),1.,atol=1e-12)
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(signals[t,1,core]) or not np.any(signals[t,1,outside])):
            raise ValueError("HL_INVALID_EXPERT_BOOK")
    return signals,updates,regimes,budgets

def capped_weights(weights,cap=CAP):
    """Euclidean capped-simplex projection, no leverage, deterministic bisection."""
    w=np.asarray(weights,dtype=float)
    if w.shape!=(4,) or not np.isfinite(w).all() or np.any(w<0) or not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("HL_INVALID_AGGREGATE")
    lo,hi=-1.,1.
    for _ in range(90):
        mid=(lo+hi)/2.
        z=np.clip(w-mid,0.,cap)
        if z.sum()>1.:lo=mid
        else:hi=mid
    z=np.clip(w-(lo+hi)/2.,0.,cap)
    if not np.isclose(z.sum(),1.,atol=1e-11) or np.any(z>cap+1e-12):
        raise ValueError("HL_CAP_PROJECT_FAIL")
    return z/z.sum()

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
    assert np.allclose(a[0][ix].sum(axis=2),1.)
    assert np.all(a[3][ix]>0)
    for w in ([1.,0.,0.,0.],[.1,.2,.3,.4],[.25,.25,.25,.25]):
        z=capped_weights(w)
        assert np.isclose(z.sum(),1.) and z.max()<=CAP+1e-12
    return True
if __name__=="__main__":
    assert static_check()
    print("HL_CAUSAL_ORTHOGONAL_RISK_BUDGET_SOURCE_PASS")
