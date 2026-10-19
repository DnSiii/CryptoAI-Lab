#!/usr/bin/env python3
"""V98 Independent Phase620: source-free causal gross/asset close-drift governor.

No signals, external engines, historical PnL, holdout, 2026+ or funding.
At open(t), use only close(t-1) and open(t) weights.
"""
from __future__ import annotations
import numpy as np

GROSS_CAP = 1.45
ASSET_CAP = .70
TOL = 1e-12

def prior_close_guard(close_weights, gross_cap=GROSS_CAP, asset_cap=ASSET_CAP, tol=TOL):
    w = np.asarray(close_weights, dtype=float)
    if w.shape != (4,) or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('strict nonnegative finite four-asset close weights required')
    return bool(w.sum() > gross_cap + tol or w.max() > asset_cap + tol)

def proportional_open_repair(open_weights, gross_cap=GROSS_CAP, asset_cap=ASSET_CAP):
    w = np.asarray(open_weights, dtype=float)
    if w.shape != (4,) or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('strict nonnegative finite four-asset open weights required')
    if not (0 < asset_cap <= gross_cap and np.isfinite(gross_cap)):
        raise ValueError('invalid cap contract')
    gross = float(w.sum()); asset = float(w.max())
    scale = min(1.0, gross_cap / gross if gross else 1.0,
                asset_cap / asset if asset else 1.0)
    repaired = w * scale
    if repaired.sum() > gross_cap + 1e-10 or repaired.max() > asset_cap + 1e-10:
        raise ValueError('governor repair did not satisfy limits')
    return repaired
