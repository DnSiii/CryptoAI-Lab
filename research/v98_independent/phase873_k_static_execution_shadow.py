#!/usr/bin/env python3
"""V98 Independent Phase873: static-NAV K capacity shadow, strictly NO PnL.

Preregistered in branch V98 at commit 44bd7aa0562be987eb800d0d203f95fcb817981e.
All t trades use K signal at close(t-1) and volume from CLOSED bar t-1.
Fixed notional NAV, no returns, no mark, no funding, no transaction costs.
This is a capacity/tracking feasibility bound, NOT a trading backtest.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, PATHS, pinned_training_frames, compose_k

ASSET_CAP = .70
GROSS_CAP = 1.75
PARTICIPATION = .05
CAPITALS = (1_000_000, 10_000_000)
EXPECTED_FULL = '2babec819c91a54cf2e3914724a63c2ae7ef5e289b4c173163c59daf9bd9a3a0'


def _longest_run(flags):
    best = cur = 0
    for v in flags:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def simulate_static(targets, quote_volume, capital, participation=PARTICIPATION, return_trace=False):
    """Trade inventory against changing targets; NEVER use prices or PnL.

    Inputs: targets[t] is known only after close(t); quote_volume[t] is
    likewise available only after close(t). Trades for target[t-1] occur
    at open(t), constrained by quote_volume[t-1].
    """
    w = np.asarray(targets, dtype=np.float64)
    q = np.asarray(quote_volume, dtype=np.float64)
    if w.ndim != 2 or w.shape[1] != 4 or q.shape != w.shape or len(w) < 3:
        raise ValueError('four aligned Clean-4 assets and at least 3 hours required')
    if (not np.isfinite(w).all() or not np.isfinite(q).all() or
        (w < -1e-12).any() or (q < 0).any() or
        (w > ASSET_CAP + 1e-9).any() or (w.sum(axis=1) > GROSS_CAP + 1e-9).any()):
        raise ValueError('invalid frozen target or quote volume')
    if not np.isfinite(capital) or capital <= 0 or not 0 < participation <= 1:
        raise ValueError('invalid fixed NAV or participation')
    inv = np.zeros(4, dtype=float)
    executed = 0.
    desired = 0.
    cap_exhausted_orders = 0
    zero_liquidity_orders = 0
    gross_max = 0.
    asset_max = 0.
    prev_gap = np.zeros(4)
    superseded = 0
    gap_series = []
    gross_series = []
    cap_series = []
    for t in range(1, len(w)):
        target = np.maximum(w[t-1], 0) * capital
        budget = participation * q[t-1]
        original_gap = target - inv
        desired += np.abs(original_gap).sum()
        superseded += int(np.sum((prev_gap * original_gap < -1e-9)))
        zero_liquidity_orders += int(np.sum((budget <= 0) & (np.abs(original_gap) > 1e-7)))
        # Sell first. Sells cannot be reused as fresh per-asset volume capacity.
        sell = np.minimum(np.maximum(inv - target, 0), budget)
        inv -= sell
        executed += sell.sum()
        # Buy subject to remaining asset capacity and total gross ceiling.
        buy_request = np.maximum(target - inv, 0)
        buy_budget = np.minimum(buy_request, budget)
        remaining_gross = max(0., GROSS_CAP * capital - inv.sum())
        if buy_budget.sum() > remaining_gross:
            buy_budget *= remaining_gross / buy_budget.sum()
        inv += buy_budget
        executed += buy_budget.sum()
        cap_exhausted_orders += int(np.sum((np.abs(target - inv) > 1e-7) &
                                           (np.abs(original_gap) > budget + 1e-7)))
        if (inv < -1e-6).any() or inv.max() > ASSET_CAP * capital + 1e-5 or inv.sum() > GROSS_CAP * capital + 1e-5:
            raise AssertionError('static-capital governor violated')
        prev_gap = target - inv
        gap_series.append(np.abs(prev_gap).sum() / capital)
        gross_series.append(inv.sum() / capital)
        cap_series.append(inv.max() / capital)
        gross_max = max(gross_max, gross_series[-1])
        asset_max = max(asset_max, cap_series[-1])
    gaps = np.array(gap_series)
    gflag = gaps > .10 + 1e-12
    report = {
        'hours': len(gaps),
        'capital_usd': int(capital),
        'desired_gap_notional_usd': float(desired),
        'filled_notional_usd': float(executed),
        'mean_l1_tracking_gap_nav': float(gaps.mean()),
        'p95_l1_tracking_gap_nav': float(np.quantile(gaps, .95)),
        'max_l1_tracking_gap_nav': float(gaps.max()),
        'hours_l1_gap_above_10pct_nav': int(gflag.sum()),
        'longest_consecutive_hours_gap_above_10pct_nav': _longest_run(gflag),
        'hours_l1_gap_above_10pct_nav_in_24h_streaks': int(sum(1 for i in range(23,len(gflag)) if gflag[i-23:i+1].all())),
        'hours_l1_gap_above_10pct_nav_in_168h_streaks': int(sum(1 for i in range(167,len(gflag)) if gflag[i-167:i+1].all())),
        'hours_unfilled_any': int((gaps > 1e-9).sum()),
        'superseded_pending_asset_gaps': superseded,
        'orders_exhausting_prior_closed_hour_capacity': cap_exhausted_orders,
        'orders_with_zero_prior_closed_hour_liquidity': zero_liquidity_orders,
        'max_static_gross_weight': float(gross_max),
        'max_static_asset_weight': float(asset_max),
        'terminal_l1_tracking_gap_nav': float(gaps[-1]),
        'terminal_inventory_weights': [float(v) for v in inv / capital],
    }
    if return_trace:
        return report, {'tracking_l1_nav': gaps, 'gross_nav': np.array(gross_series),
                        'max_asset_nav': np.array(cap_series)}
    return report


def run(root):
    root = Path(root)
    close, high = pinned_training_frames(root)
    paths = compose_k(close, high)
    assert hashlib.sha256(paths['K_full'].to_csv(float_format='%.12g').encode()).hexdigest() == EXPECTED_FULL
    q = np.stack([pd.read_csv(root / f'{a}_1h.csv',usecols=['quote_volume']).quote_volume.to_numpy(float)
                  for a in ASSETS],axis=1)
    output = {'phase':873, 'source_only':True, 'static_nav_no_pnl':True,
              'economic_selection':False,'promotion_eligible':False,
              'external_benchmarks_used':False,'validation_2025_read':False,
              'historical_pnl_computed':False,
              'frozen_k_full_sha256':EXPECTED_FULL, 'paths':{}}
    for name in PATHS:
        output['paths'][name] = {str(c):simulate_static(paths[name].to_numpy(float),q,c) for c in CAPITALS}
    return output


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    result = run(here/'phase243_clean4_canonical')
    (here/'phase873_k_static_execution_shadow_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
