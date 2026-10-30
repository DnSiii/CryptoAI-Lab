#!/usr/bin/env python3
"""V98 AD source-only causal wealth-expert core and Bayesian regime router.

Phase1188 precommitted constants. No official historical portfolio PnL, holdout,
external benchmarks, AC signals or AD promotion is computed here.
"""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT')
START = pd.Timestamp('2022-12-01T00:00:00Z')
END_EXCLUSIVE = pd.Timestamp('2025-01-01T00:00:00Z')
WARMUP = 336
FEE = .0012
ETA = .35
POSTERIOR_FLOOR = .05
TRANSITION = np.full((3, 3), .0075, dtype=np.float64)
np.fill_diagonal(TRANSITION, .985)
MEANS = np.array([-.45, 0., .45])
SIGMAS = np.array([1.25, 1.40, 1.25])


def validate_source(op, hi, lo, cl, quote, funding, event):
    frames = (op, hi, lo, cl, quote, funding, event)
    if any(not isinstance(f, pd.DataFrame) or tuple(f.columns) != ASSETS for f in frames):
        raise ValueError('AD1189_CLEAN4_COLUMNS')
    idx = cl.index
    if (not isinstance(idx, pd.DatetimeIndex) or idx.tz is None or len(idx) <= WARMUP
            or idx[0] != START or idx[-1] >= END_EXCLUSIVE
            or not idx.equals(pd.date_range(START, periods=len(idx), freq='h'))
            or any(not f.index.equals(idx) for f in frames)):
        raise ValueError('AD1189_TRAINING_CHRONOLOGY')
    arrays = [f.to_numpy(dtype=float) for f in frames]
    if any(not np.isfinite(x).all() for x in arrays):
        raise ValueError('AD1189_NONFINITE')
    o, h, l, c, q, f, e = arrays
    if (np.any(o <= 0) or np.any(c <= 0) or np.any(l <= 0)
            or np.any(h < np.maximum(o, c)) or np.any(l > np.minimum(o, c))
            or np.any(q < 0)):
        raise ValueError('AD1189_OHLC')
    if np.any((e != 0) & (e != 1)) or np.any(f[e == 0] != 0):
        raise ValueError('AD1189_NATIVE_FUNDING_MASK')
    if np.any((e != 0) & (idx.hour.to_numpy()[:, None] % 8 != 0)):
        raise ValueError('AD1189_NATIVE_FUNDING_CLOCK')
    return idx, arrays


def stable_softmax(x):
    a = np.asarray(x, dtype=np.float64)
    if not np.isfinite(a).all():
        raise ValueError('AD1189_NONFINITE_POSTERIOR')
    y = np.exp(a - np.max(a))
    return y / y.sum()


def online_core_router(op, hi, lo, cl, quote, funding, event, diagnostics=False):
    idx, (o, h, l, c, q, f, e) = validate_source(op, hi, lo, cl, quote, funding, event)
    n = len(idx)
    logp = np.log(c)
    logret = np.zeros_like(c)
    logret[1:] = logp[1:] - logp[:-1]
    market_ret = logret.mean(axis=1)
    core = np.zeros((n, 4), dtype=np.float64)
    router = np.full((n, 3), 1/3, dtype=np.float64)
    posterior = np.full((n, 3), 1/3, dtype=np.float64)
    virtual_wealth = np.ones(3, dtype=np.float64)
    experts = np.vstack([np.full(4, .25), np.full(4, .25), np.zeros(4)])
    prior_turnover = np.zeros(3, dtype=np.float64)
    regime = np.full(3, 1/3, dtype=np.float64)
    leader_refreshes = 0
    for t in range(WARMUP, n):
        if t > WARMUP:
            # Decision t-1 -> observed close-to-close t, funding event t.
            realized = c[t] / c[t-1] - 1
            net = experts @ (realized - f[t] * e[t]) - FEE * prior_turnover
            multiplier = 1 + net
            if np.any(multiplier <= 0) or not np.isfinite(multiplier).all():
                raise ValueError('AD1189_VIRTUAL_INSOLVENCY')
            virtual_wealth *= multiplier
            if np.any(virtual_wealth <= 0) or not np.isfinite(virtual_wealth).all():
                raise ValueError('AD1189_VIRTUAL_WEALTH')
        p = stable_softmax(ETA * np.log(virtual_wealth))
        p = np.maximum(p, POSTERIOR_FLOOR)
        p /= p.sum()
        posterior[t] = p
        # Precommitted refresh at completed hour t; weights apply only at t+1.
        next_experts = experts.copy()
        if t % 24 == 0:
            momentum = logp[t] - logp[t-96]
            sigma = np.maximum(np.std(logret[t-167:t+1], axis=0, ddof=0), .002)
            leadership = stable_softmax(momentum / (np.sqrt(168.) * sigma))
            next_experts[1] = .90 * leadership + .10 * .25
            leader_refreshes += 1
        core[t] = p @ next_experts
        prior_turnover = np.abs(next_experts - experts).sum(axis=1)
        experts = next_experts
        # Likelihood uses t observation and only t-168..t-1 volatility.
        prior_vol = max(float(np.std(market_ret[t-168:t], ddof=0)), .002)
        x = float(np.clip(market_ret[t] / prior_vol, -8, 8))
        predicted = regime @ TRANSITION
        log_likelihood = -.5 * ((x - MEANS) / SIGMAS)**2 - np.log(SIGMAS)
        regime = stable_softmax(np.log(predicted) + log_likelihood)
        router[t] = regime
    if diagnostics:
        return core, router, {'phase':1189, 'source_only':True,
            'historical_system_pnl_computed':False, 'validation_2025_read':False,
            'external_benchmarks_used':False, 'earliest_fill':'t+1 open',
            'warmup_hours':WARMUP, 'expert_refreshes':leader_refreshes,
            'posterior_last':posterior[-1].tolist(),
            'virtual_expert_wealth_last':virtual_wealth.tolist(),
            'router_last':router[-1].tolist(),
            'source_rows':n}
    return core, router


def observer_digest(core, router, index):
    """Non-frozen local observer only; cross-OS hash gate separately preregistered."""
    if core.shape != (len(index), 4) or router.shape != (len(index), 3):
        raise ValueError('AD1189_OBSERVER_SHAPE')
    payload = np.rint(np.column_stack((core, router)) * 1_000_000).astype('<i8')
    return hashlib.sha256(b'AD1189_NONFROZEN_OBSERVER_V1\n' +
                          index.tz_convert('UTC').asi8.astype('<i8').tobytes() +
                          payload.tobytes()).hexdigest()
