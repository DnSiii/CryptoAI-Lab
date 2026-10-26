#!/usr/bin/env python3
"""GW causal whole-book stress migration overlay, no permanently funded fourth sleeve."""
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":2.25,"TRANSITION":1.80,"STRESS":1.20}
PRIOR=np.array([.65,.175,.175,0.],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GW_INVALID_PINNED_SOURCE")
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
        vol=np.maximum(np.std(hourly,axis=0),.002)
        core=int(np.argmax(net672/vol))
        signals[t,0,core]=1.
        prior48=(lc[t-48]-lc[t-96])-(funding[t-47]-funding[t-95])
        recent_q=np.mean(q[t-47:t+1],axis=0)
        prior_q=np.mean(q[t-95:t-47],axis=0)
        ratio=np.clip((recent_q+1.)/(prior_q+1.),.5,2.)
        signals[t,1,np.argmax((net48-prior48)*ratio)]=1.
        burden=funding[t+1]-funding[t-167]
        signals[t,2,np.argmax(-burden/vol)]=1.
        breadth=int(np.count_nonzero(net336>0))
        stress_trigger=float(np.median(net48))<-.025 or breadth<=1
        btc_outperforms=float(net48[0])>=float(np.median(net48[1:]))
        if stress_trigger and btc_outperforms:
            signals[t,3,0]=1. # overlay flag, not funded sleeve
        regimes[t]="STRESS" if stress_trigger else "TREND" if breadth>=3 else "TRANSITION"
        budgets[t]=PRIOR
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or np.any(signals[t]<0) or
            not np.allclose(np.sum(signals[t,:3],axis=1),1.,atol=1e-12) or
            np.sum(signals[t,3]) not in (0.,1.)):
            raise ValueError("GW_INVALID_FINANCED_BOOK")
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
    assert np.allclose(np.sum(a[0][:,:3],axis=2)[np.arange(WARMUP,n,CLOCK)],1.)
    return True
if __name__=="__main__":
    assert static_check()
    print("GW_CAUSAL_WHOLE_BOOK_STRESS_MIGRATION_STATIC_PASS")
