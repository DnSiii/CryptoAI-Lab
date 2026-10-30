#!/usr/bin/env python3
"""V98 Independent Phase243 — independent hourly trade-side conservation gate.

DATA_ONLY, no strategy, no holdout, no network. Every trade is either
aggressor-buy or aggressor-sell: total quote/base minus taker-buy quote/base
must describe trades executed within that candle's low/high. This invariant
is not implied by checking total and buy-side VWAPs independently.
"""
from __future__ import annotations
import numpy as np


def audit_trade_side_conservation(low, high, base, quote, taker_base, taker_quote):
    """Fail closed on impossible hourly seller residuals; tolerate CSV rounding.

    A conservative quote tolerance (1e-6 times quote notional, minimum 1)
    avoids falsely rejecting small residuals after subtraction of large
    numbers. This gate does not certify exchange authenticity or price alpha.
    """
    fields = [np.asarray(v, dtype=np.float64) for v in
              (low, high, base, quote, taker_base, taker_quote)]
    if not fields or fields[0].ndim != 1 or len(fields[0]) == 0 or any(
            f.ndim != 1 or f.shape != fields[0].shape for f in fields):
        raise ValueError('seller conservation: incompatible or empty 1d bar arrays')
    lo, hi, v, q, tb, tq = fields
    if (not all(np.isfinite(x).all() for x in fields) or
        np.any(lo <= 0) or np.any(hi < lo) or
        np.any(np.minimum.reduce([v, q, tb, tq]) < 0)):
        raise ValueError('seller conservation: nonfinite or invalid candle inputs')
    total_tol = 1e-6*np.maximum(1.,q)
    buy_tol = 1e-6*np.maximum(1.,tq)
    if (np.any(q < v*lo-total_tol) or np.any(q > v*hi+total_tol) or
        np.any(tq < tb*lo-buy_tol) or np.any(tq > tb*hi+buy_tol)):
        raise ValueError('seller conservation: total or buyer VWAP outside candle')
    sell_v = v - tb
    sell_q = q - tq
    if (np.any(tb > v + 1e-6*np.maximum(1.,v)) or
        np.any(tq > q + total_tol) or
        np.any(sell_q < -total_tol) or
        np.any(sell_q < sell_v*lo-total_tol) or
        np.any(sell_q > sell_v*hi+total_tol)):
        raise ValueError('seller conservation: implied seller VWAP outside candle')
    return {'mode':'V98_PHASE243_TRADE_SIDE_CONSERVATION_DATA_ONLY',
            'checked_bars':int(len(v)), 'decision':'PASS_CONSERVATION_NOT_ALPHA'}
