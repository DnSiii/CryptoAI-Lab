#!/usr/bin/env python3
"""V98 Phase1002: NEW source-only exact-LP opening Risk Governor candidate.

Never replaces frozen Phase915. Sell-only, causal t-1 volume, fee-inclusive.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linprog

ASSET_CAP = .70
GROSS_CAP = 1.75
PARTICIPATION = .05


def repair_open_lp(cash, units, opening, prev_quote, fee):
    """Minimize opening sell USD subject to hard post-fee caps; fail closed."""
    u = np.asarray(units, dtype=float).copy()
    p = np.asarray(opening, dtype=float)
    q = np.asarray(prev_quote, dtype=float)
    if any(a.shape != (4,) for a in (u,p,q)):
        raise ValueError("CLEAN4_SHAPE_REQUIRED")
    if not all(np.isfinite(a).all() for a in (u,p,q)) or (u<0).any() or (p<=0).any() or (q<0).any():
        raise ValueError("NONCAUSAL_OR_INVALID_INPUT")
    if not math.isfinite(cash) or not math.isfinite(fee) or not 0<=fee<=.02:
        raise ValueError("INVALID_CASH_OR_FEE")
    v = u*p
    eq = float(cash + v.sum())
    sold = np.zeros(4, dtype=float)
    if not math.isfinite(eq) or eq<=0:
        return float(cash), u, sold, False
    gross = float(v.sum())
    if gross<=GROSS_CAP*eq and np.all(v<=ASSET_CAP*eq):
        return float(cash), u, sold, True
    # Normalize all inequalities by pre-repair equity to stabilize HiGHS.
    x = v/eq
    bnd = np.minimum(v, PARTICIPATION*q)/eq
    a = [[-(1-GROSS_CAP*fee)]*4]
    rhs = [GROSS_CAP - float(x.sum())]
    for j in range(4):
        row = [ASSET_CAP*fee]*4
        row[j] -= 1.
        a.append(row)
        rhs.append(ASSET_CAP - float(x[j]))
    result = linprog(
        c=np.ones(4), A_ub=np.asarray(a), b_ub=np.asarray(rhs),
        bounds=[(0.,float(b)) for b in bnd], method="highs",
        options={"primal_feasibility_tolerance":1e-9,
                 "dual_feasibility_tolerance":1e-9},
    )
    if not result.success or result.x is None or not np.isfinite(result.x).all():
        return float(cash), u, sold, False
    if (result.x < -1e-10).any() or (result.x > bnd+1e-10).any():
        return float(cash), u, sold, False
    sold = result.x*eq
    post = v-sold
    post_cash = float(cash + (1-fee)*sold.sum())
    post_eq = post_cash + float(post.sum())
    tol = 1e-8*eq
    if (post_eq<=0 or (sold< -tol).any() or
        (sold>np.minimum(v,PARTICIPATION*q)+tol).any() or
        (post< -tol).any() or float(post.sum())>GROSS_CAP*post_eq+tol or
        (post>ASSET_CAP*post_eq+tol).any()):
        return float(cash), u, np.zeros(4), False
    u -= sold/p
    if (u< -tol).any():
        return float(cash), np.asarray(units,dtype=float).copy(), np.zeros(4), False
    u = np.maximum(u,0.)
    return post_cash, u, sold, True
