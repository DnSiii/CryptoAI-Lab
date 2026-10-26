#!/usr/bin/env python3
"""GN exact causal 4-asset log-growth quadratic allocator, independent V98 training only."""
from __future__ import annotations
import itertools
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"GROWTH":2.25,"MIXED":1.80,"STRESS":1.20,"CROWDED":1.35}
COEFF={"GROWTH":(.35,.30,.20),"MIXED":(.25,.40,.35),
       "STRESS":(.10,.40,.55),"CROWDED":(.15,.55,.25)}
LAMBDA=4.

def zscore(v):
    v=np.asarray(v,dtype=float)
    centered=v-np.mean(v)
    return centered/max(.05,float(np.max(np.abs(centered))))

def solve(mu,cov):
    """Exact finite active-set KKT simplex solution, not a strategy search grid."""
    mu=np.asarray(mu,dtype=float)
    cov=np.asarray(cov,dtype=float)
    if mu.shape!=(4,) or cov.shape!=(4,4) or not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise ValueError("GN_INVALID_OPTIMIZER_INPUT")
    best=None
    for n in range(1,5):
        for active in itertools.combinations(range(4),n):
            ix=np.array(active,dtype=int)
            h=LAMBDA*cov[np.ix_(ix,ix)]
            k=np.zeros((n+1,n+1))
            k[:n,:n]=h
            k[:n,n]=1.
            k[n,:n]=1.
            rhs=np.append(mu[ix],1.)
            try:sol=np.linalg.solve(k,rhs)
            except np.linalg.LinAlgError:continue
            w=np.zeros(4);w[ix]=sol[:n]
            if np.min(w)<-1e-9:continue
            w=np.maximum(w,0.)
            if abs(w.sum()-1.)>1e-8:continue
            lag=float(sol[n])
            grad=mu-LAMBDA*(cov@w)
            if any(grad[j]>lag+1e-7 for j in range(4) if j not in active):
                continue
            objective=float(mu@w-.5*LAMBDA*w@cov@w)
            if best is None or objective>best[0]:
                best=(objective,w)
    if best is None:raise ValueError("GN_KKT_NO_FEASIBLE_OPTIMUM")
    return best[1]

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(c<=0) or np.any(o<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GN_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    covs=np.zeros((n,4,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net336=native(t,336)
        net672=native(t,672)
        returns=np.diff(lc[t-168:t+1],axis=0)
        vol=np.maximum(np.std(returns,axis=0),.002)
        cov=np.cov(returns,rowvar=False,ddof=1)
        cov=.5*cov+.5*np.diag(np.diag(cov))+np.eye(4)*1e-6
        covs[t]=cov
        signals[t,0]=zscore(.65*net336+.35*net672)
        updates[t]=True
        burden=cumulative[t+1]-cumulative[t-167]
        breadth=int(np.count_nonzero(net336>0))
        median_vol=float(np.median(vol))
        regime=("CROWDED" if float(np.mean(burden))>.015 else
                "STRESS" if breadth<=1 or median_vol>.045 else
                "GROWTH" if breadth>=3 else "MIXED")
        regimes[t]=regime
        budgets[t,0]=GROSS[regime]
        a,b,d=COEFF[regime]

        channel=(c[t]-np.min(l[t-83:t+1],axis=0))/np.maximum(
            np.max(h[t-83:t+1],axis=0)-np.min(l[t-83:t+1],axis=0),1e-9)-.5
        vnow=np.mean(q[t-83:t+1],axis=0)
        vprev=np.mean(q[t-167:t-83],axis=0)
        participation=np.clip(np.log((vnow+1.)/(vprev+1.)),-1.,1.)
        signals[t,1]=zscore(channel*participation)
        budgets[t,1]=a

        signals[t,2]=zscore(-burden/vol)
        budgets[t,2]=b

        path=c[t-168:t+1]
        worst=np.min(path/np.maximum.accumulate(path,axis=0)-1.,axis=0)
        rebound=c[t]/np.min(c[t-48:t+1],axis=0)-1.
        signals[t,3]=zscore(rebound+.5*worst)
        budgets[t,3]=d

        for omitted in (None,1,2,3):
            mu=.001*signals[t,0].copy()
            for i in (1,2,3):
                if i!=omitted:mu+=.001*signals[t,i]*budgets[t,i]
            weights=solve(mu,cov)
            if np.any(weights<-1e-10) or abs(weights.sum()-1.)>1e-10:
                raise ValueError("GN_INVALID_OPTIMAL_BOOK")
    return signals,updates,regimes,budgets,covs

def static_check():
    n=2000
    t=np.arange(n,dtype=float)
    c=np.stack([100*np.exp(.00012*t+.012*np.sin(t/(19+i*5)+i)) for i in range(4)],axis=1)
    o=np.vstack((c[0],c[:-1]))
    h=np.maximum(o,c)*1.001;l=np.minimum(o,c)*.999
    r=np.tile(np.array([.0001,-.00005,.00003,-.00008]),(n,1))
    e=np.zeros_like(r);e[::8]=1.
    q=np.stack([1e7*(1+.2*np.sin(t/(21+i*3))) for i in range(4)],axis=1)
    a=bundle(o,h,l,c,r,e,q)
    assert np.all(a[1][WARMUP::CLOCK,0])
    assert np.allclose(solve(np.array([.001,0.,-.001,.0005]),np.eye(4)*.0001).sum(),1.)
    cutoff=1080
    c2=c.copy();c2[cutoff+1:]*=1.08
    o2=o.copy();o2[cutoff+2:]=c2[cutoff+1:-1]
    b=bundle(o2,np.maximum(o2,c2)*1.001,np.minimum(o2,c2)*.999,c2,r,e,q)
    for i in (0,1,3,4):
        assert np.array_equal(a[i][:cutoff+1],b[i][:cutoff+1])
    return True

if __name__=="__main__":
    assert static_check()
    print("GN_EXACT_KKT_CONVEX_AND_CAUSAL_STATIC_PASS")
