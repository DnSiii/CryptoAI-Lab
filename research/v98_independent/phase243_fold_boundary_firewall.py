#!/usr/bin/env python3
"""V98 Independent Phase243: synthetic-only fold boundary / holdout firewall.

NO ALPHA: no real strategy prices or positions are loaded here. Two FIXED,
non-selectable sensitivity conventions protect the 2025-12-31/2026-01-01
boundary. Primary liquidates at the last in-fold open; secondary liquidates
at the last in-fold close. No next-year opening price may be used. No funding
settlement assumptions are inferred; real execution needs a separate native
funding cash ledger. This is not a replacement for frozen strategy evaluators.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT')
FOLDS = ((2023, '2023-01-01', '2024-01-01'),
         (2024, '2024-01-01', '2025-01-01'),
         (2025, '2025-01-01', '2026-01-01'))
COSTS = {'base': 0.0007, 'severe': 0.0014, 'supersevere': 0.0028}
CUTOFF = pd.Timestamp('2026-01-01T00:00:00Z')


def validate_fold(index, opens, closes, target, start, stop):
    """Strict hourly, five-asset, in-fold only, no 2026+ observations."""
    start, stop = pd.Timestamp(start), pd.Timestamp(stop)
    if start.tzinfo is None or stop.tzinfo is None:
        raise ValueError('timezone required')
    start, stop = start.tz_convert('UTC'), stop.tz_convert('UTC')
    if (start, stop) not in {(pd.Timestamp(a, tz='UTC'),pd.Timestamp(b,tz='UTC')) for _,a,b in FOLDS}:
        raise ValueError('only frozen 2023/2024/2025 chronological folds')
    if stop > CUTOFF:
        raise ValueError('holdout forbidden')
    if not isinstance(index, pd.DatetimeIndex) or str(index.tz) != 'UTC':
        raise ValueError('explicit UTC index required')
    if (len(index) != int((stop-start)/pd.Timedelta(hours=1)) or
        index[0] != start or index[-1] != stop-pd.Timedelta(hours=1) or
        index.has_duplicates or not index.is_monotonic_increasing or
        not (index[1:]-index[:-1] == pd.Timedelta(hours=1)).all()):
        raise ValueError('exact contiguous frozen fold index required')
    n=len(index)
    arrays=[]
    for name,obj in [('open',opens),('close',closes),('target',target)]:
        if not isinstance(obj, pd.DataFrame) or not obj.index.equals(index) or tuple(obj.columns)!=ASSETS:
            raise ValueError(f'{name}: exact 5-asset aligned dataframe required')
        a=obj.to_numpy(dtype=float)
        if a.shape!=(n,5) or not np.isfinite(a).all():
            raise ValueError(f'{name}: nonfinite/misaligned')
        arrays.append(a)
    op,cl,w=arrays
    if (op<=0).any() or (cl<=0).any():
        raise ValueError('nonpositive prices')
    if (np.abs(w).sum(axis=1)>1+1e-12).any():
        raise ValueError('gross exposure >1')
    # Only close is used at the final in-fold hour; no future candle is read.
    return op,cl,w


def audit_fold(index, opens, closes, target, start, stop, cost_name):
    if cost_name not in COSTS:
        raise ValueError('only frozen cost schedule')
    op,cl,w=validate_fold(index,opens,closes,target,start,stop)
    cost=COSTS[cost_name]
    n=len(index)
    # Vectorized synthetic independent accounting; no 2026 boundary bar.
    price=np.zeros(n,dtype=float)
    price[1:]=np.sum(w[:-1]*(op[1:]/op[:-1]-1),axis=1)
    turnover=np.empty(n,dtype=float)
    turnover[0]=np.abs(w[0]).sum()
    turnover[1:]=np.abs(w[1:]-w[:-1]).sum(axis=1)
    primary=price-cost*turnover
    secondary=primary.copy()
    # Primary: no new last-open signal; close prior position instead.
    primary[-1]=price[-1]-cost*np.abs(w[-2]).sum()
    # Sensitivity: last-open rebalance, last-bar price move, close at
    # 2025-12-31 23:59:59 (within fold), with two explicit turnover charges.
    secondary[-1]+=float(np.dot(w[-1],cl[-1]/op[-1]-1))-cost*np.abs(w[-1]).sum()
    # In primary, the final signal is intentionally NOT entered. It is not
    # omitted silently: report the gross amount of forced-skipped last signal.
    skipped=float(np.abs(w[-1]).sum())
    return {'primary':pd.Series(primary,index=index),
            'last_close_sensitivity':pd.Series(secondary,index=index),
            'skipped_final_open_gross':skipped,
            'last_close_uses_holdout':False,
            'last_open_timestamp':index[-1].isoformat(),
            'cost':cost_name,
            'promotion_eligible':False}


def metric_contract(r):
    """Independent additive-hourly PnL / compounded-wealth reporting contract."""
    if not isinstance(r,pd.Series) or not isinstance(r.index,pd.DatetimeIndex) or r.empty:
        raise ValueError('hourly series required')
    if (str(r.index.tz)!='UTC' or r.index.has_duplicates or
        not r.index.is_monotonic_increasing or r.index.max()>=CUTOFF or
        not (r.index[1:]-r.index[:-1] == pd.Timedelta(hours=1)).all()):
        raise ValueError('noncontiguous/non-UTC/holdout hourly series')
    v=r.to_numpy(dtype=float)
    if not np.isfinite(v).all() or (v<=-1).any():
        raise ValueError('bankrupt/nonfinite hourly return')
    eq=np.r_[1.,np.cumprod(1+v)]
    peak=np.maximum.accumulate(eq)
    days=(1+r).resample('1D').prod()-1
    pos=v[v>0]; neg=v[v<0]
    return {'compounded_return':float(eq[-1]-1),
            'max_drawdown':float((eq/peak-1).min()),
            'profit_factor':float(pos.sum()/(-neg.sum())) if len(neg) else None,
            'payoff':float(pos.mean()/(-neg.mean())) if len(pos) and len(neg) else None,
            'win_rate':float((v>0).mean()),
            'positive_days':float((days>0).mean()),
            'worst_compounded_day':float(days.min()),
            'best_compounded_day':float(days.max()),
            'daily_tail_p01':float(days.quantile(.01)),
            'daily_tail_p99':float(days.quantile(.99)),
            'total_days':int(len(days))}
