#!/usr/bin/env python3
"""DM independent directional convexity/dispersion seven-slot source, training only."""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(3.5,.40,.25,.20),"MIXED":(2.2,.45,.30,.35),
         "RISK_OFF":(1.4,.25,.30,.60)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DM_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net336=lc[t]-lc[t-336]-native[t-335:t+1].sum(axis=0)
        net168=lc[t]-lc[t-168]-native[t-167:t+1].sum(axis=0)
        r72=lc[t]-lc[t-72];r48=lc[t]-lc[t-48]
        prev48=lc[t-48]-lc[t-96];r24=lc[t]-lc[t-24]
        downside=np.sqrt(np.sum(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
        breadth_pos=int(np.count_nonzero(net336>0))
        breadth_neg=4-breadth_pos
        regime=("RISK_ON" if breadth_pos>=3 and r72[0]>0 else
                "RISK_OFF" if breadth_neg>=3 and r72[0]<0 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Core: cross-sectional positive net trend with short impulse, convex
        # upside from range escapes, or symmetric confirmed broad bear hedge.
        if regime=="RISK_OFF":
            score=np.where((net336<0)&(r72<0),
                           (-net336)*np.maximum(-r72,0.)/(.05+downside),0.)
            candidates=sorted((j for j in range(4) if score[j]>0),
                              key=lambda j:(-float(score[j]),j))[:2]
            if candidates:signals[t,0,candidates]=-score[candidates]/score[candidates].sum()
        else:
            score=np.zeros(4)
            for j in range(4):
                if net336[j]>0 and r72[j]>0:
                    prior_hi=float(h[t-336:t-24,j].max())
                    breakout=max(0.,float(c[t,j]/prior_hi-1.))
                    score[j]=net336[j]*(1.+3.*breakout)/(.05+downside[j])
            candidates=sorted((j for j in range(4) if score[j]>0),
                              key=lambda j:(-float(score[j]),j))[:2]
            if candidates:signals[t,0,candidates]=score[candidates]/score[candidates].sum()
        # Opportunity: short-horizon leadership acceleration and real quote flow.
        acceleration=r48-prev48
        opts=[]
        for j in range(4):
            if (acceleration[j]>.012 and net168[j]>0 and
                q[t-47:t+1,j].mean()>1.05*q[t-288:t-48,j].mean()):
                opts.append((float(acceleration[j]),j))
        if opts:
            _,j=max(opts,key=lambda x:(x[0],-x[1]))
            signals[t,1,j]=1.
        # Relative value: cross-asset 168h dispersion compression.
        high_j=int(np.argmax(net168));low_j=int(np.argmin(net168))
        dispersion=float(net168[high_j]-net168[low_j])
        compression=float(r24[high_j]-r24[low_j])
        carry=float((native[t-167:t+1,high_j]-
                     native[t-167:t+1,low_j]).sum())
        if high_j!=low_j and dispersion>.06 and compression<0 and carry>-.003:
            signals[t,2,high_j]=-.5
            signals[t,2,low_j]=.5
        # Stress / recovery: signed convex hedge, never both simultaneously.
        recent_vol=float(np.sqrt(np.mean(hourly[t-71:t+1,0]**2)))
        old_vol=float(np.sqrt(np.mean(hourly[t-575:t-72,0]**2)))
        if breadth_neg>=3 and r72[0]<-.035 and recent_vol>old_vol:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif breadth_neg>=2 and np.count_nonzero(r24>0)>=3 and r72[0]<0:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        # Reserve risk budget for core when a sleeve duplicates its inventory.
        for i in (1,2,3):
            if np.sum(np.maximum(signals[t,i]*signals[t,0],0.))>.45:
                budgets[t,i]*=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DM_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DM_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DM_BUDGET_NONFINITE")
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
    return True
if __name__=="__main__":
    assert static_check()
    print("DM_CAUSAL_DIRECTIONAL_CONVEXITY_SOURCE_STATIC_PASS")
