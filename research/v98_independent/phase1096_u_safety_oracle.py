#!/usr/bin/env python3
"""V98 U pre-economic ex-post safety oracle; never used to choose signals."""
import numpy as np

N = 4

def require_full_stop_coverage(bracket, actual_units, tolerance=1e-9):
    u = np.asarray(actual_units, float)
    side = np.asarray(bracket['side'])
    qty = np.asarray(bracket['stop_qty'], float)
    if (u.shape != (N,) or side.shape != (N,) or qty.shape != (N,) or
        not np.isfinite(u).all() or not np.isfinite(qty).all() or
        (qty < 0).any() or not np.isin(side, (-1, 0, 1)).all()):
        raise ValueError('U_PROTECTION_GEOMETRY')
    if np.any((np.abs(u) > tolerance) & (np.sign(u) != side)):
        return 'U_UNPROTECTED_ENTRY_SIGN'
    if np.any(np.abs(u) > qty + tolerance):
        return 'U_UNPROTECTED_STOP_QUANTITY'
    return None

def realized_funding_buffer(carried, after_entry, rates, events, marks):
    """Conservative positive debit over both preregistered funding orders.

    t event values are for ex-post path survival AUDIT, not trading decisions.
    """
    a, b, r = (np.asarray(x, float) for x in (carried, after_entry, rates))
    ev = np.asarray(events)
    mk = np.asarray(marks, float)
    if (any(x.shape != (N,) for x in (a, b, r, ev)) or
        mk.shape != (N, 2) or ev.dtype != np.dtype(bool) or
        not np.isfinite(a).all() or not np.isfinite(b).all() or
        not np.isfinite(r).all() or (r[~ev] != 0).any() or
        not np.isfinite(mk[ev]).all() or (mk[ev] <= 0).any() or
        (mk[ev, 0] > mk[ev, 1]).any() or np.isfinite(mk[~ev]).any()):
        raise ValueError('U_FUNDING_AUDIT_GEOMETRY')
    def debit(units):
        signed = units[ev] * r[ev]
        adverse = np.where(signed >= 0, mk[ev, 1], mk[ev, 0])
        return float(np.maximum(signed * adverse, 0).sum())
    return max(debit(a), debit(b))
