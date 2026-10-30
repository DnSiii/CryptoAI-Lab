#!/usr/bin/env python3
"""V98 Phase243 accounting semantics: independent, non-alpha metrics contract.

This does not run a trading strategy. It clarifies active-vs-calendar-day
regime denominators and anchors drawdown to initial wealth.
"""
from __future__ import annotations
import math
import pandas as pd


def audit_returns(r: pd.Series) -> dict:
    if not isinstance(r.index,pd.DatetimeIndex) or r.index.tz is None:
        raise ValueError('UTC-aware datetime index required')
    if not (r.index.tz_convert('UTC')==r.index).all() or r.index.has_duplicates or not r.index.is_monotonic_increasing:
        raise ValueError('monotone unique UTC timestamps required')
    if len(r) and (r.index.max()>=pd.Timestamp('2026-01-01',tz='UTC') or r.index.min()<pd.Timestamp('2023-01-01',tz='UTC')):
        raise ValueError('V98 training-only firewall')
    if r.isna().any() or not all(math.isfinite(float(x)) and float(x)>-1 for x in r):
        raise ValueError('nonfinite or bankrupt return')
    if not len(r):
        return {'active_hours':0,'active_days':0,'calendar_days':0,'max_drawdown':0.0,
                'profit_factor':None,'profit_factor_state':'UNDEFINED_EMPTY',
                'payoff':None,'win_rate_all_active_hours':None,
                'positive_days_active':None,'positive_days_calendar_span':None}
    eq=(1+r).cumprod()
    peaks=pd.concat([pd.Series([1.0],index=[r.index[0]-pd.Timedelta(nanoseconds=1)]),eq]).cummax().iloc[1:]
    dd=eq/peaks-1
    positive=float(r[r>0].sum()); negative=float(-r[r<0].sum())
    if negative>0:pf=positive/negative; pfstate='FINITE'
    elif positive>0:pf=None; pfstate='UNDEFINED_NO_LOSSES'
    else:pf=None; pfstate='UNDEFINED_NO_POSITIVE_OR_NEGATIVE'
    wins=r[r>0];losses=-r[r<0]
    payoff=float(wins.mean()/losses.mean()) if len(wins) and len(losses) else None
    active_daily=r.groupby(r.index.floor('D')).sum()
    calendar_daily=r.resample('1D').sum()
    return {'active_hours':len(r),'active_days':len(active_daily),'calendar_days':len(calendar_daily),
            'max_drawdown':float(dd.min()),'profit_factor':pf,'profit_factor_state':pfstate,
            'payoff':payoff,'win_rate_all_active_hours':float((r>0).mean()),
            'positive_days_active':float((active_daily>0).mean()),
            'positive_days_calendar_span':float((calendar_daily>0).mean()),
            'note':'Regime-only active-day positive rate is not interchangeable with full calendar-span positive rate.'}
