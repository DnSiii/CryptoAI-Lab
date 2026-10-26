#!/usr/bin/env python3
"""FA preregistered downside-adjusted breadth growth, breakout, relative acceleration and dispersion hedge. TRAINING ONLY."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=96
GROSS_CAP=2.80
CORE={"TREND":2.20,"MIXED":1.70,"STRESS":1.15}
OPPORTUNITY=.12
RV=.10
STRESS=.10

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("FA_INVALID_PINNED_SOURCE")
    n=len(c)
    lc=np.log(c)
    paid=r*e
    cumulative=np.vstack((np.zeros((1,4)),np.cumsum(paid,axis=0)))
    qcum=np.vstack((np.zeros((1,4)),np.cumsum(q,axis=0)))
    q24=np.vstack((np.zeros((23,4)),qcum[24:]-qcum[:-24]))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)

    def native(t,w):
        return lc[t]-lc[t-w]-(cumulative[t+1]-cumulative[t-w+1])

    for t in range(WARMUP,n,CLOCK):
        net720,net168,net72=(native(t,w) for w in (720,168,72))
        breadth=int(np.count_nonzero(net720>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        downside=np.sqrt(np.mean(np.minimum(np.diff(lc[t-720:t+1],axis=0),0.)**2,axis=0))
        score=net720-.5*downside*np.sqrt(720.)
        ranked=np.argsort(-score,kind="stable")[:3]
        raw=np.maximum(score[ranked],0.)+.02
        if np.all(score[ranked]<=0.):
            signals[t,0,0]=.5
            signals[t,0,1]=.5
        else:
            signals[t,0,ranked]=raw/raw.sum()
        budgets[t,0]=CORE[regime]
        updates[t]=True

        # A breakout at the completed t close must beat the prior 192 closes.
        prior_high=np.max(c[t-192:t],axis=0)
        breakout=c[t]/prior_high-1.
        participation=q24[t]>=1.10*np.median(q24[t-192:t],axis=0)
        eligible=(breakout>0.)&participation
        if eligible.any():
            j=int(np.argmax(np.where(eligible,breakout,-np.inf)))
            signals[t,1,j]=1.
            budgets[t,1]=OPPORTUNITY

        # Relative acceleration is a signed, dollar-neutral cross-sectional spread.
        acceleration=net168-.25*net720
        high_idx=int(np.argmax(acceleration))
        low_idx=int(np.argmin(acceleration))
        if (high_idx!=low_idx and
            acceleration[high_idx]-acceleration[low_idx]>=.05 and breadth>=2):
            signals[t,2,high_idx]=1.
            signals[t,2,low_idx]=-1.
            budgets[t,2]=RV

        # Only an adverse basket trend with pronounced dispersion earns a short hedge.
        if float(np.mean(net72))<0. and float(np.ptp(net72))>.025:
            j=int(np.argmin(net72))
            signals[t,3,j]=-1.
            budgets[t,3]=STRESS

    if (np.any(budgets<0) or not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals[:,0,:]),axis=1)>1.+1e-12) or
        np.any(np.abs(np.sum(signals[:,2,:],axis=1))>1e-12) or
        np.any(np.sum(abs(signals[:,1:,:]),axis=2)>2.+1e-12) or
        np.any(np.sum(abs(signals)*budgets[:,:,None],axis=(1,2))>GROSS_CAP+1e-12)):
        raise ValueError("FA_GROSS_OR_SIGNED_FINANCING_INVARIANT")
    return signals,updates,regimes,budgets

def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(np.sum(a[0][:,2,:],axis=1),0.,atol=1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("FA_CAUSAL_STATIC_PASS")
