#!/usr/bin/env python3
"""EH causal orthogonality allocator; native four-asset completed-close training only."""
import numpy as np
WARMUP=744
CLOCKS=(120,24,24,24)
CORE_BUDGET={"TREND":3.25,"MIXED":2.65,"RISK_OFF":1.60}
SAT_BUDGET={"TREND":(.16,.12,.12),"MIXED":(.15,.18,.20),"RISK_OFF":(.08,.18,.30)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EH_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    current_core=np.full(4,.25)
    for t in range(WARMUP,n,24):
        native480=np.sum(r[t-479:t+1]*e[t-479:t+1],axis=0)
        net480=lc[t]-lc[t-480]-native480
        breadth=int(np.count_nonzero(net480>0))
        m48=float(market[t]-market[t-48])
        m120=float(market[t]-market[t-120])
        regime=("RISK_OFF" if m48<-.02 and breadth<=1 else
                "TREND" if m120>0 and breadth>=3 else "MIXED")
        regimes[t]=regime
        if (t-WARMUP)%120==0:
            down=np.sqrt(np.mean(np.minimum(hourly[t-479:t+1],0.)**2,axis=0))
            score=np.where(lc[t]-lc[t-120]>0,np.maximum(net480,0.),0.)/np.maximum(down,1e-6)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            current_core=.25*np.full(4,.25)+.75*w
            signals[t,0]=current_core
            budgets[t,0]=CORE_BUDGET[regime]
            updates[t,0]=True
        raw=np.zeros((4,4))
        # Opportunity: price-location and quote-volume confirmed short-term leader.
        options=[]
        for j in (1,2,3):
            hi=float(np.max(h[t-23:t+1,j]))
            lo=float(np.min(l[t-23:t+1,j]))
            clv=float((c[t,j]-lo)/max(hi-lo,1e-8))
            trend120=float(lc[t,j]-lc[t-120,j])
            trend6=float(lc[t,j]-lc[t-6,j])
            v24=float(np.mean(q[t-23:t+1,j]))
            prior=float(np.mean(q[t-143:t-23,j]))
            if trend120>0 and trend6>0 and clv>.60 and v24>prior:
                options.append((trend120,j))
        if options:
            _,j=max(options,key=lambda z:(z[0],-z[1]))
            raw[1,j]=1.
        # RV: realized-volatility spread, trend-confirmed low-vol leadership.
        v=np.std(hourly[t-239:t+1,1:4],axis=0)
        lo=1+int(np.argmin(v));hi=1+int(np.argmax(v))
        if (lo!=hi and float(v[hi]/max(v[lo],1e-8))>1.35 and
            float((lc[t,lo]-lc[t-24,lo])-(lc[t,hi]-lc[t-24,hi]))>0):
            raw[2,lo]=.5;raw[2,hi]=-.5
        # Stress: persistent BTC relative resilience in a falling broad market.
        ret48=lc[t]-lc[t-48]
        weak=min((1,2,3),key=lambda j:(ret48[j],j))
        if m48<0 and float(ret48[0]-ret48[weak])>.01:
            raw[3,0]=.5;raw[3,weak]=-.5
        vol=float(np.std(mret[t-239:t+1]))
        vm=float(np.clip(.0075/max(vol,1e-8),.5,1.2))
        for i in (1,2,3):
            updates[t,i]=True
            s=raw[i]
            if not np.any(s):continue
            # Core-priority signed orthogonality, no return-conditioned selection.
            overlap=abs(float(s@current_core))/(np.linalg.norm(s)*np.linalg.norm(current_core)+1e-12)
            orth=max(.35,1.-overlap)
            signals[t,i]=s
            budgets[t,i]=SAT_BUDGET[regime][i-1]*vm*orth
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EH_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EH_RV_NOT_NEUTRAL")
    if not np.allclose(signals[:,3,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EH_STRESS_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EH_BUDGET_INVALID")
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
    print("EH_CAUSAL_ORTHOGONAL_SEVEN_SLOT_STATIC_PASS")
