#!/usr/bin/env python3
"""KL preregistered event-driven FOUR independent unit-row source intents. Source-only; NO PnL."""
from __future__ import annotations
import numpy as np
WARMUP=744
ASSETS=4
BUDGET=np.array([.62,.16,.12,.10])
SLEEVES=("core","opportunity","relative_value","stress_recovery")
PATHS=("KL_core_only","KL_full","KL_minus_opportunity","KL_minus_RV","KL_minus_stress")
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=ASSETS or len(c)<=WARMUP or
        any(x.shape!=c.shape or not np.isfinite(x).all() for x in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KL_INVALID_CANONICAL_SOURCE")
    n=len(c)
    net=np.zeros_like(c);net[1:]=np.diff(np.log(c),axis=0);net-=r*e
    market=net.mean(axis=1)
    # Row weights represent one-time NAV fractions at their own decision close.
    # They MUST be converted into frozen UNITS by the later physical runner.
    intents=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    valid=np.zeros(n,dtype=bool)
    entries=np.zeros((n,3),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    expiry=np.full(4,-1,dtype=int)
    current=np.zeros((4,4),dtype=float)
    for t in range(WARMUP,n):
        daily=(t-WARMUP)%24==0
        weekly=(t-WARMUP)%168==0
        core_clock=(t-WARMUP)%672==0
        # Close-only decisions; source windows end at t inclusive, actual fills >=t+1.
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        m24=net[t-23:t+1].sum(axis=0)
        m72=net[t-71:t+1].sum(axis=0)
        market24=float(market[t-23:t+1].sum())
        prior72=float(market[t-95:t-23].sum())
        market72=float(market[t-71:t+1].sum())
        if daily:
            regimes[t]=("STRESS" if market72<-.05 else
                        "RECOVERY" if market24>.03 and prior72<0 else "NORMAL")
        else: regimes[t]=regimes[t-1]
        # Expiries are time based, never extended by inactive event sampling.
        for k in (1,2,3):
            if expiry[k]>=0 and t>=expiry[k]:
                current[k]=0.;updates[t,k]=True;expiry[k]=-1
        if core_clock:
            n672=net[t-671:t+1].sum(axis=0)
            down=np.sqrt(np.mean(np.minimum(net[t-671:t+1],0.)**2,axis=0))
            score=n672-.5*down*np.sqrt(168.)
            current[0]=0.
            leader=int(np.argmax(score))
            if score[leader]>0:current[0,leader]=BUDGET[0]
            updates[t,0]=True
        if daily and good and expiry[1]<0:
            recentq=q[t-23:t+1].mean(axis=0)
            priorq=q[t-95:t-23].mean(axis=0)
            eligible=(m24>.04)&(recentq>1.25*priorq)&(c[t]>c[t-71:t+1].mean(axis=0))
            if np.any(eligible):
                k=int(np.argmax(np.where(eligible,m24,-np.inf)))
                current[1]=0.;current[1,k]=BUDGET[1]
                expiry[1]=t+72;updates[t,1]=True;entries[t,0]=True
        if weekly and good and expiry[2]<0:
            # OLS beta with intercept, computed only on historical completed bars.
            xb=net[t-335:t+1,0];vx=float(np.var(xb))
            if vx>=1e-8:
                residual=[]
                for j in (1,2,3):
                    y=net[t-335:t+1,j]
                    beta=float(np.mean((xb-xb.mean())*(y-y.mean()))/vx)
                    residual.append(float(np.sum(y[-72:]-beta*xb[-72:])))
                high_i=int(np.argmax(residual));low_i=int(np.argmin(residual))
                if high_i!=low_i and residual[high_i]>.025 and residual[low_i]<-.025:
                    current[2]=0.
                    current[2,high_i+1]=BUDGET[2]/2
                    current[2,low_i+1]=-BUDGET[2]/2
                    expiry[2]=t+168;updates[t,2]=True;entries[t,1]=True
        if daily and good and expiry[3]<0:
            if market72<-.05:
                down=np.sqrt(np.mean(np.minimum(net[t-167:t+1],0.)**2,axis=0))
                current[3]=0.;current[3,int(np.argmax(down))]=-BUDGET[3]
                expiry[3]=t+48;updates[t,3]=True;entries[t,2]=True
            elif market24>.03 and prior72<0:
                current[3]=0.;current[3,int(np.argmax(m24))]=BUDGET[3]
                expiry[3]=t+72;updates[t,3]=True;entries[t,2]=True
        intents[t]=current
        if np.abs(current).sum()>1.+1e-10:
            raise ValueError("KL_HIDDEN_GROSS")
    return intents,updates,entries,valid,regimes

def static_check():
    n=1900;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
        .045*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[1600:]*=1.8
    qq[1600:]*=4;rr[1600:]*=-1
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1600],b[i][:1600]):
            raise ValueError("KL_FUTURE_LEAK_"+str(i))
    if np.any(np.abs(a[0]).sum(axis=(1,2))>1.+1e-10):
        raise ValueError("KL_GROSS")
    # No asynchronous row changes without a recorded row event.
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("KL_SILENT_ROW_REBALANCE")
    # Explicit source quarantine: a bad quote prevents fresh sleeve entries.
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]):
        raise ValueError("KL_QUOTE_QUARANTINE")
    return True
if __name__=="__main__":
    assert static_check()
    print("KL_SOURCE_SYNTHETIC_CAUSAL_PASS")
