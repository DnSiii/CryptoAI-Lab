#!/usr/bin/env python3
"""Independent Z wealth-first fold and realized-trade metrics. No source access."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

def fold_stats(start,nav,expo,closed,*,year,strict):
    nav=np.asarray(nav,float);expo=np.asarray(expo,float)
    if nav.ndim!=1 or len(nav)<2 or expo.shape!=(len(nav)-1,4):
        raise ValueError('Z1150_FOLD_GEOMETRY')
    if (not np.isfinite(nav).all() or (nav<=0).any()
        or not np.isfinite(expo).all()):raise ValueError('Z1150_INVALID_NAV')
    hours=len(nav)-1;days=366 if year==2024 else 365
    if strict and hours!=days*24:raise ValueError('Z1150_INCOMPLETE_FOLD')
    logret=np.diff(np.log(nav))
    logwealth=float(logret.sum())
    cagr=float(np.exp(logwealth*365*24/hours)-1)
    dd=nav/np.maximum.accumulate(nav)-1
    k=max(1,int(math.ceil(.05*hours)))
    cvar=float(np.partition(logret,k-1)[:k].mean())
    ends=nav[24::24]
    prev=np.r_[nav[0],ends[:-1]]
    pos=int(np.sum(ends>prev))
    gross=np.abs(expo)
    shares=gross.sum(axis=0)
    shares=shares/max(shares.sum(),1e-12)
    hhi=float(np.sum(shares**2)) if gross.sum()>0 else 0.
    wins=np.array([float(t['pnl_usd']) for t in closed if t['pnl_usd']>0])
    losses=np.array([float(t['pnl_usd']) for t in closed if t['pnl_usd']<0])
    return {'year':year,'days':days if strict else hours//24,
        'hourly_observations':hours,'start_usd':float(nav[0]),
        'terminal_usd':float(nav[-1]),'log_wealth':logwealth,'cagr':cagr,
        'max_drawdown':float(dd.min()),'hourly_cvar_5pct':cvar,
        'positive_days':pos,'positive_days_share':float(pos/max(len(ends),1)),
        'closed_trades':len(wins)+len(losses),'profit_factor':float(wins.sum()/-losses.sum()) if len(losses) else None,
        'payoff':float(wins.mean()/-losses.mean()) if len(wins) and len(losses) else None,
        'win_rate':float(len(wins)/max(len(wins)+len(losses),1)),
        'concentration':{'asset_hhi':hhi,'asset_exposure_shares':shares.tolist()}}

def summarize(timestamps,equity,exposure,closed,regime,*,strict=True):
    idx=pd.DatetimeIndex(timestamps)
    nav=np.asarray(equity,float);expo=np.asarray(exposure,float)
    state=np.asarray(regime,int)
    if (idx.tz is None or len(idx)!=len(nav) or expo.shape!=(len(idx),4)
        or state.shape!=(len(idx),) or not np.isin(state,(0,1,2)).all()
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or not np.isfinite(nav).all() or (nav<=0).any()
        or not np.isfinite(expo).all()):raise ValueError('Z1150_GEOMETRY_OR_NONCAUSAL')
    if strict and (idx[0]!=pd.Timestamp('2022-12-31T23:00Z')
        or idx[-1]!=pd.Timestamp('2024-12-31T23:00Z')
        or len(idx)!=17545):raise ValueError('Z1150_TRAINING_FOLDS_ONLY')
    folds={};regimes={str(k):0. for k in range(3)}
    logret=np.diff(np.log(nav))
    for k in range(3):regimes[str(k)]=float(logret[state[1:]==k].sum())
    for year in (2023,2024):
        where=np.flatnonzero(idx.year==year)
        if not len(where):continue
        first=where[0];last=where[-1]
        if first==0:raise ValueError('Z1150_NO_PRE_FOLD_BASELINE')
        trade_year=[t for t in closed if pd.Timestamp(t['timestamp']).year==year]
        folds[str(year)]=fold_stats(idx[first-1],nav[first-1:last+1],
            expo[first:last+1],trade_year,year=year,strict=strict)
    if strict and set(folds)!={'2023','2024'}:raise ValueError('Z1150_MISSING_FOLD')
    if not np.isclose(sum(x['log_wealth'] for x in folds.values()),
        float(logret.sum()),atol=1e-8,rtol=0):
        raise ValueError('Z1150_FOLD_WEALTH_DRIFT')
    if not np.isclose(sum(regimes.values()),float(logret.sum()),atol=1e-8,rtol=0):
        raise ValueError('Z1150_REGIME_WEALTH_DRIFT')
    return {'folds':folds,'total_log_wealth':float(logret.sum()),
        'total_wealth_multiple':float(nav[-1]/nav[0]),
        'all_hourly_max_drawdown':float((nav/np.maximum.accumulate(nav)-1).min()),
        'regime_log_wealth':regimes,
        'regime_hours':{str(k):int(np.sum(state[1:]==k)) for k in range(3)},
        'historical_pnl_computed':False if not strict else True}
