#!/usr/bin/env python3
"""AB strict economic receipt metrics: pure audit, no data fetch or selection."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

def metrics(nav,fees,funding,exposures,regime):
    if not isinstance(nav,pd.Series) or not isinstance(nav.index,pd.DatetimeIndex):
        raise ValueError('AB1170_NAV_TYPE')
    idx=nav.index;n=len(nav)
    if (idx.tz is None or n<48 or idx[0]<pd.Timestamp('2023-01-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=n,freq='h'))):
        raise ValueError('AB1170_TRAINING_ONLY_CALENDAR')
    v=nav.to_numpy(float);fee=np.asarray(fees,float);fund=np.asarray(funding,float)
    ex=np.asarray(exposures,float);reg=np.asarray(regime,int)
    if (fee.shape!=(n,) or fund.shape!=(n,) or ex.shape!=(n,4) or reg.shape!=(n,)
        or not np.isfinite(v).all() or not np.isfinite(fee).all()
        or not np.isfinite(fund).all() or not np.isfinite(ex).all()
        or (v<=0).any() or (fee<0).any() or not np.isin(reg,(0,1,2)).all()):
        raise ValueError('AB1170_INVALID_RECEIPT')
    hourly=np.diff(np.log(v));h=n-1
    annual=np.expm1(np.log(v[-1]/v[0])*8766./h)
    dd=v/np.maximum.accumulate(v)-1
    daily=nav.resample('D').last().pct_change().dropna().to_numpy(float)
    if not len(daily):raise ValueError('AB1170_NO_COMPLETE_DAYS')
    wins=daily[daily>0];losses=daily[daily<0]
    pf=float(wins.sum()/(-losses.sum())) if len(losses) else None
    payoff=float(wins.mean()/(-losses.mean())) if len(wins) and len(losses) else None
    k=max(1,int(math.ceil(.05*len(daily))))
    reg_growth={str(j):float(hourly[reg[1:]==j].sum()) for j in (0,1,2)}
    ratio=np.abs(ex)/v[:,None]
    return {'hours':int(n),'start':str(idx[0]),'end':str(idx[-1]),
        'initial_equity':float(v[0]),'final_equity':float(v[-1]),
        'log_wealth':float(np.log(v[-1]/v[0])),'cagr':float(annual),
        'max_drawdown':float(dd.min()),'positive_days':int(len(wins)),
        'positive_day_fraction':float(len(wins)/len(daily)),
        'daily_profit_factor':pf,'daily_payoff':payoff,
        'daily_win_rate':float(len(wins)/len(daily)),
        'daily_cvar_5pct':float(np.sort(daily)[:k].mean()),
        'total_fees':float(fee.sum()),'net_funding_cash':float(fund.sum()),
        'max_asset_weight':float(ratio.max()),
        'max_gross_weight':float(ratio.sum(axis=1).max()),
        'max_net_weight':float(np.max(np.abs(ex.sum(axis=1)/v))),
        'regime_log_wealth':reg_growth,
        'regime_hours':{str(j):int((reg[1:]==j).sum()) for j in (0,1,2)},
        'metric_scope':'daily NAV PF/payoff/win; separate FIFO trade metrics required'}
