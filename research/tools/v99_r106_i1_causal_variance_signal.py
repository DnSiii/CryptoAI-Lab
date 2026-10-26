"""Preregistered I1 t-1 variance-premium signals from ORIGINAL TRAIN spot/DVOL.

Research-only causal input to a future complete native options engine.
NO options positions, fills, economic ROI, promotion or orders.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, HOURS, FOLD_EDGES
from research.tools.v99_r106_e1_spot_engine import load_original_spot
from research.tools.v99_r106_h1_dvol_spot_engine import load_original_dvol
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_variance_premium import classify_regime

PREREG_COMMIT = "ce965d4b0feaaa713ee39dd70fc249d1e9e57b9e"
ASSETS = ("BTC", "ETH")
TRAILING_HOURS = 720
FLAGS = dict(economic_train_executed=False, fills_authenticated=False,
             native_fees_authenticated=False, native_margin_authenticated=False,
             validation_opened=False, holdout_opened=False,
             orders_enabled=False, promotion_authorized=False)


def evaluate(prices, weekly):
    if len(prices) != 2 or any(len(p) != HOURS for p in prices):
        raise ValueError("NOT_COMPLETE_ORIGINAL_TRAIN_SPOT_GRID")
    dates = eligible()
    if len(dates) != 91:
        raise ValueError("FROZEN_MATURITY_SCHEDULE_CHANGED")
    rows = []
    counts = {str(f): {a: {"positive": 0, "negative": 0, "no_history": 0}
                       for a in ASSETS} for f in range(1, 6)}
    for d in dates:
        t = int(d.timestamp() * 1000)
        if not START < t < END or (t-START) % HOUR:
            raise ValueError("OUT_OF_TRAIN_DECISION")
        i = (t-START)//HOUR
        fold = next((f for f in range(1, 6) if FOLD_EDGES[f-1] <= t < FOLD_EDGES[f]), None)
        if fold is None:
            raise ValueError("OUT_OF_PREREG_FOLD")
        regime = classify_regime(t, prices[0]) if i >= 889 else "insufficient_lag"
        for asset_idx, asset in enumerate(ASSETS):
            dvol = weekly.get((t, asset))
            if dvol is None or not math.isfinite(dvol) or dvol <= 0:
                raise ValueError("MISSING_CAUSALLY_CLOSED_ORIGINAL_DVOL")
            implied = (dvol/100.0)**2 * (30.0/365.0)
            if i < TRAILING_HOURS+1:
                rv, signal, bucket = None, "NO_30D_HISTORY", "no_history"
                start_ms, end_ms = None, None
            else:
                p = prices[asset_idx]
                rv = math.fsum(math.log(p[j]/p[j-1])**2
                               for j in range(i-TRAILING_HOURS, i))
                if not math.isfinite(rv) or rv < 0:
                    raise ValueError("INVALID_CAUSAL_TRAILING_VARIANCE")
                signal = ("POSITIVE_EX_ANTE_PREMIUM" if implied > rv else "NO_PREMIUM")
                bucket = "positive" if implied > rv else "negative"
                start_ms = START+(i-TRAILING_HOURS-1)*HOUR
                end_ms = START+(i-1)*HOUR
                if end_ms >= t:
                    raise ValueError("FUTURE_SPOT_LEAK")
            counts[str(fold)][asset][bucket] += 1
            rows.append(dict(decision_ms=t, decision_utc=d.isoformat(),
                             asset=asset, fold=fold, regime=regime,
                             dvol_percent=dvol, implied_var_30d=implied,
                             trailing_rv_30d=rv, trailing_first_price_ms=start_ms,
                             trailing_last_price_ms=end_ms, signal=signal))
    if len(rows) != 182:
        raise ValueError("INCOMPLETE_91_X_2_CAUSAL_SIGNAL_GRID")
    return dict(schema="V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1",
                status="ORIGINAL_CAUSAL_SIGNAL_ONLY_OPTIONS_ECONOMICS_BLOCKED",
                preregistration_commit=PREREG_COMMIT,
                source_okx_run=40019588739, source_dvol_run=40072202459,
                train_start_ms=START, train_end_exclusive_ms=END,
                eligible_weeks=91, right_censored_weeks=3,
                observations=len(rows), trailing_hours=TRAILING_HOURS,
                source_original=True, structural_only=True,
                counts=counts, rows=rows, **FLAGS)


def main(spot_root, dvol_root, out_dir):
    prices = load_original_spot(spot_root)
    weekly = load_original_dvol(dvol_root)
    result = evaluate(prices, weekly)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out/"i1_causal_signal.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n",
        encoding="utf-8")
    summary = {"status": result["status"], "observations": result["observations"],
               "counts": result["counts"], "economic_train_executed": False,
               "promotion_authorized": False}
    print(json.dumps(summary, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_causal_variance_signal OKX_ROOT DVOL_ROOT OUT")
    main(*sys.argv[1:])
