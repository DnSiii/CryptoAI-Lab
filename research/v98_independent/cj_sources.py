#!/usr/bin/env python3
"""CJ preregistered EMA inventory, alt acceleration, relative continuation and stress; training 2022-2024 only."""
from __future__ import annotations
import numpy as np

WARMUP = 2160
GRID = 168
BUDGETS = {
    "RISK_ON": np.array([1.65, 0.50, 0.30, 0.15]),
    "MIXED": np.array([1.10, 0.40, 0.35, 0.35]),
    "RISK_OFF": np.array([0.45, 0.20, 0.45, 0.65]),
}

def _ema(c, span):
    a = 2.0 / (span + 1.0)
    out = np.empty_like(c)
    out[0] = c[0]
    for t in range(1, len(c)):
        out[t] = a * c[t] + (1.0 - a) * out[t - 1]
    return out

def bundle(close, rate, event):
    c = np.asarray(close, dtype=float)
    r = np.asarray(rate, dtype=float)
    e = np.asarray(event, dtype=float)
    if (c.ndim != 2 or c.shape[1] != 4 or r.shape != c.shape or e.shape != c.shape
        or len(c) <= WARMUP or not np.isfinite(c).all() or not np.isfinite(r).all()
        or not np.isfinite(e).all() or np.any(c <= 0)
        or np.any((e != 0) & (e != 1))):
        raise ValueError("CJ_SOURCE_INPUT")
    n = len(c)
    lc = np.log(c)
    ema_fast = _ema(c, 168)
    ema_slow = _ema(c, 672)
    signals = np.zeros((n, 4, 4), dtype=float)
    updates = np.zeros((n, 4), dtype=bool)
    regimes = np.full(n, "MIXED", dtype="<U8")
    for t in range(WARMUP, n, GRID):
        hourly = np.diff(lc[t-672:t+1], axis=0)
        v48 = np.std(hourly[-48:, 0], ddof=1)
        v168 = np.std(hourly[-168:, 0], ddof=1)
        v336 = np.std(hourly[-336:, 0], ddof=1)
        v672 = np.std(hourly[:, 0], ddof=1)
        ratio_router = float(v168 / max(v672, 1e-8))
        both_up = bool(np.all(ema_fast[t, :2] > ema_slow[t, :2]))
        both_down = bool(np.all(ema_fast[t, :2] < ema_slow[t, :2]))
        regime = ("RISK_ON" if both_up and ratio_router < 1.4
                  else "RISK_OFF" if both_down or ratio_router >= 1.6
                  else "MIXED")
        regimes[t] = regime

        # Slot 1: two-market EMA inventory with symmetric directional permission.
        eligible = []
        for j in (0, 1):
            if ema_fast[t, j] > ema_slow[t, j] and c[t, j] > ema_fast[t, j]:
                eligible.append((j, 1.0))
            elif ema_fast[t, j] < ema_slow[t, j] and c[t, j] < ema_fast[t, j]:
                eligible.append((j, -1.0))
        for j, sign in eligible:
            signals[t, 0, j] = sign / len(eligible)
        updates[t, 0] = True

        # Slot 2: acceleration of alternative assets, with long-horizon support.
        acceleration = (lc[t] - lc[t-96]) - (lc[t-96] - lc[t-192])
        long_ret = lc[t] - lc[t-504]
        eligible = [j for j in (2, 3) if acceleration[j] > 0 and long_ret[j] > 0]
        if eligible:
            j = sorted(eligible, key=lambda j: (-acceleration[j], j))[0]
            signals[t, 1, j] = 1.0
        updates[t, 1] = True

        # Slot 3: beta-adjusted ETH/BTC relative trend continuation.
        btc = hourly[-336:, 0]
        eth = hourly[-336:, 1]
        beta = float(np.clip(np.cov(eth, btc, ddof=1)[0, 1] /
                             max(np.var(btc, ddof=1), 1e-12), 0.5, 2.0))
        ret336 = lc[t] - lc[t-336]
        residual = float(ret336[1] - beta * ret336[0])
        if residual != 0:
            sign = 1.0 if residual > 0 else -1.0
            signals[t, 2, 1] = sign / (1.0 + beta)
            signals[t, 2, 0] = -sign * beta / (1.0 + beta)
        updates[t, 2] = True

        # Slot 4: volatility-confirmed downside trend or post-bear rebound.
        r48 = float(lc[t, 0] - lc[t-48, 0])
        r336 = float(ret336[0])
        ratio_stress = float(v48 / max(v336, 1e-8))
        if r48 < 0 and ratio_stress > 1.0:
            signals[t, 3, 0] = -1.0
        elif r48 > 0 and ratio_stress > 1.5 and r336 < 0:
            signals[t, 3, 0] = 1.0
        updates[t, 3] = True
    if np.any(np.sum(abs(signals), axis=2) > 1.0 + 1e-12):
        raise ValueError("CJ_GROSS_SOURCE")
    if np.any(np.abs(signals[:, 2, :].sum(axis=1)) > 0.34):
        # Beta-neutral legs are not necessarily dollar-neutral; gross remains one.
        raise ValueError("CJ_RV_UNEXPECTED_NET")
    return signals, updates, regimes

def static_check():
    n = 3500
    t = np.arange(n, dtype=float)
    c = 100 * np.exp(t[:, None] * np.array([[.0002, .0003, .0004, .0005]])
                     + .05 * np.sin(t[:, None] / 97. + np.arange(4)))
    r = np.full_like(c, .0001)
    e = np.zeros_like(c)
    e[::8] = 1.
    s, m, z = bundle(c, r, e)
    changed = c.copy()
    changed[2900:] *= 1.9
    rates = r.copy()
    rates[2900:] *= -1
    s2, m2, z2 = bundle(changed, rates, e)
    assert np.array_equal(s[:2900], s2[:2900])
    assert np.array_equal(m, m2)
    assert np.array_equal(z[:2900], z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s), axis=2) <= 1.0 + 1e-12)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True

if __name__ == "__main__":
    assert static_check()
    print("CJ_CAUSAL_EMA_ACCELERATION_RELATIVE_TREND_SOURCE_PASS")
