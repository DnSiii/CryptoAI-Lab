#!/usr/bin/env python3
"""GU seven-slot native OHLC quote-volume pressure shock recovery, TRAINING ONLY."""
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":2.25,"TRANSITION":1.80,"STRESS":1.20}
PRIOR=np.array([.55,.15,.15,.15],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GU_INVALID_PINNED_SOURCE")
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
        # Native completed-hour close-location pressure with prior-only volume scale.
        previous_volume=np.maximum(np.mean(q[t-167:t-23],axis=0),1.)
        range24=h[t-23:t+1]-l[t-23:t+1]
        clv=np.divide(2.*c[t-23:t+1]-h[t-23:t+1]-l[t-23:t+1],
                      range24,out=np.zeros_like(range24),where=range24>0)
        volume_ratio=np.clip(q[t-23:t+1]/previous_volume,.25,4.)
        pressure=np.sum(clv*volume_ratio,axis=0)
        pressure_asset=int(np.argmax(pressure))
        chosen=pressure_asset if stress_trigger and pressure[pressure_asset]>0 else core
        signals[t,3,chosen]=1.
        regimes[t]="STRESS" if stress_trigger else "TREND" if breadth>=3 else "TRANSITION"
        budgets[t]=PRIOR
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or np.any(signals[t]<0) or
            not np.allclose(np.sum(signals[t,:3],axis=1),1.,atol=1e-12) or
            not np.isclose(np.sum(signals[t,3]),1.,atol=1e-12)):
            raise ValueError("GU_INVALID_FINANCED_BOOK")
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
    assert np.allclose(np.sum(a[0],axis=2)[np.arange(WARMUP,n,CLOCK)],1.)
    return True
if __name__=="__main__":
    assert static_check()
    print("GU_CAUSAL_CANDLE_PRESSURE_STATIC_PASS")
