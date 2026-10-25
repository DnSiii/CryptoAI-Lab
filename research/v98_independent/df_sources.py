#!/usr/bin/env python3
"""DF preregistered pair error-correction seven-slot source, Clean-4 training only."""
from __future__ import annotations
import numpy as np

WARMUP=1344
GRID=72
PAIRS=((0,1),(1,3),(0,2))
BUDGETS={
    "RISK_ON":np.array([2.5,.50,.40,.25]),
    "MIXED":np.array([1.9,.55,.45,.35]),
    "RISK_OFF":np.array([.65,.55,.55,.65]),
}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DF_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);hourly=np.zeros_like(c)
    hourly[1:]=np.diff(lc,axis=0)
    native=r*e
    signals=np.zeros((n,4,4))
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        net672=lc[t]-lc[t-672]-native[t-671:t+1].sum(axis=0)
        net168=lc[t]-lc[t-168]-native[t-167:t+1].sum(axis=0)
        downside=np.sqrt(np.sum(np.minimum(hourly[t-335:t+1],0.)**2,axis=0))
        score=np.where((net672>0)&(net168>0),
                       net672/(.03+downside),0.)
        selected=sorted(range(4),key=lambda j:(-float(score[j]),j))
        selected=[j for j in selected if score[j]>0][:2]
        if selected:
            strength=score[selected]
            signals[t,0,selected]=strength/strength.sum()
        # Opportunity: cross-asset confirmed directional range escape.
        candidates=[]
        for j in range(4):
            past_hi=float(h[t-264:t-24,j].max())
            past_lo=float(l[t-264:t-24,j].min())
            old_quote=float(q[t-240:t-24,j].mean())
            new_quote=float(q[t-23:t+1,j].mean())
            drift=float(lc[t,j]-lc[t-24,j])
            if new_quote>1.20*old_quote:
                if c[t,j]>past_hi and drift>0:
                    candidates.append(((c[t,j]-past_hi)/(past_hi-past_lo),j,1.))
                elif c[t,j]<past_lo and drift<0:
                    candidates.append(((past_lo-c[t,j])/(past_hi-past_lo),j,-1.))
        if candidates:
            _,j,direction=max(candidates,key=lambda v:(v[0],-v[1]))
            signals[t,1,j]=direction
        # Relative value: OLS pair residual z-score and confirmed reversion.
        opportunities=[]
        for a,b in PAIRS:
            x=lc[t-672:t-24,b]
            y=lc[t-672:t-24,a]
            variance=float(np.mean((x-x.mean())**2))
            if variance<=1e-10:
                continue
            beta=float(np.mean((x-x.mean())*(y-y.mean()))/variance)
            if not .15<=beta<=3.:
                continue
            residual=y-beta*x
            mean=float(residual.mean())
            sd=float(residual.std())
            if sd<1e-5:
                continue
            z=float((lc[t,a]-beta*lc[t,b]-mean)/sd)
            move=float((lc[t,a]-beta*lc[t,b])-
                       (lc[t-24,a]-beta*lc[t-24,b]))
            if abs(z)>1.5 and z*move<0:
                opportunities.append((abs(z),a,b,beta,np.sign(z)))
        if opportunities:
            _,a,b,beta,direction=max(opportunities,key=lambda v:(v[0],-v[1],-v[2]))
            scale=1./(1.+beta)
            signals[t,2,a]=-direction*scale
            signals[t,2,b]=direction*beta*scale
        # Stress/recovery: realized-volatility-triggered broad downside hedge.
        ret72=lc[t]-lc[t-72]
        ret24=lc[t]-lc[t-24]
        btc_recent=float(np.sqrt(np.mean(hourly[t-23:t+1,0]**2)))
        btc_prior=float(np.sqrt(np.mean(hourly[t-527:t-24,0]**2)))
        if np.count_nonzero(ret72<0)>=3 and btc_recent>1.10*btc_prior:
            signals[t,3,0]=-.5
            signals[t,3,3]=-.5
        elif np.count_nonzero(ret72>0)<=1 and np.count_nonzero(ret24>0)>=3:
            signals[t,3,3]=1.
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if breadth>=3 and net168[0]>0 else
                "RISK_OFF" if breadth<=1 and net168[0]<0 else "MIXED")
        regimes[t]=regime
        budgets[t]=BUDGETS[regime]
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DF_GROSS_SOURCE")
    if not np.isfinite(budgets).all():
        raise ValueError("DF_BUDGET_NONFINITE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
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
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("DF_CAUSAL_PAIR_ERROR_CORRECTION_STATIC_PASS")
