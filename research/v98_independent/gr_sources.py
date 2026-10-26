#!/usr/bin/env python3
"""GR funded long-only specialist tranches: causal seven-slot TRAINING-only source."""
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":2.25,"TRANSITION":1.80,"STRESS":1.20}
TRANCHES={"TREND":(.70,.15,.10,.05),
          "TRANSITION":(.70,.10,.15,.05),
          "STRESS":(.80,.05,.05,.10)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GR_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4))
    def native(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net24,net48,net336,net672=(native(t,w) for w in (24,48,336,672))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        vol168=np.maximum(np.std(hourly,axis=0),.002)
        vol48=np.maximum(np.std(hourly[-48:],axis=0),.002)
        # Growth Core: single deterministic winner, no future-informed ranking.
        core_rank=net672/vol168
        signals[t,0,np.argmax(core_rank)]=1.
        # Opportunity: 48h completed breakout over PRECEDING 168h high.
        prior_hi=np.max(h[t-215:t-47],axis=0)
        compression=np.clip(vol168/vol48,.5,2.)
        breakout=np.where((c[t]>prior_hi)&(net48>0),
                          net48*compression,0.)
        if np.max(breakout)>0:
            signals[t,1,np.argmax(breakout)]=1.
        # Relative value: trend-confirmed native funding receiver, long only.
        burden=funding[t+1]-funding[t-167]
        rv=np.where(net336>0,-burden/vol168,-np.inf)
        if np.isfinite(rv).any():
            signals[t,2,np.argmax(rv)]=1.
        # Stress recovery: positive completed 24h bounce after market drawdown.
        stressed=float(np.median(net48))<-.05
        trough=np.min(l[t-167:t+1],axis=0)
        recovery=np.where(net24>0,net24*
                          np.clip(c[t]/np.maximum(trough,1e-9)-1.,0.,2.),0.)
        if stressed and np.max(recovery)>0:
            signals[t,3,np.argmax(recovery)]=1.
        breadth=int(np.count_nonzero(net336>0))
        regime=("STRESS" if stressed or breadth<=1 else
                "TREND" if breadth>=3 else "TRANSITION")
        regimes[t]=regime
        budgets[t]=TRANCHES[regime]
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            np.any(signals[t]<0) or
            np.any(np.sum(signals[t],axis=1)>1.+1e-12) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12)):
            raise ValueError("GR_INVALID_FINANCED_SIGNAL")
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
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][np.arange(WARMUP,n,CLOCK)].all(axis=1))
    assert np.allclose(a[0].sum(axis=2)[np.arange(WARMUP,n,CLOCK),0],1.)
    assert np.all(a[0]>=0) and np.all(a[0].sum(axis=2)<=1.+1e-12)
    return True
if __name__=="__main__":
    assert static_check()
    print("GR_CAUSAL_FUNDED_TRANCHES_STATIC_PASS")
