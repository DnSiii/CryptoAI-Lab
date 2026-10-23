#!/usr/bin/env python3
"""Y complete seven-slot signed causal portfolio targets; no historical PnL."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1124_y_pretrade_growth import maximize
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('Y_core_only','Y_full','Y_minus_opportunity','Y_minus_relative_value','Y_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'Y_core_only':('opportunity','relative_value','stress'),
         'Y_full':(),'Y_minus_opportunity':('opportunity',),
         'Y_minus_relative_value':('relative_value',),'Y_minus_stress':('stress',)}
REGIME_MULT=np.array([[.6,.5,.7,1.5],[1.,1.,1.,1.],[1.5,1.4,1.,.6]])

def validate(op,hi,lo,cl,quote,funding):
    fs=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in fs):
        raise ValueError('Y_CLEAN4_ONLY')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1800
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not x.index.equals(idx) for x in fs)):
        raise ValueError('Y_TRAINING_CALENDAR_OR_FUTURE')
    if (any(not np.isfinite(x.to_numpy(float)).all() for x in fs)
        or (op<=0).any().any() or (cl<=0).any().any() or (lo<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any()
        or (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('Y_INVALID_SOURCE')

def normalize(x):
    a=np.nan_to_num(np.asarray(x,float),nan=0.,posinf=0.,neginf=0.)
    g=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,g,out=np.zeros_like(a),where=g>1e-12)

def hold(direction,eligible,hold_hours=24,cooldown=96):
    direction=np.asarray(direction,float);eligible=np.asarray(eligible,bool)
    if direction.shape!=eligible.shape or direction.ndim!=2:
        raise ValueError('Y_EVENT_SHAPE')
    n,k=direction.shape;out=np.zeros((n,k));expiry=np.zeros(k,int)
    next_allowed=np.zeros(k,int);last=np.zeros(k)
    for t in range(n):
        trig=eligible[t]&(t>=next_allowed)&(direction[t]!=0)
        last[trig]=direction[t,trig];expiry[trig]=t+hold_hours
        next_allowed[trig]=t+cooldown
        out[t]=np.where(t<expiry,last,0.)
    return out

def hysteresis(raw,dwell=48):
    out=np.ones(len(raw),np.int8);state=1;next_switch=0
    for t,x in enumerate(raw):
        if int(x)!=state and t>=next_switch:
            state=int(x);next_switch=t+dwell
        out[t]=state
    return out

def beta_neutral_pair(beta_winner,beta_loser):
    """Return short/long weights only when signed beta can cancel exactly."""
    if (not np.isfinite(beta_winner) or not np.isfinite(beta_loser)
        or beta_winner*beta_loser<=1e-12):
        return None
    a=abs(beta_winner);b=abs(beta_loser)
    return -b/(a+b),a/(a+b)

def compose_y(op,hi,lo,cl,quote,funding,*,capital_usd=1e6,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx);log=np.log(cl);r=log.diff().fillna(0.)
    downside=np.sqrt(r.clip(upper=0).pow(2).rolling(336,min_periods=336).mean())
    # 1 Growth: 72/288h signed trend coherence, downside vol and breadth.
    ret72=log-log.shift(72);ret288=log-log.shift(288)
    breadth=((log-log.shift(72))>0).sum(axis=1)
    agree=np.sign(ret72)==np.sign(ret288)
    strength=np.where(agree,np.sign(ret72)*np.sqrt(np.abs(ret72*ret288))
                      /np.maximum(downside,1e-8),0.)
    breadth_mult=(.5+.5*np.abs(breadth.to_numpy(float)-2)/2)[:,None]
    growth=normalize(strength*breadth_mult)
    # 2 Opportunity: 8h variance breakout and prior 48h quote flow.
    var8=r.rolling(8,min_periods=8).var(ddof=0)
    basevar=var8.shift(1).rolling(336,min_periods=336).quantile(.75)
    quote48=quote.rolling(48,min_periods=48).sum()
    basequote=quote48.shift(1).rolling(336,min_periods=336).median()
    direction=np.sign((log-log.shift(8)).to_numpy(float))
    eligible=((var8>basevar)&(quote48>basequote)).fillna(False).to_numpy(bool)
    opportunity=normalize(hold(direction,eligible,24,96))
    # 3 RV: prior 240h covariance-neutral dispersion pair, 48h hold.
    prior_vol=r.shift(1).rolling(240,min_periods=240).std(ddof=0)
    scores=((log-log.shift(48))/np.maximum(prior_vol*np.sqrt(48),1e-8)).to_numpy(float)
    btc=r['BTCUSDT'].shift(1)
    beta=r.shift(1).rolling(240,min_periods=240).cov(btc).div(
        btc.rolling(240,min_periods=240).var(ddof=0).clip(lower=1e-12),axis=0).to_numpy(float)
    rv=np.zeros((n,4));pair=np.zeros(4);expiry=0
    for t in range(n):
        if t>=expiry:
            pair=np.zeros(4)
            if np.isfinite(scores[t]).all() and np.isfinite(beta[t]).all() and np.ptp(scores[t])>1e-12:
                winner=int(np.argmax(scores[t]));loser=int(np.argmin(scores[t]))
                # Opposite signed betas cannot be neutralized by a long/short pair.
                neutral=beta_neutral_pair(beta[t,winner],beta[t,loser])
                if neutral is not None:
                    pair[winner],pair[loser]=neutral;expiry=t+48
        rv[t]=pair
    relative_value=normalize(rv)
    # 4 Stress: 48h downside skew and 24h rebound.
    skew48=r.rolling(48,min_periods=48).skew().mean(axis=1)
    breadth24=((log-log.shift(24))>0).sum(axis=1)
    market24=r.mean(axis=1).rolling(24,min_periods=24).sum()
    crash=(skew48<0)&(breadth24<=1)
    rebound=(market24>0)&(breadth24>=3)
    positive=((log-log.shift(24))>0).to_numpy(bool)
    stress_raw=np.where(crash.to_numpy()[:,None],-downside.to_numpy(float),
        np.where(rebound.to_numpy()[:,None]&positive,
                 1./np.maximum(downside.to_numpy(float),1e-8),0.))
    stress=normalize(stress_raw)
    # 5 Regime: prior 336h market drawdown and 144h trend breadth.
    market=r.mean(axis=1);index=np.exp(market.cumsum())
    dd=index/index.rolling(336,min_periods=336).max()-1
    dd_base=dd.shift(1).rolling(336,min_periods=336).median()
    breadth144=((log-log.shift(144))>0).sum(axis=1)
    regime_raw=np.where((dd<dd_base)&(breadth144<=1),0,
                        np.where((dd>dd_base)&(breadth144>=3),2,1))
    regime=hysteresis(regime_raw,48)
    # 6/7: 12h signed conviction and 81-state Y pretrade growth gate.
    prev=cl.shift(1)
    down=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max()
    up=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max()
    funding_max=funding.abs().rolling(720,min_periods=720).max()
    sleeves={'growth':growth,'opportunity':opportunity,
             'relative_value':relative_value,'stress':stress}
    paths={};calls=0
    for name in PATHS:
        out=np.zeros((n,4));last=np.zeros(4)
        for t in range(n):
            if t%12==0:
                if (not np.isfinite(down.iloc[t]).all()
                    or not np.isfinite(up.iloc[t]).all()
                    or not np.isfinite(funding_max.iloc[t]).all()):
                    last=np.zeros(4)
                else:
                    scores=[];signals=[]
                    for j,key in enumerate(SLEEVES):
                        sig=sleeves[key][t]
                        conviction=min(1.,float(np.abs(sig).sum()))
                        friction=.004*float(np.abs(sig-last).sum())
                        score=max(0.,conviction-friction) if key not in EXCLUDE[name] else 0.
                        scores.append(score*REGIME_MULT[regime[t],j]);signals.append(sig)
                    total=sum(scores)
                    raw=sum(scores[j]*signals[j] for j in range(4))/total if total else np.zeros(4)
                    last=maximize(raw,cl.iloc[t].to_numpy(float),
                        down.iloc[t].to_numpy(float),up.iloc[t].to_numpy(float),
                        funding_max.iloc[t].to_numpy(float),
                        quote.iloc[t].to_numpy(float),capital_usd)
                    calls+=1
            out[t]=last
        paths[name]=pd.DataFrame(out,index=idx,columns=ASSETS)
    if diagnostics:
        return paths,{'sleeve_active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum())
                        for k,v in sleeves.items()},
            'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'governor_calls':calls,'target_execution':'t+1_open_only',
            'historical_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'holdout_accessed':False}
    return paths
