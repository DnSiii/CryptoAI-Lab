#!/usr/bin/env python3
"""EW slow-core, liquidity breakout, residual reversion and correlation stress. TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS_CAP=2.80
CORE={"TREND":2.15,"MIXED":1.85,"STRESS":1.45}
TILT=(.08,.09,.10)
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EW_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    cq=np.cumsum(q,axis=0);q12=cq.copy();q12[12:]-=cq[:-12]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    def net_at(t,w):
        return lc[t]-lc[t-w]-np.sum(r[t-w+1:t+1]*e[t-w+1:t+1],axis=0)
    for t in range(WARMUP,n,CLOCK):
        n672,n336,n72,n48,n12,n4=(net_at(t,w) for w in (672,336,72,48,12,4))
        vol=np.sqrt(np.mean(hourly[t-335:t+1]**2,axis=0))
        breadth=int(np.count_nonzero(n672>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        score=np.where((n672>0)&(n336>0),n336/np.maximum(vol,1e-6),0.)
        w=score/score.sum() if score.sum()>1e-12 else np.ones(4)/4.
        w=.30*np.ones(4)/4.+.70*w
        signals[t,0]=w;budgets[t,0]=CORE[regime]
        updates[t]=True
        def transfer(j,donors):
            d=np.asarray(donors,dtype=float).copy();d[j]=0.
            if d.sum()<=1e-10:return None
            vec=-d/d.sum();vec[j]=1.
            return vec
        # Opportunity: completed-close breakout of prior 48h high, turnover shock.
        elig=(n48[1:]>0)&(c[t,1:]>np.max(h[t-48:t,1:],axis=0))&(
            q12[t,1:]>2.*np.median(q12[t-168:t,1:],axis=0))
        if elig.any():
            j=1+int(np.argmax(np.where(elig,n48[1:]/np.maximum(vol[1:],1e-6),-np.inf)))
            tilt=transfer(j,w)
            if tilt is not None:
                signals[t,1]=tilt;budgets[t,1]=TILT[0]
        # Relative value: 12h BTC-relative spread above its historical median;
        # fade laggard's positive 4h turn against leader.
        residual=n12-n12[0]
        historical=[]
        for k in range(t-167,t+1):
            past=net_at(k,12);res=past-past[0]
            historical.append(float(res.max()-res.min()))
        lo=int(np.argmin(np.where(n336>0,residual,np.inf)))
        hi=int(np.argmax(residual))
        spread=float(residual.max()-residual.min())
        if (lo!=hi and np.isfinite(residual[lo]) and n4[lo]>0 and
            spread>np.median(historical)):
            signals[t,2,lo]=1.;signals[t,2,hi]=-1.
            budgets[t,2]=TILT[1]
        # Stress: correlation-cluster defensive BTC transfer.
        corr=np.corrcoef(hourly[t-167:t+1].T)
        mean_corr=float(np.mean(corr[np.triu_indices(4,1)]))
        if (float(np.mean(n72))<0 and mean_corr>.55 and
            n12[0]>float(np.median(n12[1:]))):
            tilt=transfer(0,w)
            if tilt is not None:
                signals[t,3]=tilt;budgets[t,3]=TILT[2]
    if (np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(np.sum(abs(signals[:,1:,:]),axis=2)>2.+1e-12) or
        np.any(np.sum(abs(signals[:,0,:]),axis=1)>1.+1e-12) or
        np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals)*budgets[:,:,None],axis=(1,2))>GROSS_CAP+1e-12)):
        raise ValueError("EW_FINANCING_OR_GROSS_INVARIANT")
    return signals,updates,regimes,budgets
def static_check():
    n=3800;t=np.arange(n,dtype=float)
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
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2),0.,atol=1e-12)
    return True
if __name__=="__main__":
    assert static_check()
    print("EW_CAUSAL_SOURCE_STATIC_PASS")
