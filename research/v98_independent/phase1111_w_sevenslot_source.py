#!/usr/bin/env python3
"""V98 W seven-slot causal targets. No PnL, no 2025, no external engines."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1110_w_256state_governor import max_feasible_w

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('W_core_only','W_full','W_minus_opportunity','W_minus_relative_value','W_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'W_core_only':('opportunity','relative_value','stress'),
         'W_full':(),'W_minus_opportunity':('opportunity',),
         'W_minus_relative_value':('relative_value',),'W_minus_stress':('stress',)}
REGIME_MULT=np.array([[.5,.5,.8,1.6],[1.,1.,1.,1.],[1.6,1.4,.8,.5]])

def validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in frames):
        raise ValueError('W_CLEAN4_REQUIRED')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1800
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not x.index.equals(idx) for x in frames)):
        raise ValueError('W_TRAINING_CALENDAR_OR_FUTURE')
    if (any(not np.isfinite(x.to_numpy(float)).all() for x in frames)
        or (op<=0).any().any() or (cl<=0).any().any() or (lo<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any()
        or (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('W_INVALID_OHLCV_FUNDING')

def normalize(raw):
    a=np.nan_to_num(np.asarray(raw,float),nan=0.,posinf=0.,neginf=0.)
    gross=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,gross,out=np.zeros_like(a),where=gross>1e-12)

def event_hold(direction,eligible,hold,cooldown):
    direction=np.asarray(direction,float);eligible=np.asarray(eligible,bool)
    if direction.shape!=eligible.shape or direction.ndim!=2:
        raise ValueError('W_EVENT_SHAPE')
    n,k=direction.shape;out=np.zeros((n,k));last=np.zeros(k)
    expiry=np.zeros(k,int);next_allowed=np.zeros(k,int)
    for t in range(n):
        trig=eligible[t]&(t>=next_allowed)&(direction[t]!=0)
        last[trig]=direction[t,trig];expiry[trig]=t+hold
        next_allowed[trig]=t+cooldown
        out[t]=np.where(t<expiry,last,0.)
    return out

def hysteresis(desired,dwell=72):
    out=np.zeros(len(desired),dtype=np.int8)
    state=1;next_switch=0
    for t,x in enumerate(desired):
        if int(x)!=state and t>=next_switch:
            state=int(x);next_switch=t+dwell
        out[t]=state
    return out

def compose_w(op,hi,lo,cl,quote,funding,*,capital_usd=1e6,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx)
    log=np.log(cl);r=log.diff().fillna(0.)
    vol168=r.rolling(168,min_periods=168).std(ddof=0)
    # 1: 96/480 EMA growth, 48h persistence.
    ema96=log.ewm(span=96,adjust=False).mean()
    ema480=log.ewm(span=480,adjust=False).mean()
    persistence=r.apply(np.sign).rolling(48,min_periods=48).mean().abs()
    strength=(ema96-ema480)/np.maximum(vol168*np.sqrt(96),1e-8)
    growth=normalize((strength.clip(-3,3)*(.5+.5*persistence)).to_numpy(float))
    # 2: 12h range expansion, prior 72h quote surprise, 36h hold/120h cooldown.
    range12=hi.rolling(12,min_periods=12).max()/lo.rolling(12,min_periods=12).min()-1
    prior_range=range12.shift(1).rolling(72,min_periods=72).median()
    prior_quote=quote.shift(1).rolling(72,min_periods=72).mean()
    direction=np.sign((log-log.shift(12)).to_numpy(float))
    eligible=((range12>prior_range)&(quote>prior_quote)).fillna(False).to_numpy(bool)
    opportunity=normalize(event_hold(direction,eligible,36,120))
    # 3: 48h return dispersion mean reversion, prior 336h volatility parity rank.
    vol336=r.shift(1).rolling(336,min_periods=336).std(ddof=0)
    standardized=(log-log.shift(48))/np.maximum(vol336*np.sqrt(48),1e-8)
    score=standardized.to_numpy(float)
    rv=np.zeros((n,4));pair=np.zeros(4);expiry=0
    for t in range(n):
        if t>=expiry:
            pair=np.zeros(4)
            if np.isfinite(score[t]).all() and np.ptp(score[t])>1e-12:
                winner=int(np.argmax(score[t]));loser=int(np.argmin(score[t]))
                pair[winner]=-.5;pair[loser]=.5;expiry=t+72
        rv[t]=pair
    relative_value=rv
    # 4: market drawdown breakout or 72h rebound; asset downside-convex inventory.
    market=r.mean(axis=1);market_index=np.exp(market.cumsum())
    drawdown=market_index/market_index.rolling(168,min_periods=168).max()-1
    drawdown_break=drawdown<drawdown.shift(1).rolling(168,min_periods=168).min()
    rebound=(market.rolling(72,min_periods=72).sum()>0)&(drawdown<0)
    breadth=((log-log.shift(24))>0).sum(axis=1)
    downside=np.sqrt(r.clip(upper=0).pow(2).rolling(168,min_periods=168).mean()).to_numpy(float)
    stress_raw=np.where((drawdown_break&(breadth<=1)).to_numpy()[:,None],-downside,
        np.where((rebound&(breadth>=3)).to_numpy()[:,None],
                 1./np.maximum(downside,1e-8),0.))
    stress=normalize(stress_raw)
    # 5: prior 720h vol rank 33/67 percentile + breadth; 72h dwell.
    mv168=market.rolling(168,min_periods=168).std(ddof=0)
    prior=mv168.shift(1).rolling(720,min_periods=720)
    q33=prior.quantile(1./3.);q67=prior.quantile(2./3.)
    regime_raw=np.where((mv168>q67)&(breadth<=1),0,
                        np.where((mv168<q33)&(breadth>=3),2,1))
    regime=hysteresis(regime_raw,72)
    # 6/7: conviction allocator then exact W 256-state executable governor.
    prev=cl.shift(1)
    down=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max()
    up=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max()
    max_funding=funding.abs().rolling(720,min_periods=720).max()
    sleeves={'growth':growth,'opportunity':opportunity,
             'relative_value':relative_value,'stress':stress}
    outputs={};governor_calls=0
    for name in PATHS:
        targets=np.zeros((n,4));last=np.zeros(4)
        for t in range(n):
            if t%12==0:
                if (not np.isfinite(down.iloc[t]).all()
                    or not np.isfinite(up.iloc[t]).all()
                    or not np.isfinite(max_funding.iloc[t]).all()):
                    last=np.zeros(4)
                else:
                    weights=[];vectors=[]
                    for j,sleeve in enumerate(SLEEVES):
                        vec=sleeves[sleeve][t]
                        conviction=min(1.,float(np.abs(vec).sum()))
                        if sleeve in EXCLUDE[name]:conviction=0.
                        weights.append(conviction*REGIME_MULT[regime[t],j])
                        vectors.append(vec)
                    total=sum(weights)
                    raw=sum(weights[j]*vectors[j] for j in range(4))/total if total else np.zeros(4)
                    last=max_feasible_w(raw,cl.iloc[t].to_numpy(float),
                        down.iloc[t].to_numpy(float),up.iloc[t].to_numpy(float),
                        max_funding.iloc[t].to_numpy(float),
                        quote.iloc[t].to_numpy(float),capital_usd)
                    governor_calls+=1
            targets[t]=last
        outputs[name]=pd.DataFrame(targets,index=idx,columns=ASSETS)
    if diagnostics:
        return outputs,{'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'sleeve_active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
            'governor_calls':governor_calls,'target_execution':'t+1_open_only',
            'historical_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'holdout_accessed':False}
    return outputs
