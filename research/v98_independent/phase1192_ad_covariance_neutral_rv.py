#!/usr/bin/env python3
"""V98 AD causal covariance-neutral one-hour dispersion sleeve, source-only."""
from __future__ import annotations
import numpy as np
from phase1189_ad_online_core_router import validate_source

WARMUP=336
COV_WINDOW=168
SHRINK=.30
RIDGE=1e-8
SHOCK_MULTIPLIER=2.
SHOCK_FLOOR=1e-8
HOLD_HOURS=8
COOLDOWN_HOURS=24


def projected_trade(innovation, covariance):
    s=np.asarray(innovation,dtype=float)
    cov=np.asarray(covariance,dtype=float)
    if s.shape!=(4,) or cov.shape!=(4,4) or not np.isfinite(s).all() or not np.isfinite(cov).all():
        raise ValueError('AD1192_PROJECTION_INPUT')
    if not np.allclose(cov,cov.T,atol=1e-12,rtol=0) or np.linalg.eigvalsh(cov).min()<=0:
        raise ValueError('AD1192_COVARIANCE_PSD')
    beta=cov[:,0]/cov[0,0]
    a=np.column_stack((np.ones(4),beta))
    x=np.linalg.solve(cov,s)
    y=np.linalg.solve(cov,a)
    gram=a.T@y
    w=x-y@(np.linalg.pinv(gram,rcond=1e-10)@(a.T@x))
    gross=float(np.abs(w).sum())
    if not np.isfinite(gross) or gross<1e-12:
        return np.zeros(4)
    w/=gross
    if abs(w.sum())>1e-7 or abs(beta@w)>1e-7:
        raise ValueError('AD1192_NEUTRALITY_FAILURE')
    return w


def relative_value_intents(op,hi,lo,cl,quote,funding,event,diagnostics=False):
    idx,(_,_,_,close,_,_,_)=validate_source(op,hi,lo,cl,quote,funding,event)
    n=len(idx)
    logp=np.log(close)
    returns=np.zeros_like(close)
    returns[1:]=logp[1:]-logp[:-1]
    demean=returns-returns.mean(axis=1,keepdims=True)
    dispersion=np.mean(demean**2,axis=1)
    intents=np.zeros((n,4),dtype=float)
    expiry=0
    next_allowed=0
    current=np.zeros(4)
    triggers=0
    for t in range(WARMUP,n):
        if t>=next_allowed:
            prior=returns[t-COV_WINDOW:t]
            median=max(float(np.median(dispersion[t-COV_WINDOW:t])),SHOCK_FLOOR)
            if dispersion[t]>SHOCK_MULTIPLIER*median:
                sample=np.cov(prior.T,ddof=0)
                cov=(1-SHRINK)*sample+SHRINK*np.diag(np.diag(sample))+np.eye(4)*RIDGE
                proposed=projected_trade(-demean[t],cov)
                if np.any(proposed):
                    current=proposed
                    expiry=t+HOLD_HOURS
                    next_allowed=t+COOLDOWN_HOURS
                    triggers+=1
        intents[t]=current if t<expiry else 0.
    if diagnostics:
        return intents,{'phase':1192,'source_only':True,
            'historical_system_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'earliest_fill':'t+1 open',
            'triggers':triggers,'active_hours':int(np.any(intents!=0,axis=1).sum()),
            'max_gross_intent':float(np.abs(intents).sum(axis=1).max())}
    return intents
