#!/usr/bin/env python3
"""IB causal prequential marginal utility seven-slot source; no executable shadow PnL."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":.70,"TRANSITION":.65,"STRESS":.55}
PRIOR={"TREND":np.array([.58,.16,.12,.14]),
       "TRANSITION":np.array([.66,.12,.10,.12]),
       "STRESS":np.array([.72,.08,.08,.12])}

def capped_simplex(raw):
    x=np.asarray(raw,dtype=float)
    if x.shape!=(4,) or not np.isfinite(x).all() or np.any(x<=0):
        raise ValueError("IB_ALLOCATOR_INVALID")
    x=x/x.sum()
    lo=float(x.min()-1.);hi=float(x.max()+1.)
    for _ in range(80):
        mid=(lo+hi)*.5
        if np.clip(x-mid,.05,.80).sum()>1.:lo=mid
        else:hi=mid
    w=np.clip(x-(lo+hi)*.5,.05,.80)
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("IB_BUDGET_PROJECTION")
    return w

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IB_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    shadow=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    past_marginals=[]
    for t in range(WARMUP,n,CLOCK):
        previous=t-CLOCK
        if previous>=WARMUP:
            # Prior close decision previous -> actual next open previous+1.
            # This is a conservative causal *eligibility* score only.
            log_change=np.log(c[t]/o[previous+1])
            signed_funding=funding[t+1]-funding[previous+1]
            frozen=shadow[previous]
            approx_utility=frozen@(log_change-signed_funding)-.0016*np.abs(frozen).sum(axis=1)
            past_marginals.append(approx_utility[1:]-approx_utility[0])
        n72=net(t,72);n168=net(t,168)
        returns=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(returns,0.)**2,axis=0)),.002)
        shadow[t,0]=(1./semi)/(1./semi).sum()
        price_efficiency=np.abs(lc[t]-lc[t-168])/np.maximum(np.abs(returns).sum(axis=0),1e-12)
        efficiency=np.sign(n168)*price_efficiency
        best=int(np.argmax(efficiency)) if np.any(efficiency>0) else int(np.argmax(n168))
        shadow[t,1,best]=1.
        btc=returns[:,0];den=float(btc@btc)+1e-12
        beta=np.clip((returns.T@btc)/den,0.,3.)
        residual=(lc[t]-lc[t-72])-beta*(lc[t,0]-lc[t-72,0])
        residual[0]=0.
        rank=np.argsort(-residual,kind="stable")
        shadow[t,2,int(rank[0])]=.5
        shadow[t,2,int(rank[-1])]=-.5
        stress=bool(n72[0]<-.05 or np.median(n72)<-.035)
        shadow[t,3,0]=-1. if stress else 1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n168>0)>=3 else "TRANSITION"
        regimes[t]=regime
        budget=capped_simplex(PRIOR[regime])
        eligible=np.ones(4,dtype=bool)
        if len(past_marginals)>=4:
            marginal=np.mean(np.array(past_marginals[-4:]),axis=0)
            eligible[1:]=marginal>.001
        signals[t]=shadow[t]
        signals[t,~eligible]=0.
        budgets[t]=budget
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or not np.isfinite(budgets[t]).all()
            or not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(budgets[t]<.05-1e-12) or np.any(budgets[t]>.80+1e-12)
            or not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12))
            or not np.isclose(signals[t,2].sum(),0.,atol=1e-12)):
            raise ValueError("IB_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

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
            raise ValueError("IB_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IB_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IB_OPTIONAL_SLEEVE_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IB_CORE_GROSS_CONSERVATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("IB_PREQUENTIAL_CAUSAL_SOURCE_PASS")
