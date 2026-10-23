#!/usr/bin/env python3
"""V98 Independent AH1240 causal 96h three-state regime router; source only."""
from __future__ import annotations
import numpy as np

STATES = ('TREND', 'DISPERSION', 'HAZARD')
LOOKBACK = 96

def ah_regime_router(close, native_rate, funding_event):
    c, r, e = map(lambda x: np.asarray(x, dtype=float),
                  (close, native_rate, funding_event))
    if (c.ndim != 2 or c.shape[1] != 4 or r.shape != c.shape
        or e.shape != c.shape or not np.isfinite(c).all()
        or not np.isfinite(r).all() or not np.isfinite(e).all()
        or np.any(c <= 0) or not np.isin(e, (0., 1.)).all()):
        raise ValueError('AH1240_GEOMETRY')
    n = len(c)
    states = np.full(n, 'TREND', dtype='<U10')
    breadth = np.zeros(n)
    dispersion = np.zeros(n)
    skew = np.zeros(n)
    market24 = np.zeros(n)
    lr = np.diff(np.log(c), axis=0)
    for t in range(LOOKBACK, n):
        x = lr[t-LOOKBACK:t]
        m = x.mean(axis=1)
        mu = float(m.mean())
        sigma = max(float(np.sqrt(np.mean((m-mu)**2))), 1e-4)
        k = float(np.mean(((m-mu)/sigma)**3))
        d = float(np.std(x.sum(axis=0)))
        m24 = float(m[-24:].sum())
        rates = r[t-LOOKBACK+1:t+1] * e[t-LOOKBACK+1:t+1]
        nz = rates[rates != 0]
        b = float(np.mean(nz > 0)) if len(nz) else 0.
        skew[t], dispersion[t], market24[t], breadth[t] = k, d, m24, b
        if m24 < -.08 and k < -.5:
            states[t] = 'HAZARD'
        elif d > .06 and abs(float(m.sum())) < .06:
            states[t] = 'DISPERSION'
    return {'state':states, 'funding_breadth':breadth,
            'dispersion':dispersion, 'market_skew':skew,
            'market_24h':market24}
