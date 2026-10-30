#!/usr/bin/env python3
"""V98 AR independent covariance-aware seven-slot source bundle. No 2025 or benchmarks."""
from __future__ import annotations
import numpy as np

WARMUP=2160
def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=np.float64) for x in
                 (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or
        any(x.shape!=c.shape for x in (h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (c,h,l,r,e,q)) or
        np.any(c<=0) or np.any(l<=0) or np.any(l>c) or
        np.any(h<c) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AR_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    lr=np.diff(logc,axis=0,prepend=logc[:1])
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"SIDEWAYS",dtype="<U9")
    opp_until=-1
    opp_asset=-1
    crisis_until=-1
    recovery_until=-1
    last_crisis=-1000000
    recovery_used=True
    for t in range(WARMUP,n):
        r24=logc[t]-logc[t-24]
        r168=logc[t]-logc[t-168]
        r720=logc[t]-logc[t-720]
        r2160=logc[t]-logc[t-2160]
        hist=lr[t-719:t+1]
        cov=np.cov(hist,rowvar=False)
        diag=np.diag(np.diag(cov))
        ridge=max(float(np.trace(cov)/4.)*.1,1e-8)
        sigma=.5*cov+.5*diag+ridge*np.eye(4)
        funding_per_hour=np.mean(r[t-719:t+1]*e[t-719:t+1],axis=0)
        mu=.5*(r720/720.)+.5*(r2160/2160.)-funding_per_hour
        kelly=np.linalg.solve(sigma,mu)
        positive=np.maximum(kelly,0.)
        if positive.sum()>1e-12:
            growth[t]=positive/positive.sum()

        # Distinct high-volume 24h event: fixed holding clock, no re-opening.
        if t>=opp_until:
            opp_asset=-1
            vol24=np.sqrt(np.mean(lr[t-23:t+1]**2,axis=0))
            prior_median=np.median(q[t-168:t],axis=0)
            eligible=(r24>2.*vol24*np.sqrt(24.))&(r168>0)&(
                q[t]>1.5*np.maximum(prior_median,1.))
            if np.any(eligible):
                score=r24/np.maximum(vol24*np.sqrt(24.),1e-10)
                rank=np.lexsort((np.arange(4),-score))
                opp_asset=int(next(j for j in rank if eligible[j]))
                opp_until=t+168
        if t<opp_until and opp_asset>=0:
            opportunity[t,opp_asset]=1.

        # Beta-adjusted cross-sectional residual relative value.
        base=hist[:,0]
        var=float(np.var(base))
        beta=np.array([np.mean((hist[:,j]-hist[:,j].mean())*
                        (base-base.mean()))/max(var,1e-10)
                        for j in (1,2,3)])
        resid=r168[1:]-beta*r168[0]
        worst=int(np.argmin(resid))+1
        best=int(np.argmax(resid))+1
        if worst!=best and float(np.max(resid)-np.min(resid))>.05:
            relative[t,worst]=.5
            relative[t,best]=-.5

        m168=float(np.median(r168))
        m24=float(np.median(r24))
        m720=float(np.median(r720))
        panic=(m168<-.12 and m24<-.05)
        if panic and t>=last_crisis+336 and t>=crisis_until:
            crisis_until=t+72
            last_crisis=t
            recovery_until=-1
            recovery_used=False
        elif (not recovery_used and t>=crisis_until and
              t-last_crisis<=336 and m24>.04):
            recovery_until=t+72
            recovery_used=True
        if t<crisis_until:
            stress[t,0]=-1.
        elif t<recovery_until:
            stress[t]=.25

        if panic:
            states[t]="PANIC"
        elif m720<0:
            states[t]="DRAWDOWN"
        elif float(np.median(r2160))>0 and np.count_nonzero(r168>0)>=3:
            states[t]="RISK_ON"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2600,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    a=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-36:]*=1.2
    b=source_bundle(changed,np.maximum(h,changed),
                    np.minimum(l,changed),r,e,q)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-36],y[:-36])
        assert np.isfinite(x).all()
        assert np.all(np.abs(x).sum(axis=1)<=1.+1e-12)
    assert np.array_equal(a[4]["state"][:-36],b[4]["state"][:-36])
    assert np.allclose(a[0][:WARMUP],0.)
    return True

if __name__=="__main__":
    assert causal_check()
    print("AR_COVARIANCE_SOURCE_CAUSAL_PASS")
