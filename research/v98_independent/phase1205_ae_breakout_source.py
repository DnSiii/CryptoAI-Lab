#!/usr/bin/env python3
"""V98 AE independent causal breakout source; source-only, no portfolio PnL."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT')
START = pd.Timestamp('2022-12-01T00:00:00Z')
END_EXCLUSIVE = pd.Timestamp('2025-01-01T00:00:00Z')
CHANNEL = 240
VOL_WINDOW = 48
VOL_FLOOR = .002
CORE_GROSS = .65
OPPORTUNITY_GROSS = .12
RV_SIDE = .10
BREAKOUT_COUNT = 3
BREAKOUT_LOOKBACK = 24
OPPORTUNITY_HOLD = 12
ROUTER_SMOOTH = .90


def validate_ae_source(op, hi, lo, cl, quote, funding, event):
    frames = (op, hi, lo, cl, quote, funding, event)
    if any(not isinstance(f, pd.DataFrame) or tuple(f.columns) != ASSETS for f in frames):
        raise ValueError('AE1205_CLEAN4_COLUMNS')
    idx = cl.index
    if (not isinstance(idx, pd.DatetimeIndex) or idx.tz is None or
            len(idx) <= CHANNEL or idx[0] != START or idx[-1] >= END_EXCLUSIVE or
            not idx.equals(pd.date_range(START, periods=len(idx), freq='h')) or
            any(not f.index.equals(idx) for f in frames)):
        raise ValueError('AE1205_TRAINING_CHRONOLOGY')
    arrays = tuple(f.to_numpy(dtype=float) for f in frames)
    if any(a.shape != (len(idx), 4) or not np.isfinite(a).all() for a in arrays):
        raise ValueError('AE1205_NONFINITE')
    o, h, l, c, q, r, e = arrays
    if (np.any(o <= 0) or np.any(c <= 0) or np.any(l <= 0) or
            np.any(h < np.maximum(o, c)) or np.any(l > np.minimum(o, c)) or
            np.any(q < 0)):
        raise ValueError('AE1205_OHLC_QUOTE')
    if (np.any((e != 0) & (e != 1)) or np.any(r[e == 0] != 0) or
            np.any((e != 0) & (idx.hour.to_numpy()[:, None] % 8 != 0))):
        raise ValueError('AE1205_NATIVE_FUNDING_MASK')
    return idx, arrays


def ae_breakout_source(op, hi, lo, cl, quote, funding, event):
    """Decision at completed close t is only eligible for execution at open t+1."""
    idx, (_, high, low, close, _, _, _) = validate_ae_source(
        op, hi, lo, cl, quote, funding, event)
    n = len(idx)
    growth = np.zeros((n, 4), dtype=np.float64)
    opportunity = np.zeros((n, 4), dtype=np.float64)
    relative_value = np.zeros((n, 4), dtype=np.float64)
    router = np.zeros((n, 3), dtype=np.float64)
    router[:, 1] = 1.
    logp = np.log(close)
    ret = np.zeros_like(close)
    ret[1:] = logp[1:] - logp[:-1]
    state = np.zeros(4, dtype=np.int8)
    fresh = np.zeros((n, 4), dtype=np.int8)
    occupancy = np.zeros(n, dtype=np.float64)
    posterior = .5
    opp_end = -1
    opp_vector = np.zeros(4, dtype=np.float64)
    for t in range(CHANNEL, n):
        # Strictly prior 240h channel and prior 48 completed hourly returns.
        top = high[t-CHANNEL:t].max(axis=0)
        bottom = low[t-CHANNEL:t].min(axis=0)
        midpoint = (top + bottom) / 2
        occupancy[t] = np.mean(close[t] > midpoint)
        up = close[t] > top
        down = close[t] < bottom
        fresh[t, up] = 1
        fresh[t, down] = -1
        state[up] = 1
        state[down] = -1
        vol = np.maximum(np.std(ret[t-VOL_WINDOW:t], axis=0), VOL_FLOOR)
        invvol = np.clip(VOL_FLOOR / vol, .1, 10.)
        raw = state * invvol
        gross = np.abs(raw).sum()
        if gross:
            growth[t] = CORE_GROSS * raw / gross
        longs = state > 0
        shorts = state < 0
        if longs.any() and shorts.any():
            relative_value[t, longs] = RV_SIDE / longs.sum()
            relative_value[t, shorts] = -RV_SIDE / shorts.sum()
        recent = fresh[max(CHANNEL, t-BREAKOUT_LOOKBACK+1):t+1]
        for sign in (1, -1):
            qualifying = (recent == sign).any(axis=0)
            if int(qualifying.sum()) >= BREAKOUT_COUNT:
                opp_vector = np.zeros(4, dtype=float)
                opp_vector[qualifying] = sign * OPPORTUNITY_GROSS / qualifying.sum()
                opp_end = t + OPPORTUNITY_HOLD
                break
        if t < opp_end:
            opportunity[t] = opp_vector
        # Completed-hour 24h occupancy is observed only after close[t].
        average = occupancy[max(CHANNEL, t-23):t+1].mean()
        posterior = ROUTER_SMOOTH * posterior + (1-ROUTER_SMOOTH) * average
        router[t] = (1., 0., 0.) if posterior < .40 else (
            (0., 0., 1.) if posterior > .60 else (0., 1., 0.))
    if (not all(np.isfinite(x).all() for x in
                (growth, opportunity, relative_value, router)) or
            np.any(np.abs(growth).sum(axis=1) > CORE_GROSS + 1e-10) or
            np.any(np.abs(opportunity).sum(axis=1) > OPPORTUNITY_GROSS + 1e-10) or
            np.any(np.abs(relative_value.sum(axis=1)) > 1e-10)):
        raise ValueError('AE1205_SOURCE_INVARIANTS')
    return growth, opportunity, relative_value, router


def source_digest(index, outputs):
    if len(outputs) != 4 or any(x.shape != (len(index), 4 if k < 3 else 3)
                                for k, x in enumerate(outputs)):
        raise ValueError('AE1205_DIGEST_SHAPE')
    payload = np.rint(np.column_stack(outputs) * 1_000_000).astype('<i8')
    return hashlib.sha256(b'AE1205_SOURCE_ONLY_V1\n' +
        index.tz_convert('UTC').asi8.astype('<i8').tobytes() +
        payload.tobytes()).hexdigest()
