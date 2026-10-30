#!/usr/bin/env python3
"""JK preregistered online marginal-edge router, Clean-4 2023-24 TRAINING ONLY."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.,"STRESS":.80,"RECOVERY":.95}
PATHS=("JK_core_only","JK_full","JK_minus_opportunity","JK_minus_RV","JK_minus_stress")
PRIOR=np.array([.50,.20,.15,.15],dtype=float)
INERTIA=.50
SHADOW_FRICTION=.0015

def _gross(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JK_NONFINITE_TARGET")
    s=float(np.abs(v).sum())
    return v/s if s>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JK_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    previous=np.zeros((5,4),dtype=float)
    prev_experts=None
    history=[[],[],[]]
    first=True
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x336=net[t-335:t+1]
        x168=net[t-167:t+1]
        x72=net[t-71:t+1]
        n672=x672.sum(axis=0)
        n168=x168.sum(axis=0)
        n72=x72.sum(axis=0)
        n24=net[t-23:t+1].sum(axis=0)
        market336=x336.mean(axis=1)
        market72=float(np.sum(x72.mean(axis=1)))
        # Strictly lagged shadow expert-minus-core excess; completed weeks only.
        if prev_experts is not None:
            realized=x168.sum(axis=0)
            for j in range(1,4):
                diff=prev_experts[j]-prev_experts[0]
                excess=float(diff@realized-SHADOW_FRICTION*np.abs(diff).sum())
                history[j-1].append(excess)
        std672=np.maximum(np.std(x672,axis=0),.002)
        raw=np.maximum(n672,0.)*np.maximum(n168,0.)/std672
        if raw.sum()<1e-12:raw=1./std672
        core=raw/raw.sum()
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(np.all(q[t-335:t+1]>0))
        valid[t]=good
        index=np.mean(c[t-335:t+1]/c[t-335],axis=1)
        drawdown=1.-float(index[-1])/max(float(np.max(index)),1e-12)
        stress=bool(market72<-.06 and np.count_nonzero(n72<0)>=3)
        regime="STRESS" if stress else ("RECOVERY" if market72>.03 and drawdown>.10 else "NORMAL")
        beta=np.mean((x336-x336.mean(axis=0))*(market336-market336.mean())[:,None],axis=0)/max(float(np.var(market336)),1e-10)
        confidence=np.zeros(4,dtype=float);confidence[0]=1.
        if good:
            flow=np.sum(np.sign(x72)*q[t-71:t+1],axis=0)/np.maximum(np.sum(q[t-71:t+1],axis=0),1e-9)
            opportunity=np.maximum(flow,0.)*np.maximum(n72,0.)
            if np.any(opportunity>0):
                experts[1,int(np.argmax(opportunity))]=1.
            residual=np.sum(x168-beta[None,:]*x168.mean(axis=1)[:,None],axis=0)
            rank=np.argsort(residual,kind="stable")
            experts[2,int(rank[-1])]=.5
            experts[2,int(rank[0])]=-.5
            if regime=="STRESS":
                rank=np.argsort(beta,kind="stable")
                experts[3,int(rank[0])]=.5
                experts[3,int(rank[-1])]=-.5
            elif regime=="RECOVERY":
                lows=np.min(c[t-335:t+1],axis=0)
                oversold=1.-c[t]/np.maximum(np.max(c[t-335:t+1],axis=0),1e-9)
                eligible=np.where(n24>0,oversold,-np.inf)
                idx=int(np.argmax(eligible)) if np.any(np.isfinite(eligible)) else int(np.argmax(n24))
                experts[3,idx]=1.
            else:
                z=x168-x168.mean(axis=0)
                skew=np.mean(z**3,axis=0)/np.maximum(np.std(x168,axis=0)**3,1e-12)
                rank=np.argsort(skew,kind="stable")
                experts[3,int(rank[-1])]=.5
                experts[3,int(rank[0])]=-.5
            for j in range(1,4):
                hst=history[j-1]
                if len(hst)<4:confidence[j]=.25
                elif sum(hst[-4:])>0 and sum(v>0 for v in hst[-4:])>=2:
                    confidence[j]=1.
                else:confidence[j]=0.
            if not np.any(opportunity>0):confidence[1]=0.
        regimes[t]=regime;forecasts[t]=experts
        weights=PRIOR*confidence
        weights[0]=1.-float(weights[1:].sum())
        if weights[0]<.50-1e-12:raise ValueError("JK_CORE_FLOOR")
        for i in range(5):
            w=weights.copy()
            if i==0:w[1:]=0.
            elif i>=2:w[i-1]=0.
            w[0]=1.-float(w[1:].sum())
            proposed=_gross(w@experts)
            if not good:proposed=_gross(core)
            elif not first:proposed=_gross(INERTIA*previous[i]+(1.-INERTIA)*proposed)
            targets[t,i]=proposed
        previous=targets[t].copy()
        prev_experts=experts.copy()
        first=False
        updates[t]=True
        if (not np.isfinite(targets[t]).all()
            or np.any(np.abs(targets[t]).sum(axis=1)>1.0000000001)
            or (not good and not np.allclose(targets[t],targets[t,0]))):
            raise ValueError("JK_GROSS_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JK_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.0000000001):
        raise ValueError("JK_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    b=bundle(o,h,l,c,r,e,qgap)
    if b[3][WARMUP] or not np.allclose(b[0][WARMUP],b[0][WARMUP,0]):
        raise ValueError("JK_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JK_CAUSAL_ONLINE_SHADOW_ROUTER_QUARANTINE_PASS")
