#!/usr/bin/env python3
"""AC discrete actual-NAV growth allocator and 81-corner governor, synthetic-only.

All constants preregistered Phase1176 before historical system PnL.
The executor must separately implement t+1 actual open, funding and cash ledger.
"""
from __future__ import annotations
import itertools
import numpy as np

CORNERS = np.array(tuple(itertools.product(range(3), repeat=4)), dtype=np.int8)
ASSET_CAP = .40
GROSS_CAP = 1.20
NET_CAP = .60
FLOOR = .30
ORDER_PARTICIPATION = .004
ENTRY_STRESS_PARTICIPATION = .002
SLIPPAGE = .002
SUPERS_FEE = .002
HORIZON_HOURS = 24
MU_PER_SCORE = .003
STEP_QUOTE_FRACTION = .001
STEP_EQUITY_FRACTION = .05
PASSES = 4


def vector(x):
    a = np.asarray(x, dtype=np.float64)
    if a.shape != (4,) or not np.isfinite(a).all():
        raise ValueError('AC1176_VECTOR')
    return a


def feasible(new_units, old_units, price, equity, down, up, funding_bound,
             prior_quote, min336_quote):
    try:
        n, old, p, d, u, f, q, qmin = map(vector,
            (new_units, old_units, price, down, up, funding_bound,
             prior_quote, min336_quote))
    except ValueError:
        return False
    if (not np.isfinite(equity) or equity <= 0 or np.any(p <= 0)
            or np.any((d < 0) | (d >= 1)) or np.any(u < 0)
            or np.any(f < 0) or np.any(q < 0) or np.any(qmin < 0)):
        return False
    order = np.abs(n - old) * p * (1 + SLIPPAGE)
    if np.any(order > ORDER_PARTICIPATION * q + 1e-9):
        return False
    increase = np.abs(n) > np.abs(old) + 1e-12
    entry_reserve = np.abs(n) * p * (1 + u)
    if np.any(increase & (entry_reserve > ENTRY_STRESS_PARTICIPATION * qmin + 1e-9)):
        return False
    # Explicitly reserve two stressed exit capacities before increasing inventory.
    if np.any(increase & (2 * entry_reserve > ORDER_PARTICIPATION * qmin + 1e-9)):
        return False
    costs = (SLIPPAGE + SUPERS_FEE) * np.sum(np.abs(n - old) * p)
    funding = np.sum(np.abs(n * p) * f)
    prices = p * np.stack((1 - d, np.ones(4), 1 + u))[CORNERS, np.arange(4)]
    exposures = prices * n
    stressed_equity = equity + ((prices - p) * n).sum(axis=1) - costs - funding
    if np.any(stressed_equity < FLOOR * equity - 1e-9):
        return False
    if np.any(np.abs(exposures) > ASSET_CAP * stressed_equity[:, None] + 1e-9):
        return False
    if np.any(np.abs(exposures).sum(axis=1) > GROSS_CAP * stressed_equity + 1e-9):
        return False
    if np.any(np.abs(exposures.sum(axis=1)) > NET_CAP * stressed_equity + 1e-9):
        return False
    return True


def objective(units, old, price, equity, scores, cov24, funding_bound):
    w = vector(units) * vector(price) / equity
    mu = MU_PER_SCORE * vector(scores)
    covariance = np.asarray(cov24, dtype=float)
    gross = float(w @ mu - .5 * (w @ covariance @ w))
    costs = (SLIPPAGE + SUPERS_FEE) * np.abs((vector(units) - vector(old)) * price).sum() / equity
    adverse_funding = np.abs(w * vector(funding_bound)).sum()
    x = gross - costs - adverse_funding
    return float(np.log1p(x)) if x > -1 else -np.inf


def allocate(scores, cov24, old_units, price, equity, down, up,
             funding_bound, prior_quote, min336_quote):
    s = vector(scores)
    old, p, d, u, f, q, qmin = map(vector,
        (old_units, price, down, up, funding_bound, prior_quote, min336_quote))
    c = np.asarray(cov24, dtype=float)
    if (np.any(s != np.round(s)) or np.any(np.abs(s) > 4)
            or c.shape != (4, 4) or not np.isfinite(c).all()
            or not np.allclose(c, c.T, atol=1e-12, rtol=0)
            or np.linalg.eigvalsh(c).min() < -1e-10
            or not np.isfinite(equity) or equity <= 0):
        raise ValueError('AC1176_COV_SCORE_OR_EQUITY')
    gate = lambda x: feasible(x, old, p, equity, d, u, f, q, qmin)
    current = old.copy()
    if not gate(current):
        # Carried inventory cannot be silently liquidated. Try executable reductions.
        repaired = None
        for pct in range(99, -1, -1):
            candidate = old * (pct / 100)
            if gate(candidate):
                repaired = candidate
                break
        if repaired is None:
            raise ValueError('AC1176_UNEXECUTABLE_CARRIED_INVENTORY')
        current = repaired
    best = objective(current, old, p, equity, s, c, f)
    step = np.minimum(STEP_QUOTE_FRACTION * q, STEP_EQUITY_FRACTION * equity) / p
    for _ in range(PASSES):
        changed = False
        for j in range(4):
            winning = current
            winning_score = best
            for direction in (-1, 1):
                candidate = current.copy()
                candidate[j] += direction * step[j]
                if not gate(candidate):
                    continue
                score = objective(candidate, old, p, equity, s, c, f)
                if score > winning_score + 1e-12:
                    winning, winning_score = candidate, score
            if winning is not current:
                current, best, changed = winning, winning_score, True
        if not changed:
            break
    if not gate(current):
        raise ValueError('AC1176_FINAL_SURVIVAL')
    return current
