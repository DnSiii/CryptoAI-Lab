#!/usr/bin/env python3
"""DW structural beta plus acceleration, residual overreaction and volatility convexity."""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"EXPANSION":(3.6,.20,.12,.10),
         "BALANCED":(3.1,.18,.16,.18),
         "VOL_SPIKE":(1.5,.10,.14,.35)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DW_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"BALANCED",dtype="<U10");budgets=np.zeros((n,4))
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    for t in range(WARMUP,n,GRID):
        r6=lc[t]-lc[t-6]
        r24=lc[t]-lc[t-24]
        prior24=lc[t-24]-lc[t-48]
        r168=lc[t]-lc[t-168]
        recent=hourly[t-71:t+1]
        prior=hourly[t-335:t+1]
        vol72=np.sqrt(np.mean(recent**2,axis=0))
        vol336=np.sqrt(np.mean(prior**2,axis=0))
        volratio=float(np.mean(vol72/np.maximum(vol336,1e-8)))
        regime=("VOL_SPIKE" if volratio>1.4 else
                "EXPANSION" if np.count_nonzero(r168>0)>=3 else "BALANCED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Core structural beta: precommitted, no winner selection.
        signals[t,0]=[.40,.25,.15,.20]
        # Positive acceleration with contemporaneously observed quote volume.
        candidates=[]
        for j in range(4):
            acceleration=float(r24[j]-prior24[j])
            volume=float(q[t-23:t+1,j].mean()/max(q[t-47:t-23,j].mean(),1.))
            if r24[j]>0 and acceleration>.002 and volume>1.:
                candidates.append((acceleration,j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Residual 24h overreaction: dollar-neutral contrarian pair.
        residual=r24-r24.mean()
        weak=min(range(4),key=lambda j:(float(residual[j]),j))
        strong=max(range(4),key=lambda j:(float(residual[j]),-j))
        if weak!=strong and float(residual[strong]-residual[weak])>.01:
            signals[t,2,weak]=.5
            signals[t,2,strong]=-.5
        # Shock convexity conditional on observed volatility ratio only.
        if volratio>1.2 and float(np.mean(r6))<0:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif volratio>1.2 and float(np.mean(r6))>0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DW_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DW_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DW_BUDGET_INVALID")
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
    return True
if __name__=="__main__":
    assert static_check()
    print("DW_STRUCTURAL_BETA_CONVEXITY_STATIC_PASS")
