#!/usr/bin/env python3
"""EU causal synchronized financed portfolio tilts, full seven-slot, TRAINING ONLY."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS_CAP=2.80
CORE={"TREND":1.95,"MIXED":1.75,"STRESS":1.45}
TILT=(.12,.10,.12)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EU_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    cq=np.cumsum(q,axis=0)
    q24=cq.copy();q24[24:]-=cq[:-24]
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        def net(window):
            debit=np.sum(r[t-window+1:t+1]*e[t-window+1:t+1],axis=0)
            return lc[t]-lc[t-window]-debit
        n336,n168,n72,n48,n24=(net(w) for w in (336,168,72,48,24))
        vol=np.sqrt(np.mean(hourly[t-167:t+1]**2,axis=0))
        breadth=int(np.count_nonzero(n336>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        score=np.where((n336>0)&(n168>0),np.maximum(n168,0)/np.maximum(vol,1e-7),0.)
        w=score/score.sum() if score.sum()>1e-12 else np.array([1.,0.,0.,0.])
        w=.25*np.array([1.,0.,0.,0.])+.75*w
        signals[t,0]=w;budgets[t,0]=CORE[regime]
        updates[t]=True
        # A tilt vector sums to zero: every long is financed by reductions in core holdings.
        def transfer(j,donors):
            d=np.asarray(donors,dtype=float).copy()
            d[j]=0.
            if d.sum()<=1e-10:return None
            d=d/d.sum()
            v=-d;v[j]=1.
            return v
        # Opportunity: volume-confirmed short-horizon relative impulse.
        eligible=(n168[1:]>0)&(n48[1:]>0)&(n24[1:]>0)&(
            q24[t,1:]>np.median(q24[t-168:t,1:],axis=0))
        if eligible.any():
            quality=np.where(eligible,n48[1:]/np.maximum(vol[1:],1e-7),-np.inf)
            j=1+int(np.argmax(quality))
            tilt=transfer(j,w)
            if tilt is not None:
                signals[t,1]=tilt;budgets[t,1]=TILT[0]
        # Relative value: finance the cheapest carry with the most expensive core-held carry.
        debit=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        candidates=(n336>0)&(n72>0)
        if candidates.any():
            j=int(np.argmin(np.where(candidates,debit,np.inf)))
            donors=(np.arange(4)!=j)&(w>1e-8)&(n168>0)
            if donors.any():
                k=int(np.argmax(np.where(donors,debit,-np.inf)))
                vec=np.zeros(4);vec[j]=1.;vec[k]=-1.
                signals[t,2]=vec;budgets[t,2]=TILT[1]
        # Stress: self-financed BTC rotation only on an observable relative recovery.
        if (float(np.mean(n48))<0 and n24[0]>0 and
            np.count_nonzero(n48[1:]<0)>=2):
            donors=w.copy();donors[0]=0.
            tilt=transfer(0,donors)
            if tilt is not None:
                signals[t,3]=tilt;budgets[t,3]=TILT[2]
    if (np.any(np.abs(np.sum(signals[:,1:,:],axis=2))>1e-12) or
        np.any(np.sum(abs(signals[:,1:,:]),axis=2)>2.+1e-12) or
        np.any(np.sum(abs(signals[:,0,:]),axis=1)>1.+1e-12) or
        np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals)*budgets[:,:,None],axis=(1,2))>GROSS_CAP+1e-12)):
        raise ValueError("EU_FINANCING_OR_GROSS_INVARIANT")
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
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2),0.,atol=1e-12)
    return True
if __name__=="__main__":
    assert static_check()
    print("EU_FINANCED_TILTS_CAUSAL_STATIC_PASS")
