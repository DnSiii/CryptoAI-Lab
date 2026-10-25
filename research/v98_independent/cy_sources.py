#!/usr/bin/env python3
"""CY causal funding-adjusted growth, funding surprise, candle RV, wick stress
with prior-only portfolio counterfactual marginal router. Training only.
"""
from __future__ import annotations
import numpy as np
WARMUP=1008
GRID=168
BASE_BUDGETS={
 "RISK_ON":np.array([2.0,.35,.35,.20]),
 "MIXED":np.array([1.5,.40,.45,.35]),
 "RISK_OFF":np.array([.6,.25,.5,.55]),
}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("CY_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    prev=np.zeros((4,4));prevbudget=np.zeros(4)
    pending=np.zeros(4)
    shadow_marginal=np.zeros((n,4))
    for t in range(1,n):
        per_module=(prev*prevbudget[:,None])@(hourly[t]-r[t]*e[t])-pending
        pending[:]=0.
        total=float(per_module.sum())
        if total<=-.95 or np.any(total-per_module<=-.95):
            raise ValueError("CY_PROXY_INSOLVENT")
        shadow_marginal[t]=np.log1p(total)-np.log1p(total-per_module)
        if t<WARMUP or (t-WARMUP)%GRID:
            continue
        ret336=lc[t]-lc[t-336]
        f168=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
        net168=(lc[t]-lc[t-168])-f168
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if ret336[0]>0 and breadth>=3 else
                "RISK_OFF" if ret336[0]<0 and breadth<=1 else "MIXED")
        regimes[t]=regime
        score=shadow_marginal[t-503:t+1].sum(axis=0) if t>=WARMUP+504 else None
        scales=np.ones(4) if score is None else np.array([1.,*np.where(score[1:]>0,1.2,.2)])
        budgets[t]=BASE_BUDGETS[regime]*scales
        if (t-WARMUP)%336==0:
            assets=[0,1,3]
            f720=(r[t-719:t+1]*e[t-719:t+1]).sum(axis=0)
            net720=(lc[t]-lc[t-720])-f720
            volume=q[t-719:t+1,assets].sum(axis=0)
            volume_share=volume/max(float(volume.sum()),1.)
            strength=np.sqrt(np.maximum(net720[assets],0.))*np.sqrt(volume_share)
            if strength.sum()>0:
                signals[t,0,assets]=strength/strength.sum()
            updates[t,0]=True
        surprise=[]
        for j in (2,3):
            idx=np.flatnonzero(e[:t+1,j])
            recent=float(r[idx[-3:],j].sum())
            prior=float(r[idx[-6:-3],j].sum())
            surprise.append(recent-prior)
        selected=2+int(np.argmax(np.abs(surprise)))
        if surprise[selected-2]!=0.:
            signals[t,1,selected]=-float(np.sign(surprise[selected-2]))
        updates[t,1]=True
        body=(c[t-167:t+1]-o[t-167:t+1])/np.maximum(h[t-167:t+1]-l[t-167:t+1],1e-9)
        efficiency=body[:,2:4].mean(axis=0)
        if efficiency[0]!=efficiency[1]:
            j=2+int(efficiency[1]>efficiency[0]);k=3 if j==2 else 2
            signals[t,2,j]=.5;signals[t,2,k]=-.5
        updates[t,2]=True
        if ret336[0]<0:
            upper=np.maximum(0.,h[t-71:t+1,0]-np.maximum(o[t-71:t+1,0],c[t-71:t+1,0]))
            lower=np.maximum(0.,np.minimum(o[t-71:t+1,0],c[t-71:t+1,0])-l[t-71:t+1,0])
            pressure=float(np.sum((lower-upper)/o[t-71:t+1,0]))
            signals[t,3,0]=1. if pressure>0 else -1.
        elif int(np.count_nonzero(lc[t]-lc[t-72]>0))<=1:
            signals[t,3,3]=-1.
        updates[t,3]=True
        for i in np.flatnonzero(updates[t]):
            pending[i]=.0015*np.sum(np.abs(signals[t,i]*BASE_BUDGETS[regime][i]-
                                               prev[i]*prevbudget[i]))
            prev[i]=signals[t,i].copy()
            prevbudget[i]=BASE_BUDGETS[regime][i]
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CY_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CY_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all():
        raise ValueError("CY_BUDGET_NONFINITE")
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
    assert np.allclose(a[0][:,2,:].sum(axis=1),0.)
    return True
if __name__=="__main__":
    assert static_check()
    print("CY_CAUSAL_SOURCE_STATIC_PASS")
