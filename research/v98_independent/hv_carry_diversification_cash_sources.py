#!/usr/bin/env python3
"""HV causal carry-aligned trend, decorrelated positive drift and financed stress cash.
Source only: completed t close, real t+1 open; no PnL, no holdout.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.60}
PRIOR={
    "TREND":np.array([.56,.20,.14,.10]),
    "TRANSITION":np.array([.58,.16,.16,.10]),
    "STRESS":np.array([.50,.12,.12,.26]),
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
        raise ValueError("HV_INVALID_NATIVE_SOURCE")
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
        n72,n168,n336,n672=(net(t,w) for w in (72,168,336,672))
        recent=np.diff(lc[t-168:t+1],axis=0)
        hourly_net=recent-r[t-167:t+1]*e[t-167:t+1]
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)

        # Core: long-only two-asset 60/40 trend/downside efficiency.
        leaders=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.60,.40]

        # Opportunity: joint positive trend and cheap native signed carry.
        burden=funding[t+1]-funding[t-167]
        eligible=(n336>0.)&(burden<np.median(burden))
        if np.any(eligible):
            score=np.where(eligible,n168/semi,-np.inf)
            signals[t,1,int(np.argmax(score))]=1.

        # RV: independently funded, positive-drift, least correlated asset.
        trailing=np.diff(lc[t-336:t+1],axis=0)-r[t-335:t+1]*e[t-335:t+1]
        core_series=trailing@signals[t,0]
        core_sd=float(np.std(core_series))
        eligible=n336>0.
        if np.any(eligible):
            corr=np.ones(4)
            for j in range(4):
                sd=float(np.std(trailing[:,j]))
                if min(sd,core_sd)>1e-12:
                    corr[j]=float(np.clip(np.mean(
                        (trailing[:,j]-trailing[:,j].mean())*
                        (core_series-core_series.mean()))/(sd*core_sd),-1.,1.))
            signals[t,2,int(np.argmin(np.where(eligible,corr,np.inf)))]=1.

        # Stress/Recovery: reserve actual cash in market stress.
        stress=(float(np.median(n168))<-.04 or float(n72[0])<-.06)
        if not stress:
            signals[t,3,int(np.argmax(n168))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime

        # Preregistered causal marginal log-utility gate; no future outcomes.
        allocation=PRIOR[regime].copy()
        core=hourly_net@signals[t,0]
        core_mean=float(np.mean(core))
        core_var=float(np.var(core))
        for i in (1,2,3):
            if not np.any(signals[t,i]):
                if i==3 and stress:
                    continue  # Explicitly funded USD cash reserve.
                allocation[0]+=allocation[i]
                allocation[i]=0.
                continue
            series=hourly_net@signals[t,i]
            utility=float(np.mean(series)-core_mean-
                          .5*(np.var(series)-core_var))
            if utility<=0.:
                allocation[0]+=allocation[i]
                allocation[i]=0.
                signals[t,i]=0.
        budgets[t]=allocation
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<0) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all((np.isclose(signals[t].sum(axis=1),1.,atol=1e-12))|
                       (np.isclose(signals[t].sum(axis=1),0.,atol=1e-12))) or
            np.any(signals[t]<0) or
            np.any((budgets[t,1:]==0.)&(signals[t,1:].sum(axis=1)>0.))):
            raise ValueError("HV_SEVEN_SLOT_FINANCING_INVALID")
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
            raise ValueError("HV_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
            a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HV_EPOCH_BUDGET_CONSERVATION")
    if not np.allclose(a[0][epochs,0,:].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HV_CORE_CONSERVATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("HV_SEVEN_SLOT_CAUSAL_SOURCE_PASS")
