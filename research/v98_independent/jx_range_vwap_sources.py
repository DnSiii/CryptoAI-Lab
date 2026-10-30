#!/usr/bin/env python3
"""JX preregistered native 1h auction range and VWAP dislocation seven-slot V98 Independent.
Only authenticated completed 1h Clean-4; target after t close, actual t+1 open.
TRAINING 2023-2024 ONLY; never load 2025+, other engines, Frozen or paper.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=336
GROSS={"NORMAL":.90,"STRESS":.70,"RECOVERY":.84}
PATHS=("JX_core_only","JX_full","JX_minus_opportunity","JX_minus_RV","JX_minus_stress")

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JX_INVALID_PINNED_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    intrarange=np.log(h/l)
    close_location=2.*(c-l)/np.maximum(h-l,1e-9)-1.
    typical=(h+l+c)/3.
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    experts_at=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        net672=net[t-671:t+1]
        net336=net[t-335:t+1]
        range336=np.maximum(np.sqrt(np.mean(intrarange[t-335:t+1]**2,axis=0)/
                                        (4.*np.log(2.))),.002)
        score=np.sum(net672,axis=0)/range336
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4,dtype=float)
        inverse=1./range336[leaders]
        core[leaders]=inverse/inverse.sum()
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        ratio=np.mean(q[t-71:t+1],axis=0)/np.maximum(np.mean(q[t-335:t+1],axis=0),1.)
        opp=np.mean(close_location[t-71:t+1],axis=0)*ratio
        budgets=np.zeros(3,dtype=float)
        if np.any(opp>0):
            experts[1,int(np.argmax(opp))]=1.
            budgets[0]=.15
        volume=np.sum(q[t-335:t+1],axis=0)
        if np.any(volume<=0):
            raise ValueError("JX_ZERO_336H_QUOTE_VWAP")
        vwap=np.sum(q[t-335:t+1]*typical[t-335:t+1],axis=0)/volume
        discount=np.log(vwap/c[t])
        relative_discount=discount-np.mean(discount)
        experts[2,int(np.argmax(relative_discount))]=1.
        budgets[1]=.10
        market72=float(np.sum(np.mean(net[t-71:t+1],axis=1)))
        market24=float(np.sum(np.mean(net[t-23:t+1],axis=1)))
        range72=float(np.mean(intrarange[t-71:t+1]))
        range336_market=float(np.mean(intrarange[t-335:t+1]))
        regime=("STRESS" if market72<-.03 and range72>range336_market else
                "RECOVERY" if market72<0 and market24>.012 else "NORMAL")
        if regime=="STRESS":
            chosen=int(np.argmin(range336))
        elif regime=="RECOVERY":
            chosen=int(np.argmax(np.mean(close_location[t-23:t+1],axis=0)))
        else:
            efficiency=np.sum(net[t-71:t+1],axis=0)/np.maximum(
                np.sum(np.abs(ret[t-71:t+1]),axis=0),.002)
            chosen=int(np.argmax(efficiency))
        experts[3,chosen]=1.
        budgets[2]=.13
        for path in range(5):
            if path==0:
                target=core.copy()
            else:
                b=budgets.copy()
                if path>=2:b[path-2]=0.
                target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if (not np.isfinite(target).all() or
                np.sum(np.abs(target))>1.+1e-10):
                raise ValueError("JX_GROSS_OR_FINITE")
            targets[t,path]=target
        regimes[t]=regime
        experts_at[t]=experts
        valid[t]=True
        updates[t]=True
    return targets,updates,regimes,valid,experts_at

def static_check():
    n=3000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[v.copy() for v in (c,o,h,l,q,r)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JX_FUTURE_MUTATION_"+str(i))
    if np.any(np.abs(a[0][a[1]]).sum(axis=2)>1.+1e-10):
        raise ValueError("JX_STATIC_GROSS")
    return True

if __name__=="__main__":
    assert static_check()
    print("JX_CAUSAL_NATIVE_FUNDING_DISPERSION_PASS")
