#!/usr/bin/env python3
"""HW preregistered cross-market spot/perp basis seven-slot causal source ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=336
GROSS={"TREND":.74,"TRANSITION":.70,"STRESS":.60}
PRIOR={"TREND":np.array([.58,.20,.12,.10]),
       "TRANSITION":np.array([.58,.15,.17,.10]),
       "STRESS":np.array([.50,.15,.20,.15])}

def bundle(opening,high,low,close,rate,event,quote,spot_close,spot_valid):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    spot=np.asarray(spot_close,dtype=float)
    valid=np.asarray(spot_valid,dtype=bool)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,spot,valid)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        not np.isfinite(spot[valid]).all() or np.any(spot[valid]<=0)):
        raise ValueError("HW_INVALID_NATIVE_OR_SPOT_SOURCE")
    n=len(c)
    lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    native_valid=np.ones((n,4),dtype=bool)
    logspot=np.log(np.where(valid,spot,1.))

    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])

    for t in range(WARMUP,n,CLOCK):
        n168,n336,n672=(net(t,w) for w in (168,336,672))
        recent=np.diff(lc[t-168:t+1],axis=0)
        semi=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.002)
        leaders=np.argsort(-n672/semi,kind="stable")[:2]
        signals[t,0,leaders]=[.60,.40]

        spot_eligible=bool(np.all(valid[t-167:t+1]))
        stress=False
        min_z=0.
        spread=0.
        if spot_eligible:
            basis_window=lc[t-167:t+1]-logspot[t-167:t+1]
            current=basis_window[-1]
            med=np.median(basis_window,axis=0)
            mad=np.median(np.abs(basis_window-med[None,:]),axis=0)
            scale=np.maximum(1.4826*mad,.0005)
            z=(current-med)/scale
            min_z=float(np.min(z))
            if min_z< -1.:
                signals[t,1,int(np.argmin(z))]=1.
            cheap=int(np.argmin(current))
            rich=int(np.argmax(current))
            spread=float(current[rich]-current[cheap])
            if spread>.002:
                signals[t,2,cheap]=.5
                signals[t,2,rich]=-.5
            stress=(float(current[0])<-.005 or
                    float(np.median(current))<-.003)
            if stress:
                signals[t,3,cheap]=1.
        if not stress:
            signals[t,3,int(np.argmax(n168))]=1.
        regime="STRESS" if stress else "TREND" if np.count_nonzero(n336>0.)>=3 else "TRANSITION"
        regimes[t]=regime

        allocation=PRIOR[regime].copy()
        if np.any(signals[t,1]):
            factor=min(1.,abs(min_z)/2.)
            delta=allocation[1]*(1.-factor)
            allocation[1]-=delta;allocation[0]+=delta
        else:
            allocation[0]+=allocation[1];allocation[1]=0.
        if np.any(signals[t,2]):
            factor=min(1.,spread/.01)
            delta=allocation[2]*(1.-factor)
            allocation[2]-=delta;allocation[0]+=delta
        else:
            allocation[0]+=allocation[2];allocation[2]=0.
        budgets[t]=allocation
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(budgets[t]<0) or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(gross[0],1.,atol=1e-12) or
            not np.isclose(gross[3],1.,atol=1e-12)):
            raise ValueError("HW_SEVEN_SLOT_SIGNED_FINANCING_INVALID")
    return signals,updates,regimes,budgets,native_valid

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    spot=c*(1.+.003*np.sin(t[:,None]/21.+np.arange(4)))
    valid=np.ones_like(c,dtype=bool)
    valid[2000:2002]=False
    spot[~valid]=np.nan
    a=bundle(o,h,l,c,r,e,q,spot,valid)
    c2,o2,h2,l2,q2,r2,s2=[x.copy() for x in (c,o,h,l,q,r,spot)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    s2[3200:]*=.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2,s2,valid)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HW_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
            a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("HW_EPOCH_BUDGET_CONSERVATION")
    for k in epochs:
        if not np.all(valid[k-167:k+1]) and np.any(a[0][k,1:3]):
            raise ValueError("HW_SPOT_MASK_LEAK")
    return True

if __name__=="__main__":
    assert static_check()
    print("HW_SPOT_PERP_BASIS_CAUSAL_SOURCE_PASS")
