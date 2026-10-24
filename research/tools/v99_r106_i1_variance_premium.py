"""I1 preregistered variance-premium structural falsification. NO TRADES / NO PNL."""
from __future__ import annotations
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, HOURS, FOLD_EDGES
from research.tools.v99_r106_e1_spot_engine import load_original_spot
from research.tools.v99_r106_h1_dvol_spot_engine import load_original_dvol

WINDOW = 720
PREREG_COMMIT = "89a88e4a248e42e87e55d0a0ea4c61322d6ea222"
FLAGS = dict(promotion_authorized=False, validation_opened=False,
             holdout_opened=False, orders_enabled=False, paper_publication_authorized=False,
             native_fee_tier_authenticated=False, actual_account_fills_authenticated=False,
             trading_engine_evaluated=False, economic_backtest_executed=False)


def eligible_windows(weekly):
    times = sorted(set(t for t, c in weekly if c == "BTC") &
                   set(t for t, c in weekly if c == "ETH"))
    selected = []
    for fold, (a, b) in enumerate(zip(FOLD_EDGES, FOLD_EDGES[1:]), 1):
        next_allowed = a
        for t in times:
            if t < a or t >= b or t < next_allowed or t + WINDOW * HOUR >= b:
                continue
            if (t, "BTC") not in weekly or (t, "ETH") not in weekly:
                continue
            selected.append((fold, t))
            next_allowed = t + WINDOW * HOUR
    return selected


def classify_regime(t, btc):
    i = (t - START) // HOUR
    if i < 889:
        return "insufficient_lag"
    r30 = btc[i-1] / btc[i-721] - 1.0
    trend = "up" if r30 > 0.02 else ("down" if r30 < -0.02 else "flat")
    # Lagged rolling 7d BTC hourly volatility, same state definition as fixed R106 diagnostics.
    hourly = [math.log(btc[k]/btc[k-1]) for k in range(i-336, i)]
    vol = [statistics.pstdev(hourly[k-167:k+1]) for k in range(167, len(hourly))]
    if len(vol) < 169:
        return "insufficient_lag"
    return trend + "_" + ("high" if vol[-1] > statistics.median(vol[-169:-1]) else "low")


def evaluate(prices, weekly):
    if len(prices) != 2 or any(len(x) != HOURS for x in prices):
        raise ValueError("I1_BAD_TRAIN_GRID")
    selected = eligible_windows(weekly)
    rows = []
    for fold, t in selected:
        i = (t - START) // HOUR
        if i < 1 or i + WINDOW >= HOURS:
            raise ValueError("I1_OUT_OF_TRAIN_WINDOW")
        regime = classify_regime(t, prices[0])
        for c, asset in enumerate(("BTC", "ETH")):
            iv = weekly[(t, asset)]
            if not math.isfinite(iv) or iv <= 0:
                raise ValueError("I1_INVALID_DVOL")
            implied = (iv / 100.0) ** 2 * 30.0 / 365.0
            realized = math.fsum(math.log(prices[c][j] / prices[c][j-1]) ** 2
                                 for j in range(i+1, i+WINDOW+1))
            if not math.isfinite(realized) or realized < 0:
                raise ValueError("I1_BAD_REALIZED")
            rows.append(dict(fold=fold, decision_ms=t, asset=asset, dvol=iv,
                             implied_variance=implied, realized_variance=realized,
                             premium=implied-realized, premium_ratio=(implied-realized)/implied,
                             realized_to_implied=realized/implied, regime=regime))
    folds = {}
    for asset in ("BTC", "ETH"):
        per = []
        for f in range(1, 6):
            x = [r for r in rows if r["asset"] == asset and r["fold"] == f]
            v = [r["premium"] for r in x]
            per.append(dict(fold=f, windows=len(x),
                            mean_premium=statistics.mean(v) if v else None,
                            median_premium=statistics.median(v) if v else None,
                            min_premium=min(v) if v else None))
        x = [r for r in rows if r["asset"] == asset]
        positives = sorted((max(0.0, r["premium"]) for r in x), reverse=True)
        positive_sum = math.fsum(positives)
        folds[asset] = dict(folds=per, all_mean_premium=statistics.mean(r["premium"] for r in x) if x else None,
                            positive_folds=sum(p["mean_premium"] is not None and p["mean_premium"] > 0 for p in per),
                            worst_realized_to_implied=max((r["realized_to_implied"] for r in x), default=None),
                            top_two_positive_premium_share=(sum(positives[:2])/positive_sum if positive_sum else None))
    gates = {
        "two_nonoverlapping_windows_each_fold_both_assets": all(
            p["windows"] >= 2 for asset in folds.values() for p in asset["folds"]),
        "btc_at_least_four_positive_folds": folds["BTC"]["positive_folds"] >= 4,
        "eth_at_least_four_positive_folds": folds["ETH"]["positive_folds"] >= 4,
        "btc_all_mean_positive": folds["BTC"]["all_mean_premium"] is not None and folds["BTC"]["all_mean_premium"] > 0,
        "eth_all_mean_positive": folds["ETH"]["all_mean_premium"] is not None and folds["ETH"]["all_mean_premium"] > 0,
    }
    return rows, folds, gates


def main(spot_root, dvol_root, out_dir):
    prices = load_original_spot(spot_root)
    weekly = load_original_dvol(dvol_root)
    rows, folds, gates = evaluate(prices, weekly)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    status = ("GROSS_STRUCTURAL_SCREEN_PASS_EXECUTABLE_OPTIONS_DATA_STILL_BLOCKED"
              if all(gates.values()) else "I1_STRUCTURAL_MECHANISM_REJECTED_NO_RETUNE")
    report = dict(schema="I1_FIRSTPARTY_VARIANCE_PREMIUM_NONOVERLAP_STRUCTURAL_V1",
                  status=status, preregistration_commit=PREREG_COMMIT,
                  source_okx_run=40019588739, source_dvol_run=40072202459,
                  train_start_ms=START, train_end_exclusive_ms=END, horizon_hours=WINDOW,
                  windows=len(rows)//2, observations=len(rows), folds=folds, gates=gates,
                  rows=rows, structural_only=True, **FLAGS)
    path = out / "i1_structural_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps(dict(status=status, windows=report["windows"],
                          positive_folds={k:v["positive_folds"] for k,v in folds.items()},
                          mean_premium={k:v["all_mean_premium"] for k,v in folds.items()},
                          failed_gates=[k for k,v in gates.items() if not v],
                          no_promotion=True), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_variance_premium OKX_ROOT DVOL_ROOT OUTPUT_DIR")
    main(*sys.argv[1:])
