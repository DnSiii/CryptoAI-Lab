#!/usr/bin/env python3
"""GQ signed native futures carry-spread / crash-beta hedge complete seven-slot TRAINING-only engine."""
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"TREND":2.25,"TRANSITION":1.80,"STRESS":1.20}
COEFF={"TREND":(.35,.40,.35),"TRANSITION":(.30,.50,.45),"STRESS":(.15,.60,.65)}

def centered(v):
    x=np.asarray(v,dtype=float)-np.mean(v)
    return x/max(.05,float(np.max(np.abs(x))))

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GQ_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4))
    past=[[] for _ in range(3)]
    def native(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net48,net168,net336,net672=(native(t,w) for w in (48,168,336,672))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        downside_vol=np.maximum(np.sqrt(np.mean(np.minimum(hourly,0.)**2,axis=0)),.002)
        core=np.maximum(.5*net336+.5*net672,0.)/downside_vol+.05
        signals[t,0]=core/core.sum()

        # Candle location x native quote-volume pressure, completed 48h only.
        location=(c[t-47:t+1]-l[t-47:t+1]) / np.maximum(
            h[t-47:t+1]-l[t-47:t+1],1e-9)-.5
        pressure=np.sum(location*q[t-47:t+1],axis=0) / np.maximum(
            48.*np.mean(q[t-167:t+1],axis=0),1.)
        signals[t,1]=centered(pressure)

        # Signed carry spread; actual shorts/longs are risk-authorized later.
        burden=funding[t+1]-funding[t-167]
        vol=np.maximum(np.std(hourly,axis=0),.002)
        signals[t,2]=centered(-burden/vol)

        # Defensive crash-beta hedge with intrabar downside survivorship.
        market=hourly.mean(axis=1)
        betas=np.clip(np.mean((hourly-hourly.mean(axis=0))*
                              (market-market.mean())[:,None],axis=0)/
                      max(float(np.var(market)),1e-10),0.,3.)
        down=np.maximum((o-l)/o,0.)
        ratio=np.mean(down[t-47:t+1],axis=0)/np.maximum(
            np.mean(down[t-167:t+1],axis=0),.0001)
        signals[t,3]=centered(-betas*max(0.,-float(np.mean(net48)))-ratio)

        breadth=int(np.count_nonzero(net336>0))
        regime=("STRESS" if float(np.median(net48))<-.08 or
                float(np.median(np.mean(down[t-167:t+1],axis=0)))>.10 else
                "TREND" if breadth>=3 else "TRANSITION")
        regimes[t]=regime
        budgets[t,0]=GROSS[regime]
        if t>=WARMUP+CLOCK:
            prior=t-CLOCK
            for i in range(1,4):
                past[i-1].append(float(signals[prior,i]@net168))
                if len(past[i-1])>4:past[i-1].pop(0)
        for i,coeff in enumerate(COEFF[regime],start=1):
            quality=np.clip(.35+2.*(np.mean(past[i-1]) if past[i-1] else 0.),.20,.65)
            budgets[t,i]=coeff*quality
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or np.any(budgets[t]<=0) or
            abs(signals[t,0].sum()-1.)>1e-10 or np.any(signals[t,0]<0) or
            np.any(np.abs(signals[t,1:].sum(axis=1))>1e-10)):
            raise ValueError("GQ_INVALID_CAUSAL_FACTOR")
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
    assert np.allclose(np.sum(a[0][:,1:,:],axis=2),0.,atol=1e-10)
    return True

if __name__=="__main__":
    assert static_check()
    print("GQ_CAUSAL_SIGNED_STATIC_PASS")
