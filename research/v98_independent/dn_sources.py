#!/usr/bin/env python3
"""DN diversified carry-aware beta plus three orthogonal sleeves. TRAINING ONLY."""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(3.,.25,.18,.18),"MIXED":(2.2,.20,.22,.25),"RISK_OFF":(1.,.10,.25,.55)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DN_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    old_core=np.full(4,.25)
    for t in range(WARMUP,n,GRID):
        net168=lc[t]-lc[t-168]-native[t-167:t+1].sum(axis=0)
        net336=lc[t]-lc[t-336]-native[t-335:t+1].sum(axis=0)
        ret24=lc[t]-lc[t-24];ret72=lc[t]-lc[t-72]
        downside=np.sqrt(np.sum(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
        carry_drag=np.maximum(native[t-335:t+1].sum(axis=0),0.)
        raw=1./(.04+downside+2.*carry_drag)
        structural=raw/raw.sum()
        old_core=.70*old_core+.30*structural
        old_core=old_core/old_core.sum()
        signals[t,0]=old_core
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if breadth>=3 and net336[0]>0 else
                "RISK_OFF" if breadth<=1 and net336[0]<0 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        prior_vol=q[t-264:t-24].mean(axis=0)
        current_vol=q[t-23:t+1].mean(axis=0)
        loc=(c[t]-l[t-23:t+1].min(axis=0))/np.maximum(
             h[t-23:t+1].max(axis=0)-l[t-23:t+1].min(axis=0),1e-12)
        eligible=[j for j in range(4) if net168[j]>0 and ret24[j]>0 and
                  loc[j]>.55 and current_vol[j]>prior_vol[j]]
        if eligible:
            j=sorted(eligible,key=lambda k:(-float(loc[k]*ret24[k]),k))[0]
            signals[t,1,j]=1.
        carry=native[t-167:t+1].sum(axis=0)
        hi=int(np.argmax(carry));lo=int(np.argmin(carry))
        if hi!=lo and carry[hi]-carry[lo]>.0005:
            signals[t,2,hi]=-.5;signals[t,2,lo]=.5
        old_vol=float(np.sqrt(np.mean(hourly[t-335:t-72,0]**2)))
        new_vol=float(np.sqrt(np.mean(hourly[t-71:t+1,0]**2)))
        if breadth<=2 and ret24[0]<0 and new_vol>old_vol:
            signals[t,3,1]=-.5;signals[t,3,3]=-.5
        elif breadth>=2 and ret24[0]>0 and ret72[0]<0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        for i in (1,3):
            if float(np.sum(np.maximum(signals[t,i]*signals[t,0],0.)))>.55:
                budgets[t,i]*=.5
        updates[t,:]=True
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DN_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DN_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DN_BUDGET_NONFINITE")
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
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.allclose(a[0][WARMUP::GRID,0,:].sum(axis=1),1.)
    return True
if __name__=="__main__":
    assert static_check()
    print("DN_STRUCTURAL_CARRY_BETA_SOURCE_STATIC_PASS")
