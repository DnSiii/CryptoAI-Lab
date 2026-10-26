#!/usr/bin/env python3
"""EX preregistered cross-horizon, funding-carry and stress capital rotations. TRAINING ONLY."""
from __future__ import annotations
import numpy as np

WARMUP = 744
CLOCK = 120
GROSS_CAP = 2.80
CORE = {"TREND": 2.00, "MIXED": 1.70, "STRESS": 1.30}
TILT = (.06, .06, .07)

def bundle(opening, high, low, close, rate, event, quote):
    o, h, l, c, r, e, q = [np.asarray(x, dtype=float) for x in
                           (opening, high, low, close, rate, event, quote)]
    if (c.ndim != 2 or c.shape[1] != 4 or len(c) <= WARMUP or
        any(x.shape != c.shape for x in (o, h, l, r, e, q)) or
        any(not np.isfinite(x).all() for x in (o, h, l, c, r, e, q)) or
        np.any(l <= 0) or np.any(l > np.minimum(o, c)) or
        np.any(h < np.maximum(o, c)) or np.any(q < 0) or
        np.any((e != 0) & (e != 1))):
        raise ValueError("EX_INVALID_PINNED_SOURCE")
    n = len(c)
    lc = np.log(c)
    hourly = np.diff(lc, axis=0, prepend=lc[:1])
    paid = r * e
    cum_paid = np.vstack((np.zeros((1, 4)), np.cumsum(paid, axis=0)))
    signals = np.zeros((n, 4, 4), dtype=float)
    updates = np.zeros((n, 4), dtype=bool)
    regimes = np.full(n, "MIXED", dtype="<U10")
    budgets = np.zeros((n, 4), dtype=float)

    def native(t, w):
        return lc[t] - lc[t-w] - (cum_paid[t+1] - cum_paid[t-w+1])

    for t in range(WARMUP, n, CLOCK):
        net480 = native(t, 480)
        net120 = native(t, 120)
        net48 = native(t, 48)
        net24 = native(t, 24)
        prev24 = native(t-24, 24)
        downside = np.sqrt(np.mean(np.minimum(hourly[t-239:t+1], 0.) ** 2, axis=0))
        breadth = int(np.count_nonzero(net480 > 0))
        regime = "TREND" if breadth >= 3 else "STRESS" if breadth <= 1 else "MIXED"
        regimes[t] = regime
        score = np.where((net480 > 0) & (net120 > 0),
                         np.maximum(net120, 0.) / np.maximum(downside, 1e-7), 0.)
        w = score / score.sum() if score.sum() > 1e-12 else np.full(4, .25)
        w = .20 * np.full(4, .25) + .80 * w
        signals[t, 0] = w
        budgets[t, 0] = CORE[regime]
        updates[t] = True

        def transfer(target, donor):
            if target == donor or w[donor] < .15:
                return None
            vec = np.zeros(4)
            vec[target] = 1.
            vec[donor] = -1.
            return vec

        # Opportunity: lagged short-term acceleration, funded from the
        # largest other core holding. No realized strategy PnL feedback.
        acceleration = net24 - prev24
        eligible = (net120[1:] > 0) & (acceleration[1:] > 0)
        if eligible.any():
            j = 1 + int(np.argmax(np.where(eligible, acceleration[1:], -np.inf)))
            donors = w.copy()
            donors[j] = -np.inf
            k = int(np.argmax(donors))
            tilt = transfer(j, k)
            if tilt is not None:
                signals[t, 1] = tilt
                budgets[t, 1] = TILT[0]

        # Relative value: forward-agnostic 120h native funding dispersion.
        # Long low-paid funding positive-trend asset, transfer from highest
        # funding donor with meaningful core inventory.
        funding120 = cum_paid[t+1] - cum_paid[t-119]
        eligible = net120 > 0
        if eligible.any():
            j = int(np.argmin(np.where(eligible, funding120, np.inf)))
            donors = np.where((w >= .15) & (np.arange(4) != j), funding120, -np.inf)
            if np.isfinite(donors).any():
                k = int(np.argmax(donors))
                if funding120[k] - funding120[j] >= .0002:
                    tilt = transfer(j, k)
                    if tilt is not None:
                        signals[t, 2] = tilt
                        budgets[t, 2] = TILT[1]

        # Stress/recovery: broad downside plus realized volatility expansion,
        # defensive BTC transfer from largest held alt.
        basket48 = float(np.mean(net48))
        vol48 = float(np.sqrt(np.mean(np.mean(hourly[t-47:t+1], axis=1) ** 2)))
        vol480 = float(np.sqrt(np.mean(np.mean(hourly[t-479:t+1], axis=1) ** 2)))
        if basket48 < 0 and vol48 > vol480:
            donor = 1 + int(np.argmax(w[1:]))
            tilt = transfer(0, donor)
            if tilt is not None:
                signals[t, 3] = tilt
                budgets[t, 3] = TILT[2]

    if (np.any(np.abs(np.sum(signals[:, 1:, :], axis=2)) > 1e-12) or
        np.any(np.sum(abs(signals[:, 1:, :]), axis=2) > 2. + 1e-12) or
        np.any(np.sum(abs(signals[:, 0, :]), axis=1) > 1. + 1e-12) or
        np.any(budgets < 0) or not np.isfinite(budgets).all() or
        np.any(np.sum(abs(signals) * budgets[:, :, None], axis=(1, 2)) >
               GROSS_CAP + 1e-12)):
        raise ValueError("EX_FINANCING_OR_GROSS_INVARIANT")
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
    assert np.allclose(np.sum(a[0][:, 1:, :], axis=2), 0., atol=1e-12)
    return True

if __name__ == "__main__":
    assert static_check()
    print("EX_CAUSAL_SOURCE_STATIC_PASS")
