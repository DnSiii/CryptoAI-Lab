#!/usr/bin/env python3
"""V98-only hourly-vs-daily close drawdown measurement; synthetic until source gate."""
from __future__ import annotations
import numpy as np

def drawdown(nav, initial):
    v=np.asarray(nav,dtype=float)
    if v.ndim!=1 or len(v)==0 or not np.isfinite(v).all() or (v<=0).any() or not np.isfinite(initial) or initial<=0:
        raise ValueError('complete positive finite chronological NAV and initial capital required')
    peak=np.maximum.accumulate(np.r_[float(initial),v])
    return float(np.min(v/peak[1:]-1.))

def compare_hourly_daily(hourly_nav, initial, hour_of_day):
    h=np.asarray(hourly_nav,dtype=float);clock=np.asarray(hour_of_day)
    if h.ndim!=1 or clock.shape!=h.shape or len(h)==0 or not np.issubdtype(clock.dtype,np.integer) or np.any((clock<0)|(clock>23)):
        raise ValueError('hourly NAV and UTC clock must align')
    # A full sample must end at a UTC day boundary; no silently dropped tail.
    if clock[0]!=0 or clock[-1]!=23 or np.any(clock!=np.arange(len(h))%24):
        raise ValueError('only complete consecutive UTC days supported')
    hourly=drawdown(h,initial)
    daily=drawdown(h[23::24],initial)
    if hourly>daily+1e-12:raise AssertionError('hourly drawdown cannot understate daily drawdown')
    return {'hourly_close_max_drawdown':hourly,'daily_close_max_drawdown':daily,
            'additional_hourly_drawdown':daily-hourly,'days':int(len(h)//24),
            'source':'synthetic_or_authenticated_hourly_NAV_required'}
