#!/usr/bin/env python3
"""EY preregistered additive multi-premium seven-slot portfolio. TRAINING ONLY."""
from __future__ import annotations
import numpy as np

WARMUP = 744
CLOCK = 144
GROSS_CAP = 2.80
CORE = {"TREND": 2.20, "MIXED": 1.80, "STRESS": 1.40}
SLEEVE = .12

def capped_inverse_vol(v):
    inverse = 1. / np.maximum(np.asarray(v, dtype=float), 1e-7)
    capped = np.zeros(4, dtype=bool)
    w = np.zeros(4)
    for _ in range(5):
        free = ~capped
        remaining = 1. - .45 * int(np.count_nonzero(capped))
        if not free.any() or remaining < 0:
            raise ValueError("EY_VOL_WATERFILL")
        w[capped] = .45
        w[free] = remaining * inverse[free] / inverse[free].sum()
        new = free & (w > .45 + 1e-12)
        if not new.any():
            break
        capped |= new
    if abs(w.sum() - 1.) > 1e-10 or np.max(w) > .45 + 1e-10:
        raise ValueError("EY_VOL_CAP")
    return w

def bundle(opening, high, low, close, rate, event, quote):
    o, h, l, c, r, e, q = [np.asarray(x, dtype=float) for x in
                           (opening, high, low, close, rate, event, quote)]
    if (c.ndim != 2 or c.shape[1] != 4 or len(c) <= WARMUP or
        any(x.shape != c.shape for x in (o, h, l, r, e, q)) or
        any(not np.isfinite(x).all() for x in (o, h, l, c, r, e, q)) or
        np.any(l <= 0) or np.any(l > np.minimum(o, c)) or
        np.any(h < np.maximum(o, c)) or np.any(q < 0) or
        np.any((e != 0) & (e != 1))):
        raise ValueError("EY_INVALID_PINNED_SOURCE")
    n = len(c)
    lc = np.log(c)
    hourly = np.diff(lc, axis=0, prepend=lc[:1])
    funding = r * e
    cumulative = np.vstack((np.zeros((1, 4)), np.cumsum(funding, axis=0)))
    signals = np.zeros((n, 4, 4), dtype=float)
    updates = np.zeros((n, 4), dtype=bool)
    regimes = np.full(n, "MIXED", dtype="<U10")
    budgets = np.zeros((n, 4), dtype=float)

    def native(t, w):
        return lc[t] - lc[t-w] - (cumulative[t+1] - cumulative[t-w+1])

    for t in range(WARMUP, n, CLOCK):
        net360, net72, net24 = (native(t, w) for w in (360, 72, 24))
        breadth = int(np.count_nonzero(net360 > 0))
        regime = "TREND" if breadth >= 3 else "STRESS" if breadth <= 1 else "MIXED"
        regimes[t] = regime
        vol360 = np.sqrt(np.mean(hourly[t-359:t+1] ** 2, axis=0))
        signals[t, 0] = capped_inverse_vol(vol360)
        budgets[t, 0] = CORE[regime]
        updates[t] = True

        # Opportunity: native-net 72h cross-sectional directional leadership.
        if np.count_nonzero(net72 > 0) >= 2:
            j = int(np.argmax(net72))
            signals[t, 1, j] = 1.
            budgets[t, 1] = SLEEVE

        # Relative value: positive native-net long-horizon trend and
        # cheapest 240h realized funding, with a median carry advantage.
        funding240 = cumulative[t+1] - cumulative[t-239]
        eligible = net360 > 0
        if eligible.any():
            j = int(np.argmin(np.where(eligible, funding240, np.inf)))
            if funding240[j] < float(np.median(funding240)):
                signals[t, 2, j] = 1.
                budgets[t, 2] = SLEEVE

        # Stress/recovery: long the first broad positive 24h response to
        # an otherwise negative 72h basket, no short or capital transfer.
        if float(np.mean(net72)) < 0 and float(np.mean(net24)) > 0:
            j = int(np.argmax(net24))
            if net24[j] > 0:
                signals[t, 3, j] = 1.
                budgets[t, 3] = SLEEVE

    if (np.any(signals < 0) or np.any(budgets < 0) or
        np.any(np.sum(abs(signals), axis=2) > 1. + 1e-12) or
        not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals) * budgets[:, :, None], axis=(1, 2)) >
               GROSS_CAP + 1e-12)):
        raise ValueError("EY_GROSS_OR_SOURCE_INVARIANT")
    return signals, updates, regimes, budgets

def static_check():
    n = 3800
    t = np.arange(n, dtype=float)
    c = 100 * np.exp(t[:, None] * np.array([[.0002, .0003, .0004, .0005]]) +
                     .05 * np.sin(t[:, None] / 97. + np.arange(4)))
    o = c * (1. - .002 * np.sin(t[:, None] / 11. + np.arange(4)))
    h = np.maximum(o, c) * 1.01
    l = np.minimum(o, c) * .99
    q = 1e6 * (1.2 + .2 * np.sin(t[:, None] / 37. + np.arange(4)))
    r = np.full_like(c, .0001)
    e = np.zeros_like(c)
    e[::8] = 1.
    a = bundle(o, h, l, c, r, e, q)
    c2, o2, h2, l2, q2, r2 = [x.copy() for x in (c, o, h, l, q, r)]
    for x in (c2, o2, h2, l2):
        x[3200:] *= 1.8
    q2[3200:] *= 4.
    r2[3200:] *= -1.
    b = bundle(o2, h2, l2, c2, r2, e, q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200], b[i][:3200]), i
    assert not a[0][:WARMUP].any()
    assert np.all(a[1][np.arange(WARMUP, n, CLOCK)].all(axis=1))
    assert np.all(np.sum(abs(a[0]), axis=2) <= 1. + 1e-12)
    assert np.all(a[0][:, 0, :].max(axis=1) <= .45 + 1e-12)
    return True

if __name__ == "__main__":
    assert static_check()
    print("EY_ADDITIVE_PREMIUM_CAUSAL_STATIC_PASS")
