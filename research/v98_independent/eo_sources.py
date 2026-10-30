#!/usr/bin/env python3
"""EO self-financing factor-tilt seven-slot portfolio sources, 2023/24 training."""
import numpy as np
WARMUP=744
CLOCKS=(72,72,72,24)
CORE={"TREND":2.0,"MIXED":1.8,"STRESS":1.4}
TILT=np.array([.12,.12,.16])
CAP=2.40

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EO_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    qcum=np.cumsum(q,axis=0)
    q24=qcum.copy();q24[24:]-=qcum[:-24]
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    held=np.zeros((4,4))
    last=np.zeros(4)
    for t in range(WARMUP,n,24):
        net480=lc[t]-lc[t-480]-np.sum(r[t-479:t+1]*e[t-479:t+1],axis=0)
        breadth=int(np.count_nonzero(net480>0))
        regime="TREND" if breadth>=3 else "STRESS" if breadth<=1 else "MIXED"
        regimes[t]=regime
        changed=np.zeros(4,dtype=bool)
        if (t-WARMUP)%72==0:
            confirm=lc[t]-lc[t-120]
            score=np.where(confirm>0,np.maximum(net480,0.),0.)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            held[0]=.25*np.full(4,.25)+.75*w
            changed[0]=True
            net72=lc[t]-lc[t-72]-np.sum(r[t-71:t+1]*e[t-71:t+1],axis=0)
            hi=int(np.argmax(net72));lo=int(np.argmin(net72))
            held[1]=0.
            if (hi!=lo and net72[hi]>0. and
                q24[t,hi]>np.median(q24[t-168:t,hi])):
                held[1,hi]=.5;held[1,lo]=-.5
            changed[1]=True
            efficiency=(c[t]-c[t-240])/np.maximum(
                np.sum(h[t-239:t+1]-l[t-239:t+1],axis=0),1e-8)
            hi=int(np.argmax(efficiency));lo=int(np.argmin(efficiency))
            held[2]=0.
            if hi!=lo and efficiency[hi]>0. and efficiency[lo]<0.:
                held[2,hi]=.5;held[2,lo]=-.5
            changed[2]=True
        # Stress/Recovery source is observed daily, not retroactively during a bar.
        held[3]=0.
        market72=float(np.mean(lc[t]-lc[t-72]))
        daily=lc[t]-lc[t-24]
        if market72<-.03 and float(np.mean(daily))>0. and np.count_nonzero(daily>0)>=3:
            hi=1+int(np.argmax(daily[1:]))
            lo=int(np.argmin(daily))
            if hi!=lo:
                held[3,hi]=.5;held[3,lo]=-.5
        changed[3]=True
        requested=np.array([CORE[regime],*(
            TILT[i-1] if np.any(held[i]) else 0. for i in (1,2,3))])
        remaining=CAP
        effective=np.zeros(4)
        for i in range(4):
            effective[i]=min(requested[i],remaining)
            remaining=max(0.,remaining-effective[i])
        if effective.sum()>CAP+1e-12:
            raise ValueError("EO_HIDDEN_LEVERAGE")
        for i in range(4):
            if changed[i] or abs(effective[i]-last[i])>1e-12:
                signals[t,i]=held[i]
                budgets[t,i]=effective[i]
                updates[t,i]=True
        last=effective.copy()
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EO_SOURCE_GROSS")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EO_NONFINITE_BUDGET")
    return signals,updates,regimes,budgets

def static_check():
    n=3600;t=np.arange(n,dtype=float)
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
        assert np.all(a[1][np.arange(WARMUP,n,clock),i])
    return True
if __name__=="__main__":
    assert static_check()
    print("EO_SELF_FINANCING_JOINT_TILTS_CAUSAL_STATIC_PASS")
