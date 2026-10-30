#!/usr/bin/env python3
"""U preregistered 336 completed-bar protective shock source; no PnL."""
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
WINDOW=336

def trailing_shocks(high,low,close):
    frames=(high,low,close)
    if any(not isinstance(f,pd.DataFrame) or tuple(f.columns)!=ASSETS for f in frames):
        raise ValueError('U_SHOCK_CLEAN4')
    idx=close.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or
        len(idx)<WINDOW+2 or idx[0]<pd.Timestamp('2022-12-01T00:00Z') or
        idx[-1]>=pd.Timestamp('2025-01-01T00:00Z') or
        not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or
        any(not idx.equals(f.index) for f in frames)):
        raise ValueError('U_SHOCK_CALENDAR_OR_FUTURE')
    if (any(not np.isfinite(f.to_numpy(float)).all() for f in frames) or
        (low<=0).any().any() or (close<=0).any().any() or
        (high<low).any().any() or (high<close).any().any() or
        (low>close).any().any()):
        raise ValueError('U_SHOCK_INVALID_BAR')
    prev=close.shift(1)
    down=(1-low/prev).clip(lower=0)
    up=(high/prev-1).clip(lower=0)
    d=down.rolling(WINDOW,min_periods=WINDOW).max().round(8)
    u=up.rolling(WINDOW,min_periods=WINDOW).max().round(8)
    if (d.iloc[WINDOW:].isna().any().any() or u.iloc[WINDOW:].isna().any().any() or
        (d.iloc[WINDOW:]>=1).any().any() or (u.iloc[WINDOW:]<0).any().any()):
        raise ValueError('U_SHOCK_INVALID_ROLLING')
    return d,u
