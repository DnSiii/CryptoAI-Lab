#!/usr/bin/env python3
"""V98 Independent AK: slow directional inventory, carry RV and stress sources.

This file contains only AK source modules/router; it never reads 2025 or PnL.
"""
from __future__ import annotations
import numpy as np

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
STATES = ("BULL", "BEAR", "CHOP", "STRESS")
WARMUP = 2016
WEEK = 168

def inputs(close, high, low, funding_rate, funding_event):
    c, h, l, r, e = (np.asarray(x, dtype=np.float64) for x in
                     (close, high, low, funding_rate, funding_event))
    if (c.ndim != 2 or c.shape[1] != 4 or
        any(x.shape != c.shape for x in (h, l, r, e)) or
        any(not np.isfinite(x).all() for x in (c, h, l, r, e)) or
        np.any(c <= 0) or np.any(l <= 0) or np.any(l > c) or
        np.any(h < c) or not np.isin(e, (0., 1.)).all()):
        raise ValueError("AK_INVALID_AUTHENTICATED_INPUT")
    return c, h, l, r, e

def source_bundle(close, high, low, funding_rate, funding_event):
    c, h, l, r, e = inputs(close, high, low, funding_rate, funding_event)
    n = len(c)
    logc = np.log(c)
    lr = np.diff(logc, axis=0, prepend=logc[:1])
    growth = np.zeros_like(c)
    opportunity = np.zeros_like(c)
    relative = np.zeros_like(c)
    stress = np.zeros_like(c)
    states = np.full(n, "CHOP", dtype="<U6")
    opportunity_expiry = np.zeros(4, dtype=np.int64)
    last_stress = -10**9
    hedge_until = -1
    recovery_until = -1
    for t in range(WARMUP, n):
        # All arrays at t use only completed t and prior bars; trading is t+1.
        r28 = logc[t] - logc[t - 672]
        r84 = logc[t] - logc[t - 2016]
        eligible = (r28 > 0.) & (r84 > 0.)
        strength = np.where(eligible, np.minimum(r28, r84 / 3.), 0.)
        if strength.sum() > 0.:
            growth[t] = strength / strength.sum()
        # Opportunity is a low-frequency persistent event, not hourly chasing.
        vol48 = np.sqrt(np.mean(lr[t - 47:t + 1] ** 2, axis=0))
        vol336 = np.sqrt(np.mean(lr[t - 335:t + 1] ** 2, axis=0))
        breakout = (c[t] > np.max(h[t - 168:t], axis=0)) & (
            vol48 > 1.15 * np.maximum(vol336, 1e-8))
        opportunity_expiry[breakout] = t + WEEK
        active = opportunity_expiry > t
        if active.any():
            opportunity[t, active] = 1. / active.sum()
        # Native 8h funding, last 21 actual events, dollar-neutral rank.
        rates = r[t - 167:t + 1] * e[t - 167:t + 1]
        carry = rates.sum(axis=0)
        rank = np.lexsort((np.arange(4), carry))
        relative[t, rank[:2]] = .25
        relative[t, rank[2:]] = -.25
        # Stress and recovery use a portfolio-level, not asset-chasing trigger.
        market72 = float(np.mean(logc[t] - logc[t - 72]))
        if market72 < -.10:
            last_stress = t
            hedge_until = t + 72
            recovery_until = -1
        elif market72 > .07 and t - last_stress <= 168:
            recovery_until = t + 72
        if t < hedge_until:
            stress[t] = (-.25, -.25, -.25, -.25)
        elif t < recovery_until:
            stress[t] = (.25, .25, .25, .25)
        # Router uses completed 28d market direction and 7d breadth.
        breadth = int(np.count_nonzero(logc[t] - logc[t - 168] > 0))
        market28 = float(np.mean(r28))
        if market72 < -.10:
            states[t] = "STRESS"
        elif market28 > .03 and breadth >= 3:
            states[t] = "BULL"
        elif market28 < -.03 and breadth <= 1:
            states[t] = "BEAR"
    return growth, opportunity, relative, stress, {"state": states}

def causal_check():
    t = np.arange(2350, dtype=np.float64)
    c = 100. * np.exp(.0004 * t[:, None] *
                       np.array([[1., 1.1, .8, 1.3]]))
    h, l = c * 1.003, c * .997
    r = np.zeros_like(c)
    e = np.zeros_like(c)
    e[::8] = 1.
    r[::8] = (.0001, -.0001, .0002, -.0002)
    before = source_bundle(c, h, l, r, e)
    changed = c.copy()
    changed[-24:] *= 2.
    after = source_bundle(changed, np.maximum(h, changed),
                          np.minimum(l, changed), r, e)
    for a, b in zip(before[:4], after[:4]):
        assert np.array_equal(a[:-24], b[:-24])
    assert np.array_equal(before[4]["state"][:-24],
                          after[4]["state"][:-24])
    assert all(x.shape == c.shape for x in before[:4])
    assert np.all(np.abs(before[0]).sum(axis=1) <= 1.00000001)
    assert np.all(np.abs(before[1]).sum(axis=1) <= 1.00000001)
    assert np.all(np.abs(before[2]).sum(axis=1) <= 1.00000001)
    assert np.all(np.abs(before[3]).sum(axis=1) <= 1.00000001)
    return True

if __name__ == "__main__":
    print("AK_SOURCE_CAUSAL_TEST", "PASS" if causal_check() else "FAIL")
