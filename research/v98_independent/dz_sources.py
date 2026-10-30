#!/usr/bin/env python3
"""DZ: causal incremental-log-wealth allocator for complete seven-slot portfolio.
Shadow histories are prior-only, not fitted from 2025 or actual future PnL.
"""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={
    "EXPANSION":(3.00,.40,.30,.30),
    "TRANSITION":(2.60,.32,.30,.32),
    "SHOCK":(1.10,.18,.26,.42),
}
SHADOW_HURDLE=.010
SHADOW_SEVERE_ROUNDTRIP=.010

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DZ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U10");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r72=lc[t]-lc[t-72]
        f168=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        f72=np.sum(r[t-71:t+1]*e[t-71:t+1],axis=0)
        net168=r168-f168
        net72=r72-f72
        breadth=int(np.count_nonzero(net168>0))
        market72=float(np.mean(r72))
        recent=np.std(hourly[t-71:t+1],axis=0)
        prior=np.std(hourly[t-335:t+1],axis=0)
        volratio=float(np.mean(recent/np.maximum(prior,1e-8)))
        regime=("SHOCK" if volratio>1.2 and market72<0 else
                "EXPANSION" if breadth>=3 and market72>0 else "TRANSITION")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        # Growth core: half strategic four-asset equal-weight beta, half
        # diversified *causal* positive net-carry trend allocation.
        positive=np.maximum(net168,0.)
        trend=positive/positive.sum() if positive.sum()>1e-12 else np.full(4,.25)
        signals[t,0]=.5*np.full(4,.25)+.5*trend
        # Opportunity: positive net-of-funding 72h alt impulse with volume.
        candidates=[]
        for j in (1,2,3):
            vr=float(np.mean(q[t-71:t+1,j]))/max(
                float(np.mean(q[t-143:t-71,j])),1.)
            if net72[j]>.01 and net168[j]>0 and vr>.80:
                candidates.append((float(net72[j]),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Relative value: 72h alt-vs-BTC idiosyncratic trend, not 168h
        # top-vs-bottom or funding spread. Neutral to the market anchor.
        residual=r72[1:]-r72[0]
        j=1+int(np.argmax(np.abs(residual)))
        if residual[j-1]>.025 and net168[j]>0:
            signals[t,2,j]=.5;signals[t,2,0]=-.5
        elif residual[j-1]<-.025 and net168[0]>0:
            signals[t,2,0]=.5;signals[t,2,j]=-.5
        # Stress/recovery: vol-regime asymmetric insurance/re-entry,
        # independent of BTC-SOL quality rotation and 72h drawdown triggers.
        if volratio>1.2 and market72<0:
            signals[t,3,1]=-.5;signals[t,3,3]=-.5
        elif volratio<.85 and market72>0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        # Incremental shadow capital allocator: score the *signal known at
        # previous close* over its subsequently completed 168h interval,
        # including native funding, minus simultaneous growth-core opportunity
        # cost and severe fixed round-trip friction. No future observations.
        for i in (1,2,3):
            edges=[]
            for k in range(1,5):
                p=t-k*GRID
                if p<WARMUP or not np.any(signals[p,i]):
                    continue
                realized=(lc[p+GRID]-lc[p]-
                          np.sum(r[p+1:p+GRID+1]*e[p+1:p+GRID+1],axis=0))
                edge=float((signals[p,i]-signals[p,0])@realized
                           -SHADOW_SEVERE_ROUNDTRIP)
                edges.append(edge)
            if (len(edges)>=2 and sum(x>0 for x in edges)>=2 and
                sum(edges)>SHADOW_HURDLE):
                scale=min(1.,.5+sum(edges)/.10)
                budgets[t,i]*=scale
            else:
                budgets[t,i]=0.
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DZ_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DZ_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DZ_BUDGET_INVALID")
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
    return True
if __name__=="__main__":
    assert static_check()
    print("DZ_INCREMENTAL_LOG_WEALTH_STATIC_PASS")
