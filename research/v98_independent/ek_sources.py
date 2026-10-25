#!/usr/bin/env python3
"""EK causal asymmetric stability-growth seven-slot native source, 2023-24 training only."""
import numpy as np
WARMUP=744
CLOCKS=(120,48,72,24)
CORE_BUDGET={"TREND":3.45,"MIXED":2.70,"RISK_OFF":1.50}
SAT_BUDGET={"TREND":(.13,.11,.09),"MIXED":(.15,.15,.13),"RISK_OFF":(.07,.14,.20)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EK_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,24):
        net480=lc[t]-lc[t-480]-np.sum(r[t-479:t+1]*e[t-479:t+1],axis=0)
        breadth=int(np.count_nonzero(net480>0))
        m120=float(market[t]-market[t-120])
        regime=("RISK_OFF" if m120<-.02 and breadth<=1 else
                "TREND" if m120>0 and breadth>=3 else "MIXED")
        regimes[t]=regime
        raw=np.zeros((4,4))
        if (t-WARMUP)%120==0:
            v=np.std(hourly[t-479:t+1],axis=0)
            score=np.where(lc[t]-lc[t-120]>0,np.maximum(net480,0.),0.)/np.maximum(v,1e-6)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            raw[0]=.12*np.full(4,.25)+.88*w
            updates[t,0]=True
            signals[t,0]=raw[0]
            budgets[t,0]=CORE_BUDGET[regime]
        if (t-WARMUP)%48==0:
            p48=lc[t]-lc[t-48]
            net240=lc[t]-lc[t-240]-np.sum(r[t-239:t+1]*e[t-239:t+1],axis=0)
            options=[(p48[j],j) for j in (1,2,3) if p48[j]>0 and net240[j]>0]
            if options:
                _,j=max(options,key=lambda z:(z[0],-z[1]))
                raw[1,j]=1.
            updates[t,1]=True
        if (t-WARMUP)%72==0:
            p72=lc[t]-lc[t-72]
            downside=np.sqrt(np.mean(np.minimum(hourly[t-239:t+1],0.)**2,axis=0))
            options=[(downside[j],j) for j in (1,2,3) if p72[j]>0]
            if options:
                _,j=min(options,key=lambda z:(z[0],z[1]))
                raw[2,j]=1.
            updates[t,2]=True
        if market[t]-market[t-168]<0 and market[t]-market[t-24]>0:
            raw[3,0]=.5;raw[3,1]=.5
        updates[t,3]=True
        vm=float(np.clip(.008/max(float(np.std(mret[t-239:t+1])),1e-8),.5,1.2))
        for i in (1,2,3):
            if updates[t,i]:
                signals[t,i]=raw[i]
                budgets[t,i]=SAT_BUDGET[regime][i-1]*vm if np.any(raw[i]) else 0.
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EK_SOURCE_GROSS")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EK_BUDGET_INVALID")
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
    assert np.all(np.sum(np.abs(a[0]),axis=2)<=1.+1e-12)
    assert np.all(np.isfinite(a[3]))
    for i,clock in enumerate(CLOCKS):
        assert np.array_equal(np.flatnonzero(a[1][:,i]),np.arange(WARMUP,n,clock))
    return True
if __name__=="__main__":
    assert static_check()
    print("EK_CAUSAL_ASYMMETRIC_SEVEN_SLOT_STATIC_PASS")
