#!/usr/bin/env python3
"""V98 Independent AG: atomic jointly feasible linear growth allocation (synthetic gate)."""
from __future__ import annotations
import itertools
import numpy as np
from scipy.optimize import linprog

CORNERS = np.asarray(list(itertools.product(range(3), repeat=4)), dtype=int)
ASSET_CAP = 0.36
GROSS_CAP = 0.90
EQUITY_FLOOR = 0.35
ORDER_SHARE = 0.003
EXIT_MULT = 2.2
COSTS = {'base': (0.0005, 0.0005),
         'severe': (0.002, 0.003),
         'supersevere': (0.005, 0.010)}


def vec(v, positive=False):
    x = np.asarray(v, dtype=float)
    if x.shape != (4,) or not np.all(np.isfinite(x)) or (positive and np.any(x < 0)):
        raise ValueError('AG1226_INVALID_VECTOR')
    return x


def corner_audit(z, old_z, equity, ratios, funding_bound, exit_cost, cost,
                 quote, quote_min, tol=1e-7):
    """Audit one *final* jointly netted portfolio under all 81 corners."""
    z, old_z = vec(z, True), vec(old_z, True)
    f, q, qmin = vec(funding_bound, True), vec(quote, True), vec(quote_min, True)
    if equity <= 0 or not np.isfinite(equity) or np.any(ratios <= 0):
        return False, 'BAD_EQUITY_OR_CORNER'
    turnover = np.abs(z - old_z)
    cash = equity - z.sum() - cost * turnover.sum()
    if cash < -tol:
        return False, 'NEGATIVE_CASH'
    if np.any(turnover > ORDER_SHARE*q + tol):
        return False, 'ORDER_CAPACITY'
    if np.any(EXIT_MULT*z*np.max(ratios, axis=0) >
              ORDER_SHARE*qmin + tol):
        return False, 'EXIT_RESERVE'
    exposure = ratios * z
    stress = cash + exposure.sum(axis=1) - (f+exit_cost)*z @ np.ones(4)
    if np.any(stress < EQUITY_FLOOR*equity - tol):
        return False, 'EQUITY_FLOOR'
    if np.any(exposure > ASSET_CAP*stress[:, None] + tol):
        return False, 'ASSET_CONCENTRATION'
    if np.any(exposure.sum(axis=1) > GROSS_CAP*stress + tol):
        return False, 'GROSS'
    return True, 'PASS'


def joint_plan(old_units, opening, cash, growth_mu, down, up,
               funding_bound, quote, quote_min, fee_mode='base'):
    """Solve one portfolio-wide net rebalance; no post-sell intermediate state."""
    old, p = vec(old_units, True), vec(opening)
    mu, d, u = vec(growth_mu), vec(down, True), vec(up, True)
    f, q, qmin = vec(funding_bound, True), vec(quote, True), vec(quote_min, True)
    if np.any(p <= 0) or np.any(d >= 1) or cash < 0 or fee_mode not in COSTS:
        raise ValueError('AG1226_BAD_INPUT')
    old_z = old*p
    equity = float(cash + old_z.sum())
    if equity <= 0:
        raise ValueError('AG1226_INSOLVENT')
    fee, slip = COSTS[fee_mode]
    cost = fee + slip
    exit_cost = cost
    ratios = np.stack([1-d, np.ones(4), 1+u])[CORNERS, np.arange(4)]
    A, b = [], []
    def add(a, bound):
        A.append(np.asarray(a, dtype=float))
        b.append(float(bound))
    # x=[4 final open notionals, 4 absolute netted traded notionals].
    for i in range(4):
        a = np.zeros(8); a[i] = 1; a[4+i] = -1
        add(a, old_z[i])
        a = np.zeros(8); a[i] = -1; a[4+i] = -1
        add(a, -old_z[i])
        a = np.zeros(8); a[i] = 1
        add(a, old_z[i] + ORDER_SHARE*q[i])
        a = np.zeros(8); a[i] = -1
        add(a, ORDER_SHARE*q[i] - old_z[i])
        a = np.zeros(8); a[i] = EXIT_MULT*(1+u[i])
        add(a, ORDER_SHARE*qmin[i])
    add(np.r_[np.ones(4), np.full(4, cost)], equity)  # real cash >=0
    for r in ratios:
        s = r-1-f-exit_cost
        # stress_equity = equity + s @ z - cost * turnover
        add(np.r_[-s, np.full(4, cost)], equity*(1-EQUITY_FLOOR))
        for i in range(4):
            a = -ASSET_CAP*s
            a = a.copy(); a[i] += r[i]
            add(np.r_[a, np.full(4, ASSET_CAP*cost)], ASSET_CAP*equity)
        add(np.r_[r-GROSS_CAP*s, np.full(4, GROSS_CAP*cost)],
            GROSS_CAP*equity)
    # Fixed linearized expected *net growth* utility; turnover is a real cost.
    # Forecast mu is causal; risk/tails are survival constraints, not objective.
    obj = np.r_[-mu/equity, np.full(4, cost/equity)]
    res = linprog(obj, A_ub=np.asarray(A), b_ub=np.asarray(b),
                  bounds=[(0, None)]*8, method='highs',
                  options={'primal_feasibility_tolerance':1e-8,
                           'dual_feasibility_tolerance':1e-8})
    if not res.success:
        raise ValueError('AG1226_NO_JOINT_FEASIBLE_PORTFOLIO_'+str(res.status))
    z = np.maximum(res.x[:4], 0.)
    ok, reason = corner_audit(z, old_z, equity, ratios, f, exit_cost,
                              cost, q, qmin, tol=2e-5)
    if not ok:
        raise ValueError('AG1226_POST_OPT_'+reason)
    delta = z-old_z
    turn = float(np.abs(delta).sum())
    after_cash = float(equity-z.sum()-cost*turn)
    if after_cash < -2e-5:
        raise ValueError('AG1226_NEGATIVE_CASH')
    return {'units': z/p, 'cash': max(0., after_cash),
            'turnover': turn, 'fees': fee*turn, 'slippage': slip*turn,
            'open_equity': equity, 'growth_utility': -float(res.fun),
            'posttrade_weights': z/equity, 'jointly_feasible': True}
