#!/usr/bin/env python3
"""EM causal seven-slot counterfactual displaced-wealth router. 2023/24 only."""
import numpy as np
WARMUP=744
CLOCKS=(96,48,72,24)
CORE_BUDGET={"TREND":2.8,"MIXED":2.4,"RISK_OFF":1.8}
SAT_BUDGET=(.22,.18,.20)
TOTAL_GROSS_DEMAND=3.2

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EM_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    # Completed 24h quote-volume sums, compared to 120 prior completed 24h sums.
    q24=np.zeros_like(q)
    qcs=np.cumsum(q,axis=0)
    q24[23:]=qcs[23:]
    q24[24:]-=qcs[:-24]
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    held=np.zeros((4,4));last_budgets=np.zeros(4)
    for t in range(WARMUP,n,24):
        funding288=np.sum(r[t-287:t+1]*e[t-287:t+1],axis=0)
        net288=lc[t]-lc[t-288]-funding288
        breadth=int(np.count_nonzero(net288>0))
        m72=float(market[t]-market[t-72])
        regime=("TREND" if breadth>=3 and m72>0 else
                "RISK_OFF" if breadth<=1 and m72<0 else "MIXED")
        regimes[t]=regime
        changed=np.zeros(4,dtype=bool)
        if (t-WARMUP)%96==0:
            down=np.sqrt(np.mean(np.minimum(hourly[t-287:t+1],0.)**2,axis=0))
            positive96=np.maximum(lc[t]-lc[t-96],0.)
            score=np.maximum(net288,0.)*positive96/np.maximum(down,1e-7)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            held[0]=.10*np.full(4,.25)+.90*w
            changed[0]=True
        if (t-WARMUP)%48==0:
            held[1]=0.
            options=[]
            for j in (1,2,3):
                prior_high=float(np.max(h[t-120:t,j]))
                if c[t,j]>prior_high and c[t,j]>c[t-24,j] and q24[t,j]>np.median(q24[t-120:t,j]):
                    options.append((float(np.log(c[t,j]/prior_high)),j))
            if options:
                _,j=max(options,key=lambda x:(x[0],-x[1]))
                held[1,j]=1.
            changed[1]=True
        if (t-WARMUP)%72==0:
            held[2]=0.
            b=hourly[t-335:t+1,0]
            denom=max(float(np.mean((b-b.mean())**2)),1e-10)
            scores=[]
            for j in (1,2,3):
                x=hourly[t-335:t+1,j]
                beta=float(np.clip(np.mean((x-x.mean())*(b-b.mean()))/denom,-1.,3.))
                residual=float(lc[t,j]-lc[t-96,j]-beta*(lc[t,0]-lc[t-96,0]))
                scores.append((residual,j))
            lo=min(scores,key=lambda x:(x[0],x[1]))
            hi=max(scores,key=lambda x:(x[0],-x[1]))
            if hi[1]!=lo[1] and hi[0]>lo[0]:
                held[2,hi[1]]=.5;held[2,lo[1]]=-.5
            changed[2]=True
        # Stress is observed every 24h; no hindsight switch within the next bar.
        held[3]=0.
        falling=int(np.count_nonzero(lc[t]-lc[t-24]<0))
        down24=float(np.sqrt(np.mean(np.minimum(mret[t-23:t+1],0.)**2)))
        down168=float(np.sqrt(np.mean(np.minimum(mret[t-167:t+1],0.)**2)))
        if falling>=3 and down24>down168:
            weakest=1+int(np.argmin(lc[t,1:]-lc[t-24,1:]))
            held[3,0]=.5;held[3,weakest]=-.5
        changed[3]=True
        # Frozen causal shadow cost-of-displacement gate. It observes only t and prior bars.
        past_native=lc[t]-lc[t-168]-np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
        core_shadow=float(held[0]@past_native)
        vm=float(np.clip(.008/max(float(np.std(mret[t-167:t+1])),1e-8),.6,1.2))
        requested=np.zeros(4)
        requested[0]=CORE_BUDGET[regime]
        for i in (1,2,3):
            gross=float(np.sum(np.abs(held[i])))
            shadow=float(held[i]@past_native)-.01*gross
            if gross>0 and shadow>.25*core_shadow:
                requested[i]=SAT_BUDGET[i-1]*vm
        remaining=TOTAL_GROSS_DEMAND
        effective=np.zeros(4)
        for i in range(4):
            effective[i]=min(requested[i],remaining)
            remaining=max(0.,remaining-effective[i])
        for i in range(4):
            if changed[i] or abs(effective[i]-last_budgets[i])>1e-12:
                signals[t,i]=held[i]
                budgets[t,i]=effective[i]
                updates[t,i]=True
        last_budgets=effective.copy()
        if np.sum(effective)>TOTAL_GROSS_DEMAND+1e-10:
            raise ValueError("EM_CAPITAL_BUDGET")
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EM_GROSS_INVALID")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EM_BUDGET_INVALID")
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
        assert np.all(a[1][np.arange(WARMUP,n,clock),i])
    return True
if __name__=="__main__":
    assert static_check()
    print("EM_CAUSAL_DISPLACED_WEALTH_SEVEN_SLOT_STATIC_PASS")
