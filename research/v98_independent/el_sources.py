#!/usr/bin/env python3
"""EL causal capital-vacancy complete seven-slot source; pinned 2023-24 training only."""
import numpy as np
WARMUP=744
CLOCKS=(96,48,72,24)
CORE_BUDGET={"TREND":3.0,"MIXED":2.5,"RISK_OFF":1.5}
SAT_BUDGET={"TREND":(.20,.12,.10),"MIXED":(.16,.16,.16),"RISK_OFF":(.08,.18,.22)}
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
        raise ValueError("EL_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    held=np.zeros((4,4))
    last_budgets=np.zeros(4)
    for t in range(WARMUP,n,24):
        net336=lc[t]-lc[t-336]-np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        breadth=int(np.count_nonzero(net336>0))
        m72=float(market[t]-market[t-72])
        regime=("TREND" if breadth>=3 and m72>0 else
                "RISK_OFF" if breadth<=1 and m72<0 else "MIXED")
        regimes[t]=regime
        signal_changed=np.zeros(4,dtype=bool)
        if (t-WARMUP)%96==0:
            semivol=np.sqrt(np.mean(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
            score=np.where(lc[t]-lc[t-72]>0,np.maximum(net336,0.),0.)/np.maximum(semivol,1e-7)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            held[0]=.15*np.full(4,.25)+.85*w
            signal_changed[0]=True
        if (t-WARMUP)%48==0:
            accel=(lc[t]-lc[t-24])-(lc[t-24]-lc[t-48])
            net168=lc[t]-lc[t-168]-np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            options=[(float(accel[j]),j) for j in (1,2,3)
                     if accel[j]>0 and lc[t,j]-lc[t-24,j]>0 and net168[j]>0]
            held[1]=0.
            if options:
                _,j=max(options,key=lambda z:(z[0],-z[1]))
                held[1,j]=1.
            signal_changed[1]=True
        if (t-WARMUP)%72==0:
            # Positive funding is an expense to longs and a receipt to shorts.
            carry=np.sum(r[t-167:t+1]*e[t-167:t+1],axis=0)
            long=int(np.argmin(carry));short=int(np.argmax(carry))
            held[2]=0.
            if long!=short and carry[short]>carry[long] and (lc[t,long]-lc[t-72,long])>(lc[t,short]-lc[t-72,short]):
                held[2,long]=.5;held[2,short]=-.5
            signal_changed[2]=True
        if True:
            m24=mret[t-23:t+1]
            recent=np.sqrt(np.mean(np.minimum(m24,0.)**2))
            old=np.sqrt(np.mean(np.minimum(mret[t-167:t+1],0.)**2))
            held[3]=0.
            if recent>old and market[t]-market[t-24]<0:
                weakest=1+int(np.argmin(lc[t,1:]-lc[t-24,1:]))
                held[3,0]=.5;held[3,weakest]=-.5
            signal_changed[3]=True
        vm=float(np.clip(.008/max(float(np.std(mret[t-167:t+1])),1e-8),.5,1.2))
        requested=np.zeros(4)
        requested[0]=CORE_BUDGET[regime]
        for i in (1,2,3):
            requested[i]=SAT_BUDGET[regime][i-1]*vm if np.any(held[i]) else 0.
        effective=np.zeros(4)
        remaining=TOTAL_GROSS_DEMAND
        for i in range(4):
            effective[i]=min(requested[i],remaining)
            remaining=max(0.,remaining-effective[i])
        # Every 24h the allocator is allowed to re-authorize changed budgets;
        # underlying signal observations remain at their fixed independent clocks.
        for i in range(4):
            if signal_changed[i] or abs(effective[i]-last_budgets[i])>1e-12:
                signals[t,i]=held[i]
                budgets[t,i]=effective[i]
                updates[t,i]=True
        last_budgets=effective.copy()
        if sum(effective)>TOTAL_GROSS_DEMAND+1e-10:
            raise ValueError("EL_VACANCY_BUDGET")
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EL_SOURCE_GROSS")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EL_BUDGET_INVALID")
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
    print("EL_CAUSAL_CAPITAL_VACANCY_SEVEN_SLOT_STATIC_PASS")
