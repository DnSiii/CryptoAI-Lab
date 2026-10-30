#!/usr/bin/env python3
"""V98 AK independent weekly wealth allocator and actual-open risk governor."""
from __future__ import annotations
from collections import deque
import numpy as np

WEEK = 168
LOOKBACK = 672
SHARE = .0025
FUNDING_RESERVE_HOURS = 24
FLOOR = .40
MAINTENANCE = .18
EXIT_FRICTION_MULTIPLIER = 2.2
FEES = {'base': (.0005, .0005),
        'severe': (.002, .003),
        'supersevere': (.005, .010)}
ORDERS = ('carried_before_fill', 'new_after_fill')
PRIORS = {
    'BULL': np.array([.65, .20, .10, .05]),
    'BEAR': np.array([.20, .05, .45, .30]),
    'CHOP': np.array([.35, .15, .40, .10]),
    'STRESS': np.array([.10, .05, .15, .70]),
}

def vector(x):
    a = np.asarray(x, dtype=np.float64)
    if a.shape != (4,) or not np.isfinite(a).all():
        raise ValueError('AK_VECTOR')
    return a

class AKAllocator:
    def __init__(self):
        self.history = deque(maxlen=LOOKBACK)
        self.inventory = np.zeros((4, 4))
        self.costs = np.zeros(4)
        self.target = np.zeros(4)
        self.last_state = 'CHOP'
        self.epochs = 0

    def observe(self, lr, funding, event):
        lr, funding, event = map(vector, (lr, funding, event))
        if not np.isin(event, (0., 1.)).all():
            raise ValueError('AK_EVENT')
        net = self.inventory @ (lr - funding * event) - self.costs
        self.history.append(net)
        self.costs[:] = 0.

    def decide(self, sleeves, regime, t):
        s = np.asarray(sleeves, dtype=np.float64)
        if s.shape != (4, 4) or not np.isfinite(s).all():
            raise ValueError('AK_SLEEVES')
        if regime not in PRIORS:
            raise ValueError('AK_REGIME')
        # Do not churn positions at every hourly close.
        if t % WEEK != 0 and regime == self.last_state:
            return self.target.copy(), False
        w = PRIORS[regime].copy()
        scale = 1.
        if len(self.history) == LOOKBACK:
            h = np.asarray(self.history)
            # Paper evidence net of a full-week cost allowance, not lookahead.
            scores = 3. * (np.sum(h, axis=0) -
                           .0025 * np.abs(s - self.inventory).sum(axis=1))
            scores -= scores.max()
            w *= np.exp(np.clip(scores, -40., 0.))
            w /= w.sum()
            p = h @ w
            edge = float(p.mean())
            variance = max(float(p.var()), 1e-6)
            scale += max(0., .5 * edge / variance)
        desired = scale * (w @ s)
        if not np.isfinite(desired).all():
            raise ValueError('AK_TARGET')
        self.costs = .0025 * np.abs(s - self.inventory).sum(axis=1)
        self.inventory = s.copy()
        self.target = desired.copy()
        self.last_state = regime
        self.epochs += 1
        return desired.copy(), True

def risk_history(opening, high, low, rate, event, quote, t):
    if t < 2016:
        raise ValueError('AK_WARMUP')
    # Historical arrays are sliced at t: never use current intrabar high/low.
    down = np.maximum(.40, np.max(1. - low[t - 336:t] /
                                    opening[t - 336:t], axis=0))
    up = np.maximum(.65, np.max(high[t - 336:t] /
                                opening[t - 336:t] - 1., axis=0))
    funding = np.maximum(.0005, 3. * np.max(
        np.abs(rate[t - 672:t] * event[t - 672:t]), axis=0))
    min_quote = np.min(quote[t - 336:t], axis=0)
    return down, up, funding, min_quote

def govern(cash, old, prev_close, opening, weights, rebalance,
           down, up, funding_bound, prior_quote, min_quote,
           fee_mode='base', funding_order='carried_before_fill'):
    old, prev_close, opening, weights, down, up, f, q, qmin = map(
        vector, (old, prev_close, opening, weights, down, up,
                 funding_bound, prior_quote, min_quote))
    if fee_mode not in FEES or funding_order not in ORDERS:
        raise ValueError('AK_COST_MODE')
    if (cash <= 0 or np.any(opening <= 0) or np.any(prev_close <= 0)
        or np.any(down < 0) or np.any(down >= 1) or np.any(up < 0)
        or np.any(f < 0) or np.any(q < 0) or np.any(qmin < 0)):
        raise ValueError('AK_BAD_OPEN')
    cash_open = float(cash + old @ (opening - prev_close))
    if cash_open <= 0:
        raise ValueError('AK_REAL_GAP_INSOLVENCY')
    fee, slip = FEES[fee_mode]
    friction = fee + slip
    max_inventory = SHARE * qmin / (opening * EXIT_FRICTION_MULTIPLIER)
    max_delta = SHARE * q / opening
    desired = weights * cash_open / opening if rebalance else old.copy()
    desired = np.clip(desired, -max_inventory, max_inventory)
    desired = np.clip(desired, old - max_delta, old + max_delta)

    def safe(n):
        turnover = float(np.sum(np.abs(n - old) * opening))
        payer = old if funding_order == 'carried_before_fill' else n
        cost = friction * turnover
        reserve = FUNDING_RESERVE_HOURS * float(
            np.sum(np.abs(payer * opening) * f))
        after = cash_open - cost - reserve
        notionals = np.abs(n * opening)
        worst_loss = float(np.sum(np.where(n >= 0, notionals * down,
                                         notionals * up)))
        stressed_gross = float(np.sum(notionals * (1. + up)))
        remaining = after - worst_loss - (
            EXIT_FRICTION_MULTIPLIER * friction * stressed_gross)
        return bool(after > 0 and remaining >= max(
            FLOOR * cash_open, MAINTENANCE * stressed_gross) - 1e-8)

    if safe(desired):
        return desired
    if safe(old):
        anchor = old
    else:
        # Carried inventory can only be reduced after the actual opening gap.
        # If liquidity prevents an executable safe reduction, reject.
        anchor = np.clip(np.zeros(4), old - max_delta, old + max_delta)
        if not safe(anchor):
            raise ValueError('AK_CARRIED_NO_SAFE_OPEN_EXIT')
    if not safe(anchor):
        raise ValueError('AK_NO_SAFE_ANCHOR')
    lo, hi = 0., 1.
    for _ in range(34):
        mid = .5 * (lo + hi)
        if safe(anchor + mid * (desired - anchor)):
            lo = mid
        else:
            hi = mid
    return anchor + lo * (desired - anchor)

if __name__ == '__main__':
    a = AKAllocator()
    s = np.eye(4)
    for t in range(LOOKBACK + 1):
        a.observe(np.array([.0002, .0001, 0., -.0001]),
                  np.zeros(4), np.zeros(4))
        x, change = a.decide(s, 'BULL', t)
        assert np.isfinite(x).all()
    p = np.ones(4) * 100.
    n = govern(10000., np.zeros(4), p, p, np.array([.5, .2, .1, .1]),
               True, np.full(4, .4), np.full(4, .65),
               np.full(4, .0005), np.full(4, 1e9), np.full(4, 1e9))
    assert np.isfinite(n).all()
    print('AK_ALLOCATOR_GOVERNOR_STATIC_PASS')
