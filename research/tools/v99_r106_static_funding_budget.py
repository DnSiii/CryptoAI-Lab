"""One-shot preregistered Binance publisher funding-rate budget screen; NO strategy/ROI/orders."""
from __future__ import annotations
import bisect
import hashlib
import json
import math
import sys
from pathlib import Path
from research.tools import v99_r106_binance_funding_original_train_source as original

START, END, STEP = original.START, original.END, original.STEP
FOLD_HOURS = (0, 3172, 6345, 9518, 12691, 15864)
FOLD_EDGES = tuple(START + x * 3600000 for x in FOLD_HOURS)
COSTS = {"severe": 4 * .0007, "supersevere": 4 * .0014}
EXPECTED = tuple(range(START, END, STEP))
SCHEMA = "V99_R106_ORIGINAL_FUNDING_STATIC_BUDGET_NOT_ROI_V1"

def bind_original_events(events, start=START, end=END):
    """No interpolation, no backdated availability; event clock only."""
    expected = list(range(start, end, STEP))
    seen = {}
    for ts, interval, rate in events:
        if not isinstance(ts, int) or not math.isfinite(interval) or not math.isfinite(rate):
            raise ValueError("invalid_native_event")
        if interval != 8:
            raise ValueError("unexpected_native_funding_interval")
        nominal = (ts // STEP) * STEP
        lag = ts - nominal
        if not 0 <= lag <= 31:
            raise ValueError("invalid_native_event_clock_offset")
        if not start <= nominal < end:
            continue
        if nominal in seen:
            raise ValueError("duplicate_native_funding_event")
        seen[nominal] = (float(rate), int(lag))
    if set(seen) != set(expected):
        raise ValueError("missing_native_funding_events")
    return seen

def read_original(root):
    raw = Path(root) / "raw_ephemeral"
    for symbol in original.SYMBOLS:
        events = []
        for month in original.MONTHS:
            name = f"{symbol}-fundingRate-{month}.zip"
            blob = (raw / name).read_bytes()
            checksum = (raw / (name + ".CHECKSUM")).read_bytes()
            import re
            match = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum)
            if match is None or hashlib.sha256(blob).hexdigest() != match.group(1).decode().lower():
                raise ValueError("publisher_sha256_mismatch")
            events.extend(original.parse_csv(blob, month))
        yield symbol, bind_original_events(events)

def calculate(original_events):
    if set(original_events) != set(original.SYMBOLS):
        raise ValueError("missing_original_assets")
    by_asset = {}
    for symbol in original.SYMBOLS:
        events = original_events[symbol]
        if set(events) != set(EXPECTED):
            raise ValueError("incomplete_original_train")
        folds = [dict(rate_sum=0., positive_events=0, negative_events=0,
                      zero_events=0, event_count=0, min_rate=None, max_rate=None)
                 for _ in range(5)]
        for nominal in EXPECTED:
            rate, lag = events[nominal]
            if not 0 <= lag <= 31 or not math.isfinite(rate):
                raise ValueError("bad_original_funding_rate")
            k = bisect.bisect_right(FOLD_EDGES, nominal) - 1
            if not 0 <= k < 5:
                raise ValueError("funding_fold_boundary")
            f = folds[k]
            f["rate_sum"] += rate
            f["event_count"] += 1
            f["positive_events"] += int(rate > 0)
            f["negative_events"] += int(rate < 0)
            f["zero_events"] += int(rate == 0)
            f["min_rate"] = rate if f["min_rate"] is None else min(f["min_rate"], rate)
            f["max_rate"] = rate if f["max_rate"] is None else max(f["max_rate"], rate)
        by_asset[symbol] = folds
    expected_fold_counts = [sum(FOLD_EDGES[k] <= ts < FOLD_EDGES[k+1] for ts in EXPECTED)
                            for k in range(5)]
    if expected_fold_counts != [397, 397, 396, 397, 396]:
        raise ValueError("unexpected_fixed_fold_event_counts")
    for symbol in original.SYMBOLS:
        if [f["event_count"] for f in by_asset[symbol]] != expected_fold_counts:
            raise ValueError("funding_fold_coverage")
    folds = []
    for k in range(5):
        gross = sum(by_asset[s][k]["rate_sum"] for s in original.SYMBOLS) / 2.
        folds.append({
            "fold": k+1,
            "events_per_asset": expected_fold_counts[k],
            "btc_signed_rate_sum": by_asset["BTCUSDT"][k]["rate_sum"],
            "eth_signed_rate_sum": by_asset["ETHUSDT"][k]["rate_sum"],
            "static_50_50_signed_funding_rate_budget_NOT_ROI": gross,
            "illustrative_budget_minus_four_side_cost_NOT_ROI": {
                name: gross - cost for name, cost in COSTS.items()
            },
        })
    positive_folds = {name: sum(f["illustrative_budget_minus_four_side_cost_NOT_ROI"][name] > 0
                                for f in folds) for name in COSTS}
    return {
        "schema": SCHEMA,
        "status": ("FUNDING_BUDGET_UNFALSIFIED_SOURCE_ONLY"
                   if positive_folds["severe"] >= 4
                   else "FUNDING_BUDGET_FAIL_4_OF_5_SOURCE_ONLY"),
        "publisher": "data.binance.vision",
        "train_start_ms": START, "train_end_exclusive_ms": END,
        "fold_edges_hours": list(FOLD_HOURS),
        "original_archives": 44, "original_events_per_asset": len(EXPECTED),
        "cost_allowances_per_fold": COSTS,
        "assets": by_asset, "folds": folds, "positive_budget_folds": positive_folds,
        "whole_train_signed_rate_budget_NOT_ROI": sum(
            f["static_50_50_signed_funding_rate_budget_NOT_ROI"] for f in folds),
        "rate_budget_is_not_nav_or_roi": True,
        "public_funding_is_not_account_settlement": True,
        "no_basis_or_fills_or_margin_certified": True,
        "economic_train_executed": False,
        "promotion_authorized": False, "orders_enabled": False,
        "validation_opened": False, "holdout_opened": False,
        "paper_modified": False, "frozen_modified": False,
    }

def run(root):
    root = Path(root)
    source_report = original.run(root)
    if sum(x["publisher_checksum_verified"] for x in source_report["files"]) != 44:
        raise ValueError("original_44_archive_provenance_incomplete")
    events = dict(read_original(root))
    report = calculate(events)
    (root / "static_funding_budget_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "positive_budget_folds": report["positive_budget_folds"],
                      "folds": report["folds"], "not_roi": True, "promotion": False},
                     sort_keys=True))
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_static_funding_budget OUTDIR")
    run(sys.argv[1])
