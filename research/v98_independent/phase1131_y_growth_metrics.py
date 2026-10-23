#!/usr/bin/env python3
"""Y growth-first economic metrics; source agnostic and selection-free.

Trade profit factor/payoff use explicit closed-trade realized PnLs, never
hourly marked returns. Caller, not this function, attests data provenance.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

def _trade_metrics(pnls):
    a=np.asarray(pnls,dtype=float)
    if a.ndim!=1 or not np.isfinite(a).all():raise ValueError('Y1131_TRADE_PNL_INVALID')
    if not len(a):return {'trades':0,'profit_factor':None,'payoff':None,'win_rate':None}
    win=a[a>0];loss=-a[a<0]
    return {'trades':int(len(a)),
        'profit_factor':float(win.sum()/loss.sum()) if len(loss) else None,
        'payoff':float(win.mean()/loss.mean()) if len(win) and len(loss) else None,
        'win_rate':float(len(win)/len(a))}

def summarize(index,equity,asset_exposure,closed_trades=(),regimes=None):
    idx=pd.DatetimeIndex(index)
    nav=np.asarray(equity,dtype=float)
    exp=np.asarray(asset_exposure,dtype=float)
    if (idx.tz is None or not idx.is_monotonic_increasing or not idx.is_unique
        or len(idx)<25 or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or nav.shape!=(len(idx),) or exp.shape!=(len(idx),4)
        or not np.isfinite(nav).all() or not np.isfinite(exp).all()
        or np.any(nav<=0)):
        raise ValueError('Y1131_INVALID_CAUSAL_FOLD_SOURCE')
    if regimes is None:states=np.ones(len(idx),dtype=int)
    else:
        states=np.asarray(regimes)
        if states.shape!=(len(idx),) or not np.isin(states,(0,1,2)).all():
            raise ValueError('Y1131_BAD_REGIMES')
    trades=[]
    for item in closed_trades:
        if set(item)!={'timestamp','pnl_usd'}:raise ValueError('Y1131_TRADE_SCHEMA')
        t=pd.Timestamp(item['timestamp']);v=float(item['pnl_usd'])
        if t.tzinfo is None or t<idx[0] or t>idx[-1] or not math.isfinite(v):
            raise ValueError('Y1131_TRADE_TIMESTAMP_OR_PNL')
        trades.append((t,v))
    folds={}
    for year,days,hours in ((2023,365,8760),(2024,366,8784)):
        mask=idx.year==year
        if not mask.any():continue
        ids=np.flatnonzero(mask)
        if len(ids)!=hours or ids[0]<1:
            raise ValueError('Y1131_INCOMPLETE_CHRONOLOGICAL_FOLD')
        baseline=nav[ids[0]-1];x=nav[ids]
        prev=np.r_[baseline,x[:-1]]
        log_hour=np.log(x/prev)
        wealth=float(np.log(x[-1]/baseline))
        peak=np.maximum.accumulate(np.r_[baseline,x])
        maxdd=float(np.min(np.r_[baseline,x]/peak-1))
        daily=x.reshape(days,24)[:,-1]
        daily_log=np.log(daily/np.r_[baseline,daily[:-1]])
        positives=int((daily_log>0).sum())
        worst=np.sort(log_hour)[:max(1,math.ceil(.05*len(log_hour)))]
        notion=np.abs(exp[ids]);asset_total=notion.sum(axis=0)
        share=asset_total/asset_total.sum() if asset_total.sum()>0 else np.zeros(4)
        trades_year=[v for t,v in trades if t.year==year]
        folds[str(year)]={'days':days,'hourly_observations':hours,
            'log_wealth':wealth,'cagr':float(np.expm1(wealth*365.25/days)),
            'max_drawdown':maxdd,'hourly_max_drawdown':maxdd,
            'positive_days':positives,'positive_days_share':positives/days,
            'hourly_cvar_5pct':float(worst.mean()),
            'concentration':{'asset_exposure_shares':share.tolist(),
                             'asset_hhi':float(np.sum(share*share))},
            'regime_hours':{str(i):int(np.sum(states[ids]==i)) for i in range(3)},
            **_trade_metrics(trades_year)}
    if set(folds)!={'2023','2024'}:
        raise ValueError('Y1131_INCOMPLETE_TWO_FOLD_TRAINING')
    return {'folds':folds}
