#!/usr/bin/env python3
"""HT preregistered covariance-residual / liquidity-breakout seven-slot SOURCE ONLY.

Training 2023-24, warmup Dec 2022; completed close t -> execution t+1.
No PnL, 2025, external engines or parameter selection.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"TREND":.72,"TRANSITION":.67,"STRESS":.60}
PRIOR={
    "TREND":np.array([.60,.16,.14,.10]),
    "TRANSITION":np.array([.55,.15,.15,.15]),
    "STRESS":np.array([.45,.12,.18,.25]),
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
        raise ValueError("HT_INVALID_NATIVE_SOURCE")
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
        n24,n72,n336,n504=(net(t,w) for w in (24,72,336,504))
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n504/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.70,.30]

        prior_high=np.max(h[t-168:t],axis=0)
        v24=np.mean(q[t-23:t+1],axis=0)
        v168=np.mean(q[t-167:t+1],axis=0)
        volume_ratio=v24/np.maximum(v168,1e-12)
        breakout=np.maximum(0.,np.log(c[t]/prior_high))*np.minimum(3.,volume_ratio)
        if float(np.max(breakout))>0.:
            signals[t,1,int(np.argmax(breakout))]=1.

        trailing=np.diff(lc[t-672:t+1],axis=0)
        btc=trailing[:,0]
        var=max(float(np.mean((btc-btc.mean())**2)),1e-8)
        betas=np.clip(np.mean((trailing-trailing.mean(axis=0))*
                              (btc-btc.mean())[:,None],axis=0)/var,-2.,2.)
        residual=(lc[t]-lc[t-72])-betas*(lc[t,0]-lc[t-72,0])
        ranks=np.argsort(residual,kind="stable")
        long_rv=int(ranks[0]);short_rv=int(ranks[-1])
        if long_rv==short_rv:raise ValueError("HT_RV_NOT_DISTINCT")
        signals[t,2,long_rv]=.60
        signals[t,2,short_rv]=-.40

        btc_semi=float(semi[0])
        stress=(float(lc[t,0]-lc[t-72,0])<-.08 or btc_semi>.025)
        if stress:
            short_asset=1+int(np.argmax(betas[1:]))
            signals[t,3,0]=.30
            signals[t,3,short_asset]=-.70
        else:
            negative72=np.flatnonzero(n72<0.)
            if len(negative72):
                candidate=negative72[np.argmax(n24[negative72])]
                signals[t,3,int(candidate)]=1.
            else:
                signals[t,3,0]=1.

        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime

        # Prior-only covariance-aware net-log heuristic; no future or fitted labels.
        hourly_net=recent-r[t-167:t+1]*e[t-167:t+1]
        optional=[]
        for i in (1,2,3):
            if not np.any(signals[t,i]):
                optional.append(0.)
                continue
            x=hourly_net@signals[t,i]
            score=max(0.,float(np.mean(x)-.5*np.var(x)-.0001/CLOCK))
            optional.append(float(PRIOR[regime][i]*(.5+min(1.,score/.0001))))
        budgets[t,1:]=optional
        budgets[t,0]=1.-sum(optional)
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<0) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.allclose(np.abs(signals[t,[0,2,3]]).sum(axis=1),1.,atol=1e-12) or
            not np.isclose(np.abs(signals[t,1]).sum(),
                           float(np.any(signals[t,1])),atol=1e-12)):
            raise ValueError("HT_SEVEN_SLOT_CONSERVATION")
    return signals,updates,regimes,budgets,native_valid

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HT_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HT_EPOCH_BUDGET_CONSERVATION")
    if not np.all((a[0][epochs,2]<0).any(axis=1)):
        raise ValueError("HT_SIGNED_RV_MISSING")
    return True

if __name__=="__main__":
    if not static_check():raise SystemExit(2)
    print("HT_COVARIANCE_BREAKOUT_SEVEN_SLOT_CAUSAL_SOURCE_PASS")
