#!/usr/bin/env python3
"""EG independent preregistered causal virtual-edge opportunity-cost router; TRAINING ONLY."""
import numpy as np
WARMUP=1440
CLOCKS=(168,24,24,24)
CORE={"TREND":3.30,"MIXED":2.70,"RISK_OFF":1.70}
SAT={"TREND":(.18,.13,.12),"MIXED":(.14,.17,.16),"RISK_OFF":(.05,.17,.24)}
EDGE_TOLL=.002
EDGE_LOOKBACK=14
EDGE_MIN_OBS=8
EDGE_THRESHOLD=.002

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EG_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1)
    market_hourly=hourly.mean(axis=1)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    previous=np.zeros((4,4))
    before_previous=np.zeros((4,4))
    virtual_history=[[],[],[],[]]
    for t in range(WARMUP,n,24):
        # A completed 24h interval is known only at this completed close.
        if t>WARMUP:
            interval=c[t]/c[t-24]-1.
            for i in (1,2,3):
                pnl=float(previous[i]@interval)
                switching=float(EDGE_TOLL*np.abs(previous[i]-before_previous[i]).sum())
                virtual_history[i].append(pnl-switching)
        net504=lc[t]-lc[t-504]-np.sum(r[t-503:t+1]*e[t-503:t+1],axis=0)
        market336=float(market[t]-market[t-336])
        market72=float(market[t]-market[t-72])
        breadth=int(np.count_nonzero(net504>0))
        regime=("RISK_OFF" if market72<-.025 and breadth<=1 else
                "TREND" if market336>0 and breadth>=3 else "MIXED")
        regimes[t]=regime
        vol168=float(np.std(market_hourly[t-167:t+1]))
        multiplier=float(np.clip(.007/max(vol168,1e-8),.40,1.15))
        raw=np.zeros((4,4))
        if (t-WARMUP)%168==0:
            downside=np.sqrt(np.mean(np.minimum(hourly[t-503:t+1],0.)**2,axis=0))
            momentum168=lc[t]-lc[t-168]
            score=np.where(momentum168>0,np.maximum(net504,0.),0.)/np.maximum(downside,1e-6)
            weights=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            raw[0]=.20*np.full(4,.25)+.80*weights
            signals[t,0]=raw[0];budgets[t,0]=CORE[regime];updates[t,0]=True
        # Opportunity: continuation after a short, completed pullback.
        options=[]
        for j in (1,2,3):
            net336=float(lc[t,j]-lc[t-336,j]-np.sum(r[t-335:t+1,j]*e[t-335:t+1,j]))
            pullback=float(lc[t-3,j]-lc[t-15,j])
            rebound=float(lc[t,j]-lc[t-3,j])
            v24=float(np.mean(q[t-23:t+1,j]))
            prior=float(np.mean(q[t-191:t-23,j]))
            if net336>0 and pullback<0 and rebound>0 and v24>=.70*prior:
                options.append((net336,j))
        if options:
            _,j=max(options,key=lambda z:(z[0],-z[1]))
            raw[1,j]=1.
        # RV: mean reversion of trailing BTC-beta-adjusted residuals.
        x=hourly[t-503:t+1,0];xc=x-x.mean()
        var=float(xc@xc)
        beta=np.zeros(4)
        for j in (1,2,3):
            y=hourly[t-503:t+1,j]
            beta[j]=float(xc@(y-y.mean()))/max(var,1e-12)
        res72=np.array([(lc[t,j]-lc[t-72,j])-beta[j]*(lc[t,0]-lc[t-72,0])
                        for j in range(4)])
        res12=np.array([(lc[t,j]-lc[t-12,j])-beta[j]*(lc[t,0]-lc[t-12,0])
                        for j in range(4)])
        hi=max((1,2,3),key=lambda j:(res72[j],-j))
        lo=min((1,2,3),key=lambda j:(res72[j],j))
        if hi!=lo and res72[hi]-res72[lo]>.02 and res12[lo]-res12[hi]>0:
            raw[2,lo]=.5;raw[2,hi]=-.5
        # Stress: relative resilience rather than shorting the entire market.
        down24=float(np.sqrt(np.mean(np.minimum(market_hourly[t-23:t+1],0.)**2)))
        down336=float(np.sqrt(np.mean(np.minimum(market_hourly[t-335:t+1],0.)**2)))
        price72=lc[t]-lc[t-72]
        weakest=min((1,2,3),key=lambda j:(price72[j],j))
        if (market72<-.025 and down24>1.1*max(down336,1e-8)
            and price72[0]-price72[weakest]>.015):
            raw[3,0]=.5;raw[3,weakest]=-.5
        for i in (1,2,3):
            updates[t,i]=True
            history=virtual_history[i][-EDGE_LOOKBACK:]
            if (len(history)>=EDGE_MIN_OBS and sum(history)>EDGE_THRESHOLD
                and np.any(raw[i])):
                signals[t,i]=raw[i]
                budgets[t,i]=SAT[regime][i-1]*multiplier
        before_previous=previous.copy()
        previous=raw.copy()
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EG_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EG_RV_NOT_NEUTRAL")
    if not np.allclose(signals[:,3,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EG_STRESS_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EG_BUDGET_INVALID")
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
    print("EG_CAUSAL_OPPORTUNITY_COST_ROUTER_STATIC_PASS")
