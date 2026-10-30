#!/usr/bin/env python3
"""JP precommitted seven-slot delayed-shadow growth competition, 2023-24 training only."""
from __future__ import annotations
import numpy as np
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JP_core_only","JP_full","JP_minus_opportunity","JP_minus_RV","JP_minus_stress")
INERTIA=.50

def _unit(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JP_NONFINITE_TARGET")
    g=float(np.abs(v).sum())
    return v/g if g>1e-12 else np.zeros(4,dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(v,dtype=float) for v in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(v.shape!=c.shape for v in (o,h,l,r,e,q))
        or any(not np.isfinite(v).all() for v in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JP_INVALID_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    clv=np.clip((2*c-h-l)/np.maximum(h-l,1e-12),-1.,1.)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.zeros((5,4),dtype=float)
    prev_experts=None
    shadow=[[] for _ in range(3)]
    first=True
    for t in range(WARMUP,n,CLOCK):
        # Strictly delayed: realized 168h returns since the PREVIOUS epoch
        # are credited only to PREVIOUS frozen expert vectors, not new signals.
        if prev_experts is not None:
            interval=net[t-CLOCK+1:t+1]
            for k in range(3):
                a=prev_experts[k+1]-prev_experts[0]
                realized=float(np.sum(interval@a))-.0009*float(np.abs(a).sum())
                shadow[k].append(realized)
                if len(shadow[k])>2:shadow[k].pop(0)
        x336=net[t-335:t+1]
        x168=net[t-167:t+1]
        x72=net[t-71:t+1]
        x24=net[t-23:t+1]
        down=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.001)
        raw=np.maximum(np.sum(x336,axis=0),0.)/down
        if raw.sum()<1e-12:raw=1./down
        core=_unit(raw)
        experts=np.zeros((4,4),dtype=float)
        experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        market72=float(np.mean(x72,axis=1).sum())
        market24=float(np.mean(x24,axis=1).sum())
        p168=np.mean(c[t-167:t+1]/c[t-167],axis=1)
        dd=1.-float(p168[-1])/max(float(p168.max()),1e-12)
        regime=("STRESS" if market72<-.03 or dd>.10 else
                "RECOVERY" if market24>.01 and dd>.05 else "NORMAL")
        regimes[t]=regime
        if good:
            volume=np.mean(q[t-71:t+1],axis=0)/np.maximum(
                np.mean(q[t-239:t-71],axis=0),1e-12)
            drift72=np.sum(x72,axis=0)
            opportunity=np.maximum(drift72,0.)*volume
            if np.any(opportunity>0):experts[1,int(np.argmax(opportunity))]=1.
            # Cross-sectional time-scale catch-up, never the 168h winner score.
            drift168=np.sum(x168,axis=0)
            acceleration=7.*np.sum(x24,axis=0)-drift168
            relative=(acceleration-acceleration.mean())/down
            experts[2,int(np.argmax(relative))]=1.
            if regime=="STRESS":
                experts[3,int(np.argmin(drift72))]=-1.
            elif regime=="RECOVERY":
                experts[3,int(np.argmax(np.sum(x24,axis=0)))]=1.
            else:
                clv24=np.mean(clv[t-23:t+1],axis=0)
                drift24=np.sum(x24,axis=0)
                defensive=np.maximum(clv24,0.)*np.maximum(drift24,0.)/down
                idx=int(np.argmax(defensive)) if np.any(defensive>0) else int(np.argmin(down))
                experts[3,idx]=1.
        forecasts[t]=experts
        for i in range(5):
            if i==0 or not good:
                proposed=core.copy()
            else:
                budgets=np.zeros(3,dtype=float)
                for k in range(3):
                    if np.abs(experts[k+1]).sum()>1e-12:
                        score=sum(shadow[k])
                        budgets[k]=.06+.10*min(1.,max(0.,score)/.04)
                if i>=2:budgets[i-2]=0.
                if budgets.sum()>.48+1e-10:raise ValueError("JP_BUDGET")
                proposed=_unit((1.-budgets.sum())*core+budgets@experts[1:])
                if not first:proposed=_unit(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        prev_experts=experts.copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.+1e-10)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JP_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=3000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[v.copy() for v in (c,o,h,l,q,r)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JP_FUTURE_MUTATION_"+str(i))
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JP_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JP_DELAYED_SHADOW_CAUSAL_SOURCE_PASS")
