#!/usr/bin/env python3
"""V98 AC source-only, seven-slot discrete intents; no historical PnL.

Pre-registered in phase1173. Only completed t information is used; any fill
must be performed by a separate stateful executor no earlier than t+1.
"""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT')
MODES = ('immediate', 'capacity_1m', 'capacity_10m')
PATHS = ('AC_core_only', 'AC_full', 'AC_minus_opportunity',
         'AC_minus_relative_value', 'AC_minus_stress')
SLEEVES = ('growth', 'opportunity', 'relative_value', 'stress')
EXCLUDE = {
    'AC_core_only': ('opportunity', 'relative_value', 'stress'),
    'AC_full': (),
    'AC_minus_opportunity': ('opportunity',),
    'AC_minus_relative_value': ('relative_value',),
    'AC_minus_stress': ('stress',),
}
# Fixed integer routing; the dynamic actual-NAV allocator is a later gate.
ROUTER = np.array([[1, 0, 1, 2], [2, 1, 1, 1], [3, 2, 1, 0]], dtype=np.int16)


def validate_source(op, hi, lo, cl, quote, funding):
    inputs = (op, hi, lo, cl, quote, funding)
    if any(not isinstance(f, pd.DataFrame) or tuple(f.columns) != ASSETS for f in inputs):
        raise ValueError('AC1174_CLEAN4_COLUMNS')
    idx = cl.index
    if (not isinstance(idx, pd.DatetimeIndex) or idx.tz is None or len(idx) < 900
            or idx[0] < pd.Timestamp('2022-12-01T00:00:00Z')
            or idx[-1] >= pd.Timestamp('2025-01-01T00:00:00Z')
            or not idx.equals(pd.date_range(idx[0], periods=len(idx), freq='h'))
            or any(not f.index.equals(idx) for f in inputs)):
        raise ValueError('AC1174_TRAINING_CHRONOLOGY')
    arrays = [f.to_numpy(dtype=np.float64) for f in inputs]
    if any(not np.isfinite(x).all() for x in arrays):
        raise ValueError('AC1174_NONFINITE_SOURCE')
    o, h, l, c, q, _ = arrays
    if (np.any(o <= 0) or np.any(c <= 0) or np.any(l <= 0)
            or np.any(h < np.maximum(o, c)) or np.any(l > np.minimum(o, c))
            or np.any(q < 0)):
        raise ValueError('AC1174_BAD_OHLC_OR_VOLUME')
    return idx


def held_events(direction, eligible, hold=12, lockout=96):
    d = np.asarray(direction, dtype=np.int8)
    eligible = np.asarray(eligible, dtype=bool)
    if d.ndim != 2 or d.shape != eligible.shape or d.shape[1] != 4:
        raise ValueError('AC1174_EVENT_SHAPE')
    out = np.zeros_like(d)
    expiry = np.zeros(4, dtype=np.int64)
    next_allowed = np.zeros(4, dtype=np.int64)
    current = np.zeros(4, dtype=np.int8)
    for t in range(len(d)):
        trigger = eligible[t] & (d[t] != 0) & (t >= next_allowed)
        current[trigger] = d[t, trigger]
        expiry[trigger] = t + hold
        next_allowed[trigger] = t + lockout
        out[t] = np.where(t < expiry, current, 0)
    return out


def dwell_regime(raw, min_dwell=72):
    raw = np.asarray(raw, dtype=np.int8)
    if raw.ndim != 1 or np.any((raw < 0) | (raw > 2)):
        raise ValueError('AC1174_REGIME_INPUT')
    result = np.ones(len(raw), dtype=np.int8)
    state, next_change = 1, 0
    for t, candidate in enumerate(raw):
        if int(candidate) != state and t >= next_change:
            state, next_change = int(candidate), t + min_dwell
        result[t] = state
    return result


def compute_slots(op, hi, lo, cl, quote, funding):
    validate_source(op, hi, lo, cl, quote, funding)
    log = np.log(cl)
    ret = log.diff().fillna(0.)
    r168 = log - log.shift(168)
    r720 = log - log.shift(720)
    # Growth: ordinal long-horizon persistence with causal downside penalty.
    relative = r168.sub(r168.median(axis=1), axis=0)
    downside = ret.clip(upper=0).pow(2).rolling(168, min_periods=168).mean().pow(.5)
    down_ref = downside.median(axis=1)
    raw_growth = (np.sign(r720).fillna(0.).to_numpy(dtype=np.int16)
                  + np.sign(relative).fillna(0.).to_numpy(dtype=np.int16))
    penalty = downside.gt(1.5 * down_ref, axis=0).fillna(False).to_numpy(bool)
    growth = np.where(penalty, raw_growth - np.sign(raw_growth), raw_growth).astype(np.int8)
    growth[:720] = 0

    # Opportunity: completed volume shock with close-location directional impulse.
    baseline = quote.shift(1).rolling(48, min_periods=48).median().clip(lower=1e-8)
    vol_shock = quote / baseline
    clv = (2 * cl - hi - lo) / (hi - lo).clip(lower=1e-8)
    eligible = ((vol_shock > 3) & (clv.abs() > .6)).fillna(False).to_numpy(bool)
    opportunity = held_events(np.sign(clv).fillna(0.).to_numpy(dtype=np.int8), eligible)
    opportunity[:720] = 0

    # Relative value: 72h cross-sectional reversal with strictly prior dispersion gate.
    rv_72 = log - log.shift(72)
    rv_vol = ret.rolling(72, min_periods=72).std(ddof=0).clip(lower=1e-8)
    risk_adj = rv_72 / (rv_vol * np.sqrt(72.))
    dispersion = risk_adj.max(axis=1) - risk_adj.min(axis=1)
    baseline_disp = dispersion.shift(1).rolling(336, min_periods=336).median()
    valid = (dispersion > 1.25 * baseline_disp) & (baseline_disp > 0)
    ranks = risk_adj.to_numpy(dtype=float)
    relative_value = np.zeros_like(growth)
    for t in range(720, len(growth)):
        if bool(valid.iloc[t]) and np.isfinite(ranks[t]).all():
            lo_j, hi_j = int(np.argmin(ranks[t])), int(np.argmax(ranks[t]))
            if lo_j != hi_j:
                relative_value[t, lo_j] = 1
                relative_value[t, hi_j] = -1

    # Stress/recovery: downside breadth, 168h tail reference and 48h recovery.
    r12 = log - log.shift(12)
    neg_tail = r12.clip(upper=0).abs().shift(1).rolling(168, min_periods=168).quantile(.9)
    shock_breadth = (r12 < -1.5 * neg_tail).sum(axis=1).to_numpy(dtype=int)
    recover_breadth = ((log - log.shift(48)) > 0).sum(axis=1).to_numpy(dtype=int)
    stress = np.zeros_like(growth)
    active = False
    for t in range(720, len(growth)):
        if shock_breadth[t] >= 3:
            active = True
        elif recover_breadth[t] >= 3:
            active = False
        if active:
            stress[t] = -1

    # Regime: completed BTC quote volume percentile and market median 168h return.
    btc_q = quote['BTCUSDT']
    low_q = btc_q.shift(1).rolling(720, min_periods=720).quantile(.25)
    high_q = btc_q.shift(1).rolling(720, min_periods=720).quantile(.75)
    median_r = r168.median(axis=1)
    raw = np.where((btc_q > high_q) & (median_r > 0), 2,
                   np.where((btc_q < low_q) & (median_r < 0), 0, 1))
    regime = dwell_regime(raw)
    return {'growth': growth, 'opportunity': opportunity,
            'relative_value': relative_value, 'stress': stress}, regime


def compose_intents(op, hi, lo, cl, quote, funding, diagnostics=False):
    slots, regime = compute_slots(op, hi, lo, cl, quote, funding)
    n = len(cl)
    out = {}
    for mode in MODES:
        for path in PATHS:
            scores = np.zeros((n, 4), dtype=np.int16)
            for slot_index, name in enumerate(SLEEVES):
                if name not in EXCLUDE[path]:
                    scores += ROUTER[regime, slot_index, None] * slots[name].astype(np.int16)
            # Fixed integer signed conviction: avoid floating serialization drift.
            scores = np.clip(scores, -4, 4).astype(np.int8)
            out[path, mode] = scores
    if diagnostics:
        return out, {'source_only': True, 'historical_pnl_computed': False,
                     'validation_2025_read': False, 'external_benchmarks_used': False,
                     'earliest_fill': 't+1',
                     'regime_hours': {str(k): int((regime == k).sum()) for k in range(3)},
                     'sleeve_active_hours': {k: int(np.count_nonzero(v)) for k, v in slots.items()},
                     'path_active_hours': {p + '__' + m: int(np.count_nonzero(np.any(v, axis=1)))
                                           for (p, m), v in out.items()}}
    return out


def canonical_hash(scores, index, path, mode):
    a = np.asarray(scores)
    if (path not in PATHS or mode not in MODES or a.ndim != 2
            or a.shape[1] != 4 or len(a) != len(index)
            or not np.issubdtype(a.dtype, np.integer)
            or np.any(np.abs(a.astype(np.int64)) > 4)):
        raise ValueError('AC1174_CANONICAL_INPUT')
    if not isinstance(index, pd.DatetimeIndex) or index.tz is None:
        raise ValueError('AC1174_CANONICAL_TIMEZONE')
    header = ('V98_AC_INTENT_V1|' + path + '|' + mode + '|'
              + ','.join(ASSETS) + '|' + str(len(index)) + '\n').encode('ascii')
    times = np.asarray(index.tz_convert('UTC').asi8, dtype='<i8').tobytes(order='C')
    return hashlib.sha256(header + times + a.astype(np.int8).tobytes(order='C')).hexdigest()
