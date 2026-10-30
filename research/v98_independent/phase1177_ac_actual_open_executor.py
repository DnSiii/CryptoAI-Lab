#!/usr/bin/env python3
"""V98 AC t+1 actual-open signed self-financing executor; synthetic only."""
from __future__ import annotations
import numpy as np
from phase1176_ac_discrete_allocator import (
    CORNERS, ASSET_CAP, GROSS_CAP, NET_CAP, FLOOR, ORDER_PARTICIPATION,
    SLIPPAGE, allocate, vector)

FEES = {'base': .0007, 'severe': .0012, 'supersevere': .002}
ORDERS = ('carried_before_fill', 'new_after_fill')


def funding_cash(units, rate, bounds, events):
    u, r = vector(units), vector(rate)
    b = np.asarray(bounds, float)
    ev = np.asarray(events, bool)
    if (b.shape != (4, 2) or ev.shape != (4,)
            or not np.isfinite(b[ev]).all() or np.any(b[ev, 0] <= 0)
            or np.any(b[ev, 1] < b[ev, 0])):
        raise ValueError('AC1177_NATIVE_SIGNED_MARK')
    mark = np.where(u * r >= 0, b[:, 1], b[:, 0])
    return np.where(ev, -u * r * mark, 0.)


def intrabar(cash, units, low, opening, high, prior_equity, debit):
    u = vector(units)
    p = np.stack([vector(low), vector(opening), vector(high)])
    if np.any(p <= 0) or not np.isfinite(cash + prior_equity + debit) or prior_equity <= 0 or debit < 0:
        raise ValueError('AC1177_INTRABAR_SOURCE')
    ex = p[CORNERS, np.arange(4)] * u
    eq = cash + ex.sum(axis=1) - debit
    if np.any(eq < FLOOR * prior_equity - 1e-9):
        return 'AC1177_EQUITY_FLOOR'
    if np.any(np.abs(ex) > ASSET_CAP * eq[:, None] + 1e-9):
        return 'AC1177_ASSET_CAP'
    if np.any(np.abs(ex).sum(axis=1) > GROSS_CAP * eq + 1e-9):
        return 'AC1177_GROSS_CAP'
    if np.any(np.abs(ex.sum(axis=1)) > NET_CAP * eq + 1e-9):
        return 'AC1177_NET_CAP'
    return None


def execute_hour(prior, opening, high, low, closing, cash, old_units,
                 scores, cov24, down, up, funding_bound, prior_quote, min336_quote,
                 *, fee, funding_rate, mark_bounds, funding_event,
                 order='carried_before_fill', rebalance=True):
    p, o, h, l, c, old, d, u, q = map(vector,
        (prior, opening, high, low, closing, old_units, down, up, prior_quote))
    if (fee not in FEES.values() or order not in ORDERS or not np.isfinite(cash)
            or np.any(p <= 0) or np.any(o <= 0) or np.any(l <= 0)
            or np.any(h < np.maximum(o, c)) or np.any(l > np.minimum(o, c))):
        raise ValueError('AC1177_SOURCE_OR_COST')
    equity = float(cash + np.dot(old, p))
    if equity <= 0:
        return {'ok': False, 'reason': 'AC1177_PRIOR_EQUITY'}
    stop = p * np.where(old >= 0, 1 - d, 1 + u)
    gap = bool(np.any(((old > 1e-12) & (o <= stop)) |
                      ((old < -1e-12) & (o >= stop))))
    if gap:
        # Cancel all entries. No imaginary stop or reduce-only fill.
        target = old.copy()
    elif rebalance:
        try:
            target = allocate(scores, cov24, old, p, equity, d, u,
                              funding_bound, q, min336_quote)
        except ValueError as exc:
            return {'ok': False, 'reason': str(exc)}
    else:
        target = old.copy()
    delta = target - old
    fill = o * (1 + np.sign(delta) * SLIPPAGE)
    turnover = float(np.sum(np.abs(delta) * fill))
    if np.any(np.abs(delta) * fill > ORDER_PARTICIPATION * q + 1e-9):
        return {'ok': False, 'reason': 'AC1177_UNEXECUTABLE_OPEN_ORDER'}
    balance = float(cash - np.dot(delta, fill) - fee * turnover)
    carried = old if order == 'carried_before_fill' else target
    flows = funding_cash(carried, funding_rate, mark_bounds, funding_event)
    if gap:
        flows = np.minimum(flows, 0.)
    debit = float(np.maximum(-flows, 0.).sum())
    reason = intrabar(balance, target, l, o, h, equity, debit)
    if reason:
        return {'ok': False, 'reason': 'AC1177_GAP_UNEXECUTABLE' if gap else reason}
    balance += float(flows.sum())
    nav = float(balance + np.dot(target, c))
    if not np.isfinite(nav) or nav <= 0:
        return {'ok': False, 'reason': 'AC1177_FINAL_EQUITY'}
    return {'ok': True, 'reason': None, 'units': target, 'cash': balance,
            'equity': nav, 'turnover': turnover, 'fees': fee * turnover,
            'funding_cash_delta': float(flows.sum()), 'gap': gap,
            'self_financing': True, 'synthetic_only': True}
