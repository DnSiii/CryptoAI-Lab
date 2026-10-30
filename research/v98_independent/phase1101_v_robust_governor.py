#!/usr/bin/env python3
"""V portfolio-first 16-corner max-feasible scale, pre-economic and t-1-only."""
from __future__ import annotations
import itertools
import numpy as np

N=4
ASSET_CAP=.45
NET_CAP=.75
GROSS_CAP=1.35
EQUITY_FLOOR=.25
FEE=.002
SLIPPAGE=.002
ITERATIONS=32

def _inputs(weights,prevclose,down,up,prior_funding_max):
    w,p,d,h,f=[np.asarray(x,dtype=float) for x in
               (weights,prevclose,down,up,prior_funding_max)]
    if (any(x.shape!=(N,) or not np.isfinite(x).all() for x in (w,p,d,h,f)) or
        (p<=0).any() or (d<0).any() or (d>=1).any() or (h<0).any() or
        (f<0).any()):
        raise ValueError('V_GOVERNOR_INVALID_PRIOR_INPUT')
    return w,p,d,h,f

def all_corners_feasible(weights,prevclose,down,up,prior_funding_max):
    """16 stressed equity/concentration corners; prior inputs only."""
    w,p,d,h,f=_inputs(weights,prevclose,down,up,prior_funding_max)
    cost=(FEE+SLIPPAGE)*float(np.abs(w).sum())
    reserve=float(np.sum(np.abs(w)*f*(1+h)))
    cash=1.-float(w.sum())-cost
    for bits in itertools.product((False,True),repeat=N):
        factor=np.where(bits,1+h,1-d)
        exposure=w*factor
        equity=cash+float(exposure.sum())-reserve
        if (not np.isfinite(equity) or equity<EQUITY_FLOOR or
            np.abs(exposure).max()>ASSET_CAP*equity+1e-12 or
            np.abs(exposure).sum()>GROSS_CAP*equity+1e-12 or
            abs(exposure.sum())>NET_CAP*equity+1e-12):
            return False
    return True

def max_feasible_weights(raw,prevclose,down,up,prior_funding_max):
    """Maximize common positive scale under ALL corners, not minimum risk.

    Exactly 32 bisections; check the 6-decimal quantized candidate at each
    iteration to avoid mixed-sign rounding creating a false survival.
    """
    w,p,d,h,f=_inputs(raw,prevclose,down,up,prior_funding_max)
    if np.all(w==0):return np.zeros(N)
    lo,hi=0.,1.
    for _ in range(ITERATIONS):
        mid=(lo+hi)/2.
        candidate=np.trunc(mid*w*1e6)/1e6
        if all_corners_feasible(candidate,p,d,h,f):lo=mid
        else:hi=mid
    out=np.trunc(lo*w*1e6)/1e6
    if not all_corners_feasible(out,p,d,h,f):
        raise AssertionError('V_GOVERNOR_SERIALIZATION_BREACH')
    return out
