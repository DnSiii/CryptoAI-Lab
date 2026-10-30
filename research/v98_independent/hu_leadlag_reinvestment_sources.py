#!/usr/bin/env python3
"""HU BTC-to-altcoin lead-lag / long-only relative-pricing seven-slot SOURCE ONLY.

All source features completed at t close, executed at t+1 actual open. No PnL.
"""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.60}
PRIOR={
    "TREND":np.array([.58,.18,.14,.10]),
    "TRANSITION":np.array([.53,.18,.17,.12]),
    "STRESS":np.array([.45,.15,.15,.25]),
}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("HU_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)

    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])

    for t in range(WARMUP,n,CLOCK):
        n72,n336,n672=(net(t,w) for w in (72,336,672))
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.70,.30]

        trailing=np.diff(lc[t-672:t+1],axis=0)
        btc=trailing[:,0]
        var=max(float(np.mean((btc-btc.mean())**2)),1e-8)
        betas=np.clip(np.mean((trailing-trailing.mean(axis=0))*
                              (btc-btc.mean())[:,None],axis=0)/var,-2.,2.)
        btc24=float(lc[t,0]-lc[t-24,0])
        alt24=lc[t,1:]-lc[t-24,1:]
        underreaction=betas[1:]*btc24-alt24
        signals[t,1,1+int(np.argmax(underreaction))]=1.

        residual168=(lc[t]-lc[t-168])-betas*(lc[t,0]-lc[t-168,0])
        signals[t,2,int(np.argmin(residual168))]=1.

        stress=(float(lc[t,0]-lc[t-72,0])<-.08 or float(semi[0])>.025)
        if stress:
            signals[t,3,int(np.argmin(semi))]=1.
        else:
            signals[t,3,int(np.argmax(n72))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime

        # A prior-only joint correlation penalty, not fitted to outcomes.
        hourly_net=recent-r[t-167:t+1]*e[t-167:t+1]
        core=hourly_net@signals[t,0]
        core_sd=float(np.std(core))
        allocation=PRIOR[regime].copy()
        for i in (1,2,3):
            series=hourly_net@signals[t,i]
            sd=float(np.std(series))
            corr=0. if min(core_sd,sd)<1e-12 else float(
                np.mean((core-core.mean())*(series-series.mean()))/(core_sd*sd))
            corr=float(np.clip(corr,-1.,1.))
            revised=allocation[i]*(1.-.35*max(0.,corr))
            allocation[0]+=allocation[i]-revised
            allocation[i]=revised
        budgets[t]=allocation
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<=0) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.allclose(np.abs(signals[t]).sum(axis=1),1.,atol=1e-12) or
            np.any(signals[t]<0)):
            raise ValueError("HU_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,native_valid

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
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HU_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
            a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HU_EPOCH_BUDGET_CONSERVATION")
    if not np.allclose(a[0][epochs].sum(axis=2),1.,atol=1e-12):
        raise ValueError("HU_LONG_ONLY_SLEEVE_CONSERVATION")
    return True

if __name__=="__main__":
    if not static_check():raise SystemExit(2)
    print("HU_LEADLAG_SEVEN_SLOT_CAUSAL_SOURCE_PASS")
