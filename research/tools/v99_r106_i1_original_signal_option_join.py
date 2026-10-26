"""Join ORIGINAL causal I1 TRAIN signals to original partial option-book receipts.

SOURCE ONLY: not an economic engine, not original fills, not licensed full tape.
Preregistered: research/V99_R106_I1_ORIGINAL_SIGNAL_TO_OPTIONS_SOURCE_JOIN_PREREG_20261026.md
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START, END, FOLD_EDGES
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_execution_readiness import verify_and_load, parse_instrument

AGE_US = 300_000_000
SKEW_US = 1_000_000
DAY_US = 86_400_000_000
FLAGS = dict(economic_train_executed=False, historical_option_fills_certified=False,
             native_fee_tier_authenticated=False, native_margin_authenticated=False,
             certified_complete_option_lifecycles=0, validation_opened=False,
             holdout_opened=False, orders_enabled=False, promotion_authorized=False)


def original_rows(root: Path):
    # Existing source verifier authenticates original sample hashes, clocks and shape.
    manifest, _ = verify_and_load(root)
    raw = []
    for day in manifest["days"]:
        with (root / day["sample_file"]).open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if row["exchange"] != "deribit":
                    raise ValueError("WRONG_ORIGINAL_OPTION_VENUE")
                arrival, event = int(row["local_timestamp"]), int(row["timestamp"])
                # Preserve anomalous exchange clocks: the last physically arrived
                # update must revoke older quotes, even if event > arrival.
                raw.append((arrival, event, row))
    return raw


def _good(row):
    try:
        values = [float(row[k]) for k in
                  ("bid_price", "ask_price", "bid_amount", "ask_amount")]
    except (ValueError, TypeError, OverflowError):
        return False
    return all(math.isfinite(v) and v > 0 for v in values) and values[0] < values[1]


def source_ready(raw, decision_ms: int, asset: str):
    t = decision_ms * 1000
    latest = {}
    for arrival, event, row in raw:
        # Select the physically latest predecision update BEFORE freshness checks.
        # A newer stale-event quote must revoke an older fresh quote.
        if not (arrival < t):
            continue
        p = parse_instrument(row["symbol"])
        if p is None or p[0] != asset:
            continue
        if not (21 * DAY_US <= p[1] - t <= 45 * DAY_US and p[1] < END * 1000):
            continue
        symbol = row["symbol"]
        if symbol not in latest or arrival >= latest[symbol][0]:
            latest[symbol] = (arrival, event, p, row)
    by_expiry = {}
    for arrival, event, p, row in latest.values():
        if t - AGE_US <= event <= arrival < t and _good(row):
            by_expiry.setdefault(p[1], []).append((arrival, event, p[2]))
    for quotes in by_expiry.values():
        for i, a in enumerate(quotes):
            for b in quotes[i + 1:]:
                if (a[2] != b[2] and abs(a[0] - b[0]) <= SKEW_US
                        and abs(a[1] - b[1]) <= SKEW_US):
                    return True
    return False


def join(signal_path: Path, partial_root: Path):
    signal_path, partial_root = Path(signal_path), Path(partial_root)
    report = json.loads(signal_path.read_text(encoding="utf-8"))
    if (report.get("schema") != "V99_I1_ORIGINAL_TRAIN_CAUSAL_30D_SIGNAL_V1"
            or report.get("source_original") is not True
            or report.get("observations") != 182
            or report.get("eligible_weeks") != 91
            or report.get("economic_train_executed") is not False
            or report.get("promotion_authorized") is not False):
        raise ValueError("UNTRUSTED_OR_NONORIGINAL_SIGNAL_REPORT")
    expected = [(int(d.timestamp() * 1000), asset)
                for d in eligible() for asset in ("BTC", "ETH")]
    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != 182:
        raise ValueError("WRONG_ORIGINAL_SIGNAL_COUNT")
    observed = [(r["decision_ms"], r["asset"]) for r in rows]
    if observed != expected:
        raise ValueError("SIGNAL_DECISION_GRID_CHANGED")
    raw = original_rows(partial_root)
    output = []
    folds = {str(f): {"BTC": {"positive": 0, "source_ready": 0, "intersection": 0},
                      "ETH": {"positive": 0, "source_ready": 0, "intersection": 0}}
             for f in range(1, 6)}
    for r in rows:
        t, asset = r["decision_ms"], r["asset"]
        f = next((i for i in range(1, 6) if FOLD_EDGES[i-1] <= t < FOLD_EDGES[i]), None)
        if f != r["fold"] or not START <= t < END:
            raise ValueError("FORGED_OR_SEALED_FOLD")
        if r["signal"] not in ("POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY"):
            raise ValueError("UNPREREGISTERED_SIGNAL")
        positive = r["signal"] == "POSITIVE_EX_ANTE_PREMIUM"
        ready = source_ready(raw, t, asset)
        intersection = positive and ready
        bucket = folds[str(f)][asset]
        bucket["positive"] += int(positive)
        bucket["source_ready"] += int(ready)
        bucket["intersection"] += int(intersection)
        output.append(dict(decision_ms=t, asset=asset, fold=f,
                           causal_signal=r["signal"], original_two_leg_source_ready=ready,
                           signal_and_source_intersection=intersection))
    if sum(f[a]["positive"] for f in folds.values() for a in ("BTC", "ETH")) != 132:
        raise ValueError("ORIGINAL_SIGNAL_COUNT_NOT_RECONCILED")
    return dict(schema="V99_I1_ORIGINAL_SIGNAL_OPTION_SOURCE_INTERSECTION_V1",
                status="BLOCKED_PARTIAL_ORIGINAL_OPTION_ARCHIVE",
                preregistration_path="research/V99_R106_I1_ORIGINAL_SIGNAL_TO_OPTIONS_SOURCE_JOIN_PREREG_20261026.md",
                source_signal_sha256=hashlib.sha256(signal_path.read_bytes()).hexdigest(),
                source_partial_manifest_sha256=hashlib.sha256((partial_root / "manifest.json").read_bytes()).hexdigest(),
                original_source_rows=4000, original_signal_observations=182,
                positive_original_causal_signals=132,
                original_source_ready_asset_weeks=sum(f[a]["source_ready"] for f in folds.values() for a in ("BTC", "ETH")),
                signal_source_intersections=sum(f[a]["intersection"] for f in folds.values() for a in ("BTC", "ETH")),
                folds=folds, decisions=output, **FLAGS)


def main(signal_path, partial_root, output):
    result = join(Path(signal_path), Path(partial_root))
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
        ("status", "original_signal_observations", "positive_original_causal_signals",
         "original_source_ready_asset_weeks", "signal_source_intersections",
         "certified_complete_option_lifecycles", "economic_train_executed")}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_signal_option_join SIGNAL_JSON PARTIAL_ROOT OUT_JSON")
    main(*sys.argv[1:])
