"""Independent original-source I1 causal signal replay and leakage falsification.

Imports only the established original source loaders and frozen calendar, NOT
the primary signal evaluator or its regime classifier.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, HOURS, FOLD_EDGES
from research.tools.v99_r106_e1_spot_engine import load_original_spot
from research.tools.v99_r106_h1_dvol_spot_engine import load_original_dvol
from research.tools.v99_r106_i1_full_archive_intake import eligible

ASSETS = ("BTC", "ETH")


def original_lagged_variance(series, i):
    return math.fsum((math.log(series[k])-math.log(series[k-1]))**2
                     for k in range(i-720, i))


def original_regime(series, i):
    if i < 889:
        return "insufficient_lag"
    trend_return = series[i-1]/series[i-721]-1
    trend = "up" if trend_return > 0.02 else ("down" if trend_return < -0.02 else "flat")
    hourly = [math.log(series[k]/series[k-1]) for k in range(i-336, i)]
    vols = [statistics.pstdev(hourly[k-167:k+1])
            for k in range(167, len(hourly))]
    if len(vols) < 169:
        return "insufficient_lag"
    bucket = "high" if vols[-1] > statistics.median(vols[-169:-1]) else "low"
    return trend+"_"+bucket


def verify(prices, weekly, report):
    if (report.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
            or report.get("status") != "ORIGINAL_CAUSAL_SIGNAL_ONLY_OPTIONS_ECONOMICS_BLOCKED"
            or report.get("observations") != 182
            or report.get("eligible_weeks") != 91
            or report.get("right_censored_weeks") != 3
            or report.get("train_start_ms") != START
            or report.get("train_end_exclusive_ms") != END
            or report.get("trailing_hours") != 720):
        raise AssertionError("FORGED_CAUSAL_REPORT_HEADER")
    for key in ("economic_train_executed", "fills_authenticated",
                "native_fees_authenticated", "native_margin_authenticated",
                "validation_opened", "holdout_opened",
                "orders_enabled", "promotion_authorized"):
        if report.get(key) is not False:
            raise AssertionError("FORGED_ECONOMIC_STATUS")
    if report.get("source_original") is not True:
        raise AssertionError("UNVERIFIED_SOURCE_CLAIM")
    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != 182:
        raise AssertionError("NOT_182_ORIGINAL_SIGNALS")
    expected_keys = [(int(d.timestamp()*1000), asset)
                     for d in eligible() for asset in ASSETS]
    if [(r.get("decision_ms"), r.get("asset")) for r in rows] != expected_keys:
        raise AssertionError("REORDERED_OR_MISSING_DECISIONS")
    counts = {str(f): {a: {"positive": 0, "negative": 0, "no_history": 0}
                       for a in ASSETS} for f in range(1, 6)}
    for row in rows:
        t, asset = row["decision_ms"], row["asset"]
        idx = (t-START)//HOUR
        fold = next((f for f in range(1,6) if FOLD_EDGES[f-1] <= t < FOLD_EDGES[f]), None)
        if row["fold"] != fold or row["regime"] != original_regime(prices[0], idx):
            raise AssertionError("FORGED_FOLD_OR_REGIME")
        dv = weekly[(t, asset)]
        iv = (dv/100.0)**2*(30.0/365.0)
        if not (math.isclose(row["dvol_percent"], dv, rel_tol=0, abs_tol=1e-12)
                and math.isclose(row["implied_var_30d"], iv, rel_tol=0, abs_tol=1e-12)):
            raise AssertionError("FORGED_IMPLIED_VARIANCE")
        if idx < 721:
            if (row["trailing_rv_30d"] is not None or
                    row["trailing_first_price_ms"] is not None or
                    row["trailing_last_price_ms"] is not None or
                    row["signal"] != "NO_30D_HISTORY"):
                raise AssertionError("FUTURE_OR_SHORT_WINDOW_BACKFILL")
            bucket = "no_history"
        else:
            rv = original_lagged_variance(prices[ASSETS.index(asset)], idx)
            if row["trailing_rv_30d"] is None or not math.isclose(
                    row["trailing_rv_30d"], rv, rel_tol=1e-10, abs_tol=1e-12):
                raise AssertionError("FORGED_CAUSAL_TRAILING_VARIANCE")
            if (row["trailing_first_price_ms"] != START+(idx-721)*HOUR
                    or row["trailing_last_price_ms"] != START+(idx-1)*HOUR
                    or row["trailing_last_price_ms"] >= t):
                raise AssertionError("FUTURE_PRICE_INCLUDED")
            signal = "POSITIVE_EX_ANTE_PREMIUM" if iv > rv else "NO_PREMIUM"
            if row["signal"] != signal:
                raise AssertionError("FORGED_EX_ANTE_SIGNAL")
            bucket = "positive" if iv > rv else "negative"
        counts[str(fold)][asset][bucket] += 1
    if report.get("counts") != counts:
        raise AssertionError("FORGED_FOLD_COUNTS")
    return counts


def main(spot_root, dvol_root, result_path):
    prices = load_original_spot(spot_root)
    weekly = load_original_dvol(dvol_root)
    path = Path(result_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    counts = verify(prices, weekly, report)
    valid = next(r for r in report["rows"] if r["trailing_rv_30d"] is not None)
    idx = (valid["decision_ms"]-START)//HOUR
    asset_series = prices[ASSETS.index(valid["asset"])]
    baseline = original_lagged_variance(asset_series, idx)
    future = list(asset_series)
    future[idx+1] *= 1.7
    if original_lagged_variance(future, idx) != baseline:
        raise AssertionError("FUTURE_PRICE_LEAK")
    past = list(asset_series)
    past[idx-1] *= 1.7
    if original_lagged_variance(past, idx) == baseline:
        raise AssertionError("PAST_PRICE_IGNORED")
    bad = json.loads(json.dumps(report))
    tampered = next(r for r in bad["rows"] if r["trailing_rv_30d"] is not None)
    tampered["trailing_rv_30d"] += 0.01
    try:
        verify(prices, weekly, bad)
    except AssertionError as exc:
        if str(exc) != "FORGED_CAUSAL_TRAILING_VARIANCE":
            raise
    else:
        raise AssertionError("FAILED_TO_REJECT_TAMPERED_RESULT")
    result = dict(status="INDEPENDENT_ORIGINAL_T_MINUS_ONE_SIGNAL_MATCH",
                  observations=182, folds=5, counts=counts,
                  future_price_mutation_invariant=True,
                  prior_price_mutation_detected=True,
                  tampered_report_rejected=True,
                  economic_train_executed=False,
                  promotion_authorized=False)
    out = path.parent/"i1_causal_signal_independent_oracle.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_causal_signal_oracle OKX_ROOT DVOL_ROOT REPORT")
    main(*sys.argv[1:])
