#!/usr/bin/env python3
"""EI independent causal event-driven cooperative seven-slot source, TRAINING only."""
import numpy as np
WARMUP=744
CLOCKS=(96,24,24,24)
CORE_BUDGET={"TREND":3.15,"MIXED":2.70,"RISK_OFF":1.40}
SAT_BUDGET={"TREND":(.15,.10,.10),"MIXED":(.16,.13,.14),"RISK_OFF":(.08,.15,.20)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("EI_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    hourly=np.diff(lc,axis=0,prepend=lc[:1])
    market=lc.mean(axis=1);mret=hourly.mean(axis=1)
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U10")
    budgets=np.zeros((n,4))
    prev=np.zeros((4,4))
    previous_regime=None
    for t in range(WARMUP,n,24):
        net336=lc[t]-lc[t-336]-np.sum(r[t-335:t+1]*e[t-335:t+1],axis=0)
        breadth=int(np.count_nonzero(net336>0))
        m72=float(market[t]-market[t-72])
        regime=("RISK_OFF" if m72<-.025 and breadth<=1 else
                "TREND" if m72>0 and breadth>=3 else "MIXED")
        regimes[t]=regime
        raw=np.zeros((4,4))
        if (t-WARMUP)%96==0:
            down=np.sqrt(np.mean(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
            score=np.maximum(net336-.5*down,0.)
            w=score/score.sum() if score.sum()>1e-12 else np.full(4,.25)
            raw[0]=.2*np.full(4,.25)+.8*w
            updates[t,0]=True
            signals[t,0]=raw[0]
            budgets[t,0]=CORE_BUDGET[regime]
            prev[0]=raw[0]
        # Opportunity: volume-confirmed moving-average continuation.
        eligible=[]
        for j in (1,2,3):
            p24=float(lc[t,j]-lc[t-24,j])
            p48=float(lc[t,j]-lc[t-48,j])
            ma168=float(np.mean(c[t-167:t+1,j]))
            vol48=float(np.mean(q[t-47:t+1,j]))
            prev168=float(np.mean(q[t-215:t-47,j]))
            if p24>0 and c[t,j]>ma168 and vol48>1.15*prev168:
                eligible.append((p48,j))
        if eligible:
            _,j=max(eligible,key=lambda z:(z[0],-z[1]))
            raw[1,j]=1.
        # Relative value: cross-sectional 48h candle-efficiency spread.
        clv=(c[t-47:t+1,1:4]-l[t-47:t+1,1:4]) / np.maximum(
            h[t-47:t+1,1:4]-l[t-47:t+1,1:4],1e-12)
        avg=np.mean(clv,axis=0)
        winner=1+int(np.argmax(avg));loser=1+int(np.argmin(avg))
        r48=lc[t]-lc[t-48]
        if (winner!=loser and avg[winner-1]-avg[loser-1]>.18 and
            r48[winner]>0 and r48[loser]<r48[winner]):
            raw[2,winner]=.5;raw[2,loser]=-.5
        # Stress/Recovery: long-only broad participation after a down 72h tape.
        r12=lc[t]-lc[t-12]
        if m72<0 and float(market[t]-market[t-12])>0 and np.count_nonzero(r12>0)>=3:
            top=sorted(range(4),key=lambda j:(-r12[j],j))[:2]
            raw[3,top]=.5
        vol=float(np.std(mret[t-167:t+1]))
        vm=float(np.clip(.008/max(vol,1e-8),.5,1.15))
        # Event-only trading: changed signal/regime or deterministic 168h checkpoint.
        for i in (1,2,3):
            changed=not np.array_equal(raw[i],prev[i])
            checkpoint=(t-WARMUP)%168==0
            if changed or checkpoint or regime!=previous_regime:
                updates[t,i]=True
                signals[t,i]=raw[i]
                budgets[t,i]=SAT_BUDGET[regime][i-1]*vm if np.any(raw[i]) else 0.
                prev[i]=raw[i].copy()
        previous_regime=regime
    if np.any(np.sum(np.abs(signals),axis=2)>1.+1e-12):
        raise ValueError("EI_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("EI_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("EI_BUDGET_INVALID")
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
    assert np.array_equal(np.flatnonzero(a[1][:,0]),np.arange(WARMUP,n,96))
    for i in (1,2,3):
        idx=np.flatnonzero(a[1][:,i])
        assert np.all((idx-WARMUP)%24==0)
        assert len(idx)>0
    return True
if __name__=="__main__":
    assert static_check()
    print("EI_CAUSAL_EVENT_DRIVEN_SEVEN_SLOT_STATIC_PASS")
