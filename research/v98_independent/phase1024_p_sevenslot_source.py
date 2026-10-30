#!/usr/bin/env python3
"""V98 Independent P: preregistered Phase1023 seven-slot source-only targets.

No PnL, funding, future validation, contaminated holdout or external engines.
A target observed at close(t) may only trade at open(t+1).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, START, END, PINS, pinned_training_frames

PATHS = ('P_core_only', 'P_full', 'P_minus_opportunity', 'P_minus_relative_value', 'P_minus_recovery')
SHARES = {'growth': .55, 'opportunity': .20, 'relative_value': .15, 'recovery': .10}
EXCLUDE = {'P_core_only': frozenset(('opportunity', 'relative_value', 'recovery')),
           'P_full': frozenset(), 'P_minus_opportunity': frozenset(('opportunity',)),
           'P_minus_relative_value': frozenset(('relative_value',)),
           'P_minus_recovery': frozenset(('recovery',))}
GROSS = {0: .40, 1: 1.10, 2: 1.65}
ASSET_CAP = .70
GROSS_CAP = 1.75
SHOCK_LOOKBACK = 1440
ROOT = Path(__file__).resolve().parent


def _normalize(a):
    v = np.asarray(a, float)
    v = np.where(np.isfinite(v) & (v > 0), v, 0.)
    d = v.sum(axis=1, keepdims=True)
    return np.divide(v, d, out=np.zeros_like(v), where=d > 0)


def _waterfill(score, gross):
    score = np.asarray(score, float)
    if score.shape != (4,) or not np.isfinite(score).all() or (score < 0).any() or not 0 <= gross <= GROSS_CAP:
        raise ValueError('P_INVALID_WATERFILL_INPUT')
    out = np.zeros(4)
    active = score > 0
    remain = float(gross)
    for _ in range(4):
        if not active.any() or remain <= 1e-12:
            break
        take = np.minimum(remain * score * active / (score * active).sum(), np.maximum(ASSET_CAP - out, 0))
        out += take
        remain -= float(take.sum())
        active &= (ASSET_CAP - out > 1e-12)
    if out.sum() > GROSS_CAP + 1e-9 or out.max() > ASSET_CAP + 1e-9:
        raise AssertionError('P_CAP_BREACH')
    return out


def _validate_frames(op, hi, lo, cl, quote):
    expected = pd.date_range(START, END, freq='h')
    for f in (op, hi, lo, cl, quote):
        if not isinstance(f, pd.DataFrame) or tuple(f.columns) != ASSETS or not f.index.equals(expected):
            raise ValueError('P_TRAINING_ONLY_CLEAN4_CHRONOLOGY')
        if not np.isfinite(f.to_numpy(float)).all():
            raise ValueError('P_NONFINITE_INPUT')
    if (op <= 0).any().any() or (lo <= 0).any().any() or (quote < 0).any().any():
        raise ValueError('P_NONPOSITIVE_PRICE_OR_NEGATIVE_VOLUME')
    if (lo > np.minimum(op, cl)).any().any() or (hi < np.maximum(op, cl)).any().any():
        raise ValueError('P_INVALID_OHLC')


def pinned_p_bars(root):
    root = Path(root)
    close, high = pinned_training_frames(root)  # immutable Clean-4 data loader, no K signals
    raw = {a: pd.read_csv(root / (a + '_1h.csv')) for a in ASSETS}
    op = pd.DataFrame({a: raw[a]['open'].to_numpy(float) for a in ASSETS}, index=close.index)
    lo = pd.DataFrame({a: raw[a]['low'].to_numpy(float) for a in ASSETS}, index=close.index)
    q = pd.DataFrame({a: raw[a]['quote_volume'].to_numpy(float) for a in ASSETS}, index=close.index)
    _validate_frames(op, high, lo, close, q)
    return op, high, lo, close, q


def p_shocks(op, hi, lo):
    o, h, l = (x.to_numpy(float) for x in (op, hi, lo))
    down = pd.DataFrame(1-l/o).rolling(SHOCK_LOOKBACK, min_periods=SHOCK_LOOKBACK).max().to_numpy()
    up = pd.DataFrame(h/o-1).rolling(SHOCK_LOOKBACK, min_periods=SHOCK_LOOKBACK).max().to_numpy()
    if (down[np.isfinite(down)] >= 1).any() or (up[np.isfinite(up)] < 0).any():
        raise ValueError('P_INVALID_HISTORICAL_SHOCK')
    return down, up


def compose_p(op, hi, lo, cl, quote, diagnostics=False):
    _validate_frames(op, hi, lo, cl, quote)
    index = cl.index
    logc = np.log(cl)
    r = logc.diff()
    vol = r.rolling(168, min_periods=168).std(ddof=0)
    invvol = 1 / vol.where(vol > 1e-12)
    ema48 = cl.ewm(span=48, adjust=False).mean()
    ema192 = cl.ewm(span=192, adjust=False).mean()
    median576 = cl.shift(1).rolling(576, min_periods=576).median()
    prior96 = hi.shift(1).rolling(96, min_periods=96).max()
    breakout_strength = (cl / prior96 - 1).clip(lower=0)
    core_raw = breakout_strength.div(vol.where(vol > 1e-12)).where((ema48 > ema192) & (cl > median576), 0)
    opp_raw = breakout_strength.where((logc-logc.shift(24) > 0) & (cl > prior96) &
              (quote >= 1.5 * quote.shift(1).rolling(240, min_periods=240).median()), 0)
    market = r.mean(axis=1)
    var = market.rolling(336, min_periods=336).var(ddof=0)
    beta = r.rolling(336, min_periods=336).cov(market).div(var.where(var > 1e-16), axis=0)
    residual96 = (r-beta.mul(market, axis=0)).rolling(96, min_periods=96).sum()
    rv_raw = residual96.sub(residual96.median(axis=1), axis=0).clip(lower=0).where(
        (residual96 > 0) & (logc-logc.shift(192) > 0), 0)
    market24 = market.rolling(24, min_periods=24).sum()
    stress = market24.rolling(168, min_periods=168).min() <= -.08
    market12 = market.rolling(12, min_periods=12).sum() > 0
    candle_range = ((hi-lo)/op).mean(axis=1)
    contracted = candle_range.rolling(12, min_periods=12).mean() < candle_range.shift(12).rolling(48, min_periods=48).mean()
    close_location = (cl-lo).div((hi-lo).where(hi > lo)) - .5
    recovery_raw = (logc-logc.shift(12)).clip(lower=0).where(close_location > 0, 0).mul(
        (stress & market12 & contracted).astype(float), axis=0)
    sleeves = {k: _normalize(v.mul(invvol, axis=0)) for k, v in
               (('growth', core_raw), ('opportunity', opp_raw),
                ('relative_value', rv_raw), ('recovery', recovery_raw))}
    breadth = ((logc-logc.shift(192)) > 0).sum(axis=1)
    v48 = market.rolling(48, min_periods=48).std(ddof=0)
    v336 = market.shift(1).rolling(336, min_periods=336).std(ddof=0)
    ratio = v48 / v336.where(v336 > 1e-12)
    raw_on = (breadth >= 3) & (ratio <= 1)
    raw_off = (breadth <= 1) | (ratio >= 1.8)
    raw = np.where(ratio.notna(), np.where(raw_off, 0, np.where(raw_on, 2, 1)), 0)
    state = 0
    previous = -1
    streak = 0
    states = np.zeros(len(index), np.int8)
    for t, candidate in enumerate(raw):
        candidate = int(candidate)
        streak = streak + 1 if candidate == previous else 1
        previous = candidate
        if candidate != state and streak >= 24:
            state = candidate
        states[t] = state
    paths, diag = {}, {}
    for name in PATHS:
        weights = np.zeros((len(index), 4))
        last = np.zeros(4)
        updates = 0
        for t in range(len(index)):
            if index[t].hour == 23 or (t > 0 and states[t] != states[t-1]):
                active = {k: v[t] for k,v in sleeves.items() if k not in EXCLUDE[name] and v[t].sum() > 0}
                total = sum(SHARES[k] for k in active)
                score = sum((SHARES[k] / total * v for k,v in active.items()), np.zeros(4)) if total else np.zeros(4)
                last = _waterfill(score, GROSS[int(states[t])])
                updates += 1
            weights[t] = last
        frame = pd.DataFrame(weights, index=index, columns=ASSETS)
        paths[name] = frame
        diag[name] = {'sha256': hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest(),
                      'updates': updates, 'active_hours': int((weights.sum(axis=1)>0).sum()),
                      'max_gross': float(weights.sum(axis=1).max()),
                      'max_asset': float(weights.max()), 'l1_turnover': float(np.abs(np.diff(weights, axis=0)).sum())}
    if diagnostics:
        return paths, {'paths':diag, 'regime_hours': {str(i):int((states==i).sum()) for i in (0,1,2)},
                       'sleeve_active_hours': {k:int((v.sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                       'historical_pnl_computed':False,'validation_2025_read':False,'external_benchmarks_used':False}
    return paths


def run_source_only(root=ROOT):
    bars = pinned_p_bars(Path(root)/'phase243_clean4_canonical')
    paths, diag = compose_p(*bars, diagnostics=True)
    return {'phase':1024, 'decision':'P_SOURCE_ONLY_NOT_ECONOMICALLY_APPROVED',
            'source_pins':PINS, 'paths':diag['paths'], 'diagnostics':diag,
            'historical_pnl_computed':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False}

if __name__ == '__main__':
    result = run_source_only()
    (ROOT/'phase1024_p_sevenslot_source_result.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'phase':1024,'decision':result['decision'],'paths':result['paths']},sort_keys=True))
