#!/usr/bin/env python3
"""EJ causal native long-only convex trend/relative discount/recovery seven-slot source."""
import numpy as np
WARMUP=744
CLOCKS=(72,48,24,24)
CORE_BUDGET={"TREND":3.60,"MIXED":2.80,"RISK_OFF":1.40}
SAT_BUDGET={"TREND":(.18,.13,.10),"MIXED":(.16,.16,.14),"RISK_OFF":(.07,.08,.20)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EJ_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,24):
        net504=lc[t]-lc[t-504]-np.sum(r[t-503:t+1]*e[t-503:t+1],axis=0)
        breadth=int(np.count_nonzero(net504>0))
        m96=float(market[t]-market[t-96])
        regime=("RISK_OFF" if m96<-.03 and breadth<=1 else
                "TREND" if m96>0 and breadth>=3 else "MIXED")
        regimes[t]=regime
        raw=np.zeros((4,4))
        if (t-WARMUP)%72==0:
            rv=np.std(hourly[t-503:t+1],axis=0)
            score=np.where(lc[t]-lc[t-72]>0,np.maximum(net504,0.),0.)/np.maximum(rv,1e-6)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            raw[0]=.10*np.full(4,.25)+.90*w
            updates[t,0]=True
            signals[t,0]=raw[0]
            budgets[t,0]=CORE_BUDGET[regime]
        if (t-WARMUP)%48==0:
            net168=lc[t]-lc[t-168]-np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            candidates=[]
            for j in (1,2,3):
                prev_high=float(np.max(h[t-96:t,j]))
                vol24=float(np.mean(q[t-23:t+1,j]))
                prev96=float(np.mean(q[t-119:t-23,j]))
                if net168[j]>0 and c[t,j]>prev_high and vol24>prev96:
                    candidates.append((net168[j],j))
            if candidates:
                _,j=max(candidates,key=lambda z:(z[0],-z[1]))
                raw[1,j]=1.
            updates[t,1]=True
        # Long-only relative discount conditional on a native uptrend and recovery.
        r24=lc[t]-lc[t-24]
        r6=lc[t]-lc[t-6]
        median=float(np.median(r24[1:4]))
        options=[(median-r24[j],j) for j in (1,2,3) if net504[j]>0 and r6[j]>0]
        if options:
            _,j=max(options,key=lambda z:(z[0],-z[1]))
            raw[2,j]=1.
        updates[t,2]=True
        # Broad rebound participation after market drawdown, no short hedge.
        if market[t]-market[t-48]<0 and market[t]-market[t-6]>0 and np.count_nonzero(r6>0)>=2:
            best=sorted(range(4),key=lambda j:(-r6[j],j))[:2]
            raw[3,best]=.5
        updates[t,3]=True
        vm=float(np.clip(.008/max(float(np.std(mret[t-167:t+1])),1e-8),.5,1.2))
        for i in (1,2,3):
            if updates[t,i]:
                signals[t,i]=raw[i]
                budgets[t,i]=SAT_BUDGET[regime][i-1]*vm if np.any(raw[i]) else 0.
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EJ_SOURCE_GROSS")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EJ_BUDGET_INVALID")
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
    print("EJ_CAUSAL_COMPOSED_SEVEN_SLOT_STATIC_PASS")
