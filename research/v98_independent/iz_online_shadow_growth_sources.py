#!/usr/bin/env python3
"""IZ: preregistered causal online-shadow seven-slot sources, no economic PnL, 2023-24 only."""
from __future__ import annotations
import numpy as np
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"NORMAL":1.0,"STRESS":.8,"RECOVERY":.95}
START_SHADOW=744
SHADOW=672
MIN_EDGE=.01
MIN_EPOCHS=2
SHADOW_TURNOVER_COST=.0008
SHADOW_RESERVE_DAILY=.00015

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(z,dtype=float) for z in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape or not np.isfinite(z).all() for z in (o,h,l,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IZ_INVALID_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4))
    validity=np.ones((n,4),dtype=bool)
    shadow_edges=np.full((n,3),np.nan)
    for t in range(WARMUP,n,CLOCK):
        h672=ret[t-671:t+1]
        h336=ret[t-335:t+1]
        h168=ret[t-167:t+1]
        vol672=np.maximum(np.std(h672,axis=0),.002)
        vol168=np.maximum(np.std(h168,axis=0),.002)
        funding=np.sum(r[t-671:t+1]*e[t-671:t+1],axis=0)
        trend=np.log(c[t]/c[t-672])-funding-.5*vol672*np.sqrt(672.)
        pos=np.sqrt(np.maximum(trend,0.))
        signals[t,0]=pos/pos.sum() if pos.sum()>0 else np.full(4,.25)
        m168=np.sum(h168,axis=0)
        ratio=float(np.median(vol168/vol672))
        med=float(np.median(m168))
        regime=("STRESS" if med<0 and ratio>1.25 else
                "RECOVERY" if med>0 and ratio<.85 else "NORMAL")
        regimes[t]=regime
        valid=bool(np.all(q[t-671:t+1]>0))
        validity[t,1:]=valid
        if valid:
            breakout=(c[t]/np.max(h[t-336:t],axis=0)-1.)/vol168
            if float(np.max(breakout))>0:
                signals[t,1,int(np.argmax(breakout))]=1.
            residual=np.sum(h336,axis=0)-float(np.median(np.sum(h336,axis=0)))
            downside=np.maximum(np.sqrt(np.mean(np.minimum(h336,0.)**2,axis=0)),.002)
            ranked=np.argsort(residual/downside,kind="stable")
            signals[t,2,int(ranked[-1])]=.5
            signals[t,2,int(ranked[0])]=-.5
            if regime=="STRESS":
                signals[t,3,int(np.argmin(m168))]=-1.
            elif regime=="RECOVERY":
                signals[t,3,int(np.argmax(m168))]=1.
            else:
                downside168=np.mean(np.minimum(h168,0.)**2,axis=0)
                signals[t,3,int(np.argmin(downside168))]=1.
        # Shadow history is strictly prior to the allocation decision; only
        # completed closes and native funding known at t, and epoch targets
        # from epochs <= t-336. Never use future performance of current signal.
        qualified=[]
        if t>=WARMUP+2*CLOCK:
            start=max(WARMUP,t-SHADOW)
            epochs=list(range(start,t,CLOCK))
            if len(epochs)>=MIN_EPOCHS:
                shadow=np.zeros(4)
                prev=np.zeros((4,4))
                for epoch in epochs:
                    current=signals[epoch]
                    if epoch>start:
                        shadow-=SHADOW_TURNOVER_COST*np.abs(current-prev).sum(axis=1)
                    prev=current
                    end=min(epoch+CLOCK,t)
                    # Next-hour price move/funding from previous completed
                    # epoch close; never receive PnL on the signal hour.
                    shadow+=np.sum(net[epoch+1:end+1]@current.T,axis=0)
                for i in range(1,4):
                    edge=float(shadow[i]-shadow[0]-SHADOW_RESERVE_DAILY*((t-start)/24.))
                    shadow_edges[t,i-1]=edge
                    if valid and np.abs(signals[t,i]).sum()>0 and edge>MIN_EDGE:
                        qualified.append((i,min(.10,max(.01,edge))))
        budgets[t,0]=1.
        if qualified:
            total=sum(weight for _,weight in qualified)
            budgets[t,0]=.55
            for i,weight in qualified:
                budgets[t,i]=.45*weight/total
        updates[t]=True
        if (not np.isclose(budgets[t].sum(),1.,atol=1e-12)
            or np.any(budgets[t]<0)
            or not np.isclose(signals[t,0].sum(),1.,atol=1e-12)
            or not np.all(np.isclose(np.abs(signals[t]).sum(axis=1),0.,atol=1e-12)
                          |np.isclose(np.abs(signals[t]).sum(axis=1),1.,atol=1e-12))
            or np.any((budgets[t,1:]>0)&(~validity[t,1:]))):
            raise ValueError("IZ_BUDGET_OR_SOURCE_GUARD")
    return signals,updates,regimes,budgets,validity,shadow_edges

def static_check():
    n=4000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/83.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);r[:,2]=-.0001
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IZ_FUTURE_MUTATION_"+str(i))
    if not np.array_equal(a[5][:3200],b[5][:3200],equal_nan=True):
        raise ValueError("IZ_SHADOW_FUTURE_MUTATION")
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.allclose(a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IZ_BUDGET_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    gap=bundle(o,h,l,c,r,e,qgap)
    if np.any(gap[0][WARMUP,1:]) or gap[4][WARMUP,1:].any():
        raise ValueError("IZ_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IZ_CAUSAL_SHADOW_BUDGET_AND_QUARANTINE_PASS")
