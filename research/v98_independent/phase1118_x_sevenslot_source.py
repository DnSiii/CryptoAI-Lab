#!/usr/bin/env python3
"""X distinct complete seven-slot signed causal portfolio targets, no PnL."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1117_x_contingent_governor import maximize
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('X_core_only','X_full','X_minus_opportunity','X_minus_relative_value','X_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'X_core_only':('opportunity','relative_value','stress'),
         'X_full':(),'X_minus_opportunity':('opportunity',),
         'X_minus_relative_value':('relative_value',),'X_minus_stress':('stress',)}
REGIME_MULT=np.array([[.7,.5,.7,1.5],[1.,1.,1.,1.],[1.4,1.5,1.,.5]])

def validate(op,hi,lo,cl,quote,funding):
    fs=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(f,pd.DataFrame) or tuple(f.columns)!=ASSETS for f in fs):
        raise ValueError('X_CLEAN4_REQUIRED')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1800
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not f.index.equals(idx) for f in fs)):
        raise ValueError('X_TRAINING_CALENDAR_OR_FUTURE')
    if (any(not np.isfinite(f.to_numpy(float)).all() for f in fs)
        or (op<=0).any().any() or (cl<=0).any().any() or (lo<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any()
        or (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('X_INVALID_SOURCE')

def normalize(a):
    x=np.nan_to_num(np.asarray(a,float),nan=0.,posinf=0.,neginf=0.)
    g=np.abs(x).sum(axis=1,keepdims=True)
    return np.divide(x,g,out=np.zeros_like(x),where=g>1e-12)

def event_hold(d,e,hold=18,cooldown=72):
    d=np.asarray(d,float);e=np.asarray(e,bool)
    if d.shape!=e.shape or d.ndim!=2:raise ValueError('X_EVENT_SHAPE')
    n,k=d.shape;out=np.zeros_like(d);expiry=np.zeros(k,int)
    next_allowed=np.zeros(k,int);last=np.zeros(k)
    for t in range(n):
        trig=e[t]&(t>=next_allowed)&(d[t]!=0)
        last[trig]=d[t,trig];expiry[trig]=t+hold
        next_allowed[trig]=t+cooldown
        out[t]=np.where(t<expiry,last,0.)
    return out

def dwell_router(raw,dwell=48):
    state=1;next_switch=0;out=np.ones(len(raw),np.int8)
    for t,v in enumerate(raw):
        if int(v)!=state and t>=next_switch:
            state=int(v);next_switch=t+dwell
        out[t]=state
    return out

def compose_x(op,hi,lo,cl,quote,funding,*,capital_usd=1e6,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx);log=np.log(cl);r=log.diff().fillna(0.)
    downsemi=np.sqrt(r.clip(upper=0).pow(2).rolling(336,min_periods=336).mean())
    # 1 Growth: signed 24/144h return agreement and 96h leadership rank.
    ret24=log-log.shift(24);ret144=log-log.shift(144)
    strength96=(log-log.shift(96))/np.maximum(
        r.shift(1).rolling(336,min_periods=336).std(ddof=0)*np.sqrt(96),1e-8)
    leader=strength96.abs().rank(axis=1,pct=True)
    agree=np.sign(ret24)==np.sign(ret144)
    growth_raw=np.where(agree,np.sign(ret24)*np.sqrt(np.abs(ret24*ret144))
                        *leader/np.maximum(downsemi,1e-8),0.)
    growth=normalize(growth_raw)
    # 2 Opportunity: prior 48h breakout, prior 336h volume surge, 18h/72h.
    prior_high=hi.shift(1).rolling(48,min_periods=48).max()
    prior_low=lo.shift(1).rolling(48,min_periods=48).min()
    vol24=quote.rolling(24,min_periods=24).sum()
    prior_vol=vol24.shift(1).rolling(336,min_periods=336).median()
    direction=np.where(cl>prior_high,1.,np.where(cl<prior_low,-1.,0.))
    eligible=((vol24>prior_vol)&(direction!=0)).to_numpy(bool)
    opportunity=normalize(event_hold(direction,eligible,18,72))
    # 3 RV: 168h prior BTC beta, 24h residual reversion, 48h dollar-neutral pair.
    btc=r['BTCUSDT'];alts=r[list(ASSETS[1:])]
    btc_prior=btc.shift(1)
    beta=alts.shift(1).rolling(168,min_periods=168).cov(btc_prior).div(
        btc_prior.rolling(168,min_periods=168).var(ddof=0).clip(lower=1e-12),axis=0)
    residual=alts.sub(beta.mul(btc,axis=0),axis=0)
    score=(residual.rolling(24,min_periods=24).sum()/np.maximum(
        residual.shift(1).rolling(336,min_periods=336).std(ddof=0)*np.sqrt(24),1e-8)).to_numpy(float)
    rv=np.zeros((n,4));pair=np.zeros(4);expiry=0
    for t in range(n):
        if t>=expiry:
            pair=np.zeros(4)
            if np.isfinite(score[t]).all() and np.ptp(score[t])>1e-12:
                hi_asset=int(np.argmax(score[t]))+1;lo_asset=int(np.argmin(score[t]))+1
                pair[hi_asset]=-.5;pair[lo_asset]=.5;expiry=t+48
        rv[t]=pair
    relative_value=rv
    # 4 Stress/recovery: 72h downside skew and signed breadth.
    skew72=r.rolling(72,min_periods=72).skew().mean(axis=1)
    breadth=((log-log.shift(24))>0).sum(axis=1)
    market72=r.mean(axis=1).rolling(72,min_periods=72).sum()
    crash=(skew72<0)&(breadth<=1)
    rebound=(market72>0)&(breadth>=3)
    downside=downsemi.to_numpy(float)
    positive=((log-log.shift(24))>0).to_numpy(bool)
    stress_raw=np.where(crash.to_numpy()[:,None],-downside,
                np.where(rebound.to_numpy()[:,None]&positive,
                         1./np.maximum(downside,1e-8),0.))
    stress=normalize(stress_raw)
    # 5 Regime: 96h BTC cross-correlation and 336h breadth persistence.
    corr=alts.rolling(96,min_periods=96).corr(btc).mean(axis=1)
    corr_prior=corr.shift(1).rolling(336,min_periods=336).median()
    breadth_persistence=breadth.rolling(336,min_periods=336).mean()/4.
    raw_regime=np.where((corr>corr_prior)&(breadth_persistence<.5),0,
                  np.where((corr<corr_prior)&(breadth_persistence>.5),2,1))
    regime=dwell_router(raw_regime,48)
    # 6/7: signed conviction and X contingent 256-state max-growth governor.
    prev=cl.shift(1)
    down=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max()
    up=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max()
    funding_max=funding.abs().rolling(720,min_periods=720).max()
    sleeves={'growth':growth,'opportunity':opportunity,
             'relative_value':relative_value,'stress':stress}
    outputs={};calls=0
    for path in PATHS:
        out=np.zeros((n,4));last=np.zeros(4)
        for t in range(n):
            if t%12==0:
                if (not np.isfinite(down.iloc[t]).all()
                    or not np.isfinite(up.iloc[t]).all()
                    or not np.isfinite(funding_max.iloc[t]).all()):
                    last=np.zeros(4)
                else:
                    weights=[];signals=[]
                    for j,key in enumerate(SLEEVES):
                        vec=sleeves[key][t]
                        conviction=min(1.,float(np.abs(vec).sum()))
                        cost=.004*float(np.abs(vec-last).sum())
                        score=max(0.,conviction-cost) if key not in EXCLUDE[path] else 0.
                        weights.append(score*REGIME_MULT[regime[t],j])
                        signals.append(vec)
                    total=sum(weights)
                    raw=sum(weights[j]*signals[j] for j in range(4))/total if total else np.zeros(4)
                    last=maximize(raw,cl.iloc[t].to_numpy(float),
                        down.iloc[t].to_numpy(float),up.iloc[t].to_numpy(float),
                        funding_max.iloc[t].to_numpy(float),
                        quote.iloc[t].to_numpy(float),capital_usd)
                    calls+=1
            out[t]=last
        outputs[path]=pd.DataFrame(out,index=idx,columns=ASSETS)
    if diagnostics:
        return outputs,{'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum())
                         for k,v in sleeves.items()},
                        'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
                        'governor_calls':calls,'target_execution':'t+1_open_only',
                        'historical_pnl_computed':False,'validation_2025_read':False,
                        'holdout_accessed':False,'external_benchmarks_used':False}
    return outputs
