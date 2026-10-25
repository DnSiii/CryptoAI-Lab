#!/usr/bin/env python3
"""DD asymmetric long-only relative opportunity seven-slot source. Historical training only."""
from __future__ import annotations
import numpy as np
WARMUP=1080
GRID=120
BUDGETS={
    "RISK_ON":np.array([2.4,.30,.35,0.],dtype=float),
    "MIXED":np.array([1.7,.40,.40,.40],dtype=float),
    "RISK_OFF":np.array([.40,.20,.25,.85],dtype=float),
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
        raise ValueError("DD_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net600=lc[t]-lc[t-600]-native[t-599:t+1].sum(axis=0)
        net240=lc[t]-lc[t-240]-native[t-239:t+1].sum(axis=0)
        ret120=lc[t]-lc[t-120]
        ret72=lc[t]-lc[t-72]
        ret60=lc[t]-lc[t-60]
        breadth=int(np.count_nonzero(net240>0))
        regime=("RISK_ON" if breadth>=3 and ret120[0]>0 else
                "RISK_OFF" if breadth<=1 and ret120[0]<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        # Core: positive net 600h trend scaled by realized downside risk.
        down=np.sqrt(np.mean(np.minimum(hourly[t-599:t+1],0.)**2,axis=0))
        score=np.where((net600>0)&(ret120>0),
                       np.maximum(net600,0.)/np.maximum(down,.0005),0.)
        top=sorted(range(4),key=lambda j:(-float(score[j]),j))[:2]
        top=[j for j in top if score[j]>0]
        if top:
            weight=score[top]/float(score[top].sum())
            signals[t,0,top]=weight
        updates[t,0]=True
        used=set(top)
        # Secondary opportunity: price range escape confirmed by quote turnover.
        options=[]
        for j in range(4):
            if j in used:continue
            past_high=float(np.max(h[t-264:t-24,j]))
            old_quote=float(q[t-240:t-24,j].mean())
            recent_quote=float(q[t-23:t+1,j].mean())
            if c[t,j]>past_high and recent_quote>old_quote:
                options.append(((float(c[t,j])/past_high)-1.,j))
        if options and budgets[t,1]>0:
            _,j=max(options,key=lambda x:(x[0],-x[1]))
            signals[t,1,j]=1.
            used.add(j)
        updates[t,1]=True
        # Relative value is a long-only selection against an equal-weight basket.
        # Avoid the forced short-leg price drag of a market-neutral carry spread.
        relative=net240-float(net240.mean())
        eligible=[j for j in range(4) if j not in used and
                  net240[j]>0 and ret60[j]>0 and relative[j]>.02]
        if eligible and budgets[t,2]>0:
            j=max(eligible,key=lambda k:(float(relative[k]),-k))
            signals[t,2,j]=1.
        updates[t,2]=True
        # Crisis hedge or breadth recovery; risk budget may be zero in RISK_ON.
        if ret120[0]<0 and (lc[t,0]-lc[t-240,0])<0 and int(np.count_nonzero(ret72<0))>=3:
            signals[t,3,int(np.argmin(ret72))]=-1.
        elif (lc[t,0]-lc[t-240,0])<0 and int(np.count_nonzero(ret72>0))>=3:
            signals[t,3,int(np.argmax(ret72))]=1.
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DD_GROSS_SOURCE")
    if np.any(signals[:,2,:]<0) or np.any(signals[:,0,:]<0):
        raise ValueError("DD_LONG_ONLY_CORE_RV")
    if not np.isfinite(budgets).all():
        raise ValueError("DD_BUDGET_NONFINITE")
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
    assert np.all(a[0][:,2,:]>=0.)
    return True
if __name__=="__main__":
    assert static_check()
    print("DD_CAUSAL_SOURCE_STATIC_PASS")
