"""Independent Decimal re-execution of I1 gross tail stress from original receipts."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import sys
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path

from research.verification.independent_v99_r106_i1_variance_oracle import (
    read_spot, read_dvol, verify_report,
)

MULT = ("1.0", "1.25", "1.5")
ASSETS = ("BTC", "ETH")


def aggregate(items):
    # Each item is (fold, Decimal gross variance premium).
    vals = [v for _, v in items]
    pos = sorted((v for v in vals if v > 0), reverse=True)
    neg = [-v for v in vals if v < 0]
    p = sum(pos, Decimal(0))
    n = sum(neg, Decimal(0))
    fold_means = [sum((v for f, v in items if f == fold), Decimal(0)) /
                  sum(1 for f, _ in items if f == fold) for fold in range(1, 6)]
    return dict(observations=len(vals), mean=sum(vals, Decimal(0))/len(vals),
                positive_windows=len(pos),
                positive_folds=sum(x > 0 for x in fold_means),
                fold_means=fold_means, worst_window=min(vals),
                total_positive=p, total_negative_magnitude=n,
                top_two_positive_share=(sum(pos[:2], Decimal(0))/p if p else None),
                largest_loss_to_total_positive=(max(neg)/p if neg and p else None))


def independent(doc):
    rows = doc["rows"]
    if len(rows) != 30 or doc["observations"] != 30:
        raise ValueError("TAIL_ORACLE_COUNT")
    pairs = {}
    for row in rows:
        pairs.setdefault((row["fold"], row["decision_ms"]), {})[row["asset"]] = row
    if len(pairs) != 15 or any(set(pair) != set(ASSETS) for pair in pairs.values()):
        raise ValueError("TAIL_ORACLE_PAIRS")
    results = {}
    with localcontext() as ctx:
        ctx.prec = 38
        for label in MULT:
            factor = Decimal(label)
            asset_data = {}
            for asset in ASSETS:
                entries = [(r["fold"], Decimal(str(r["implied_variance"])) -
                            factor*Decimal(str(r["realized_variance"])))
                           for r in rows if r["asset"] == asset]
                asset_data[asset] = aggregate(entries)
            pair_data = []
            for (fold, _), pair in sorted(pairs.items()):
                value = sum((Decimal(str(pair[a]["implied_variance"])) -
                             factor*Decimal(str(pair[a]["realized_variance"]))
                             for a in ASSETS), Decimal(0))/Decimal(2)
                pair_data.append((fold, value))
            results[label] = dict(assets=asset_data,
                                  paired_equal_weight_nonportfolio=aggregate(pair_data))
    return dict(multipliers=results,
                regime_window_counts=dict(sorted(Counter(r["regime"] for r in rows
                                                         if r["asset"] == "BTC").items())),
                worst_realized_to_implied={a:max(r["realized_to_implied"] for r in rows
                                                if r["asset"] == a) for a in ASSETS})


def compare(expected, actual, path="root"):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise ValueError("TAIL_ORACLE_KEYS_"+path)
        for k, v in expected.items():
            compare(v, actual[k], path+"."+str(k))
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError("TAIL_ORACLE_LIST_"+path)
        for i, (a, b) in enumerate(zip(expected, actual)):
            compare(a, b, path+"."+str(i))
    elif isinstance(expected, Decimal):
        if not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(
                float(expected), float(actual), rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("TAIL_ORACLE_NUMERIC_"+path)
    elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if not isinstance(actual, (int, float)) or not math.isclose(
                expected, actual, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("TAIL_ORACLE_NUMERIC_"+path)
    elif expected != actual:
        raise ValueError("TAIL_ORACLE_VALUE_"+path)


def main(spot_root, dvol_root, original_path, tail_path):
    raw = Path(original_path).read_bytes()
    doc = json.loads(raw)
    independent_status = verify_report(read_spot(spot_root), read_dvol(dvol_root), doc)
    if independent_status["status"] != "INDEPENDENT_ORIGINAL_DVOL_SPOT_30D_VARIANCE_REEXECUTION_VERIFIED":
        raise ValueError("TAIL_ORACLE_SOURCE")
    tail = json.loads(Path(tail_path).read_text())
    if tail["schema"] != "V99_I1_POST_SCREEN_GROSS_TAIL_SENSITIVITY_V1":
        raise ValueError("TAIL_ORACLE_SCHEMA")
    if tail["source_report_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("TAIL_ORACLE_SOURCE_HASH")
    for key in ("promotion_authorized", "validation_opened", "holdout_opened",
                "orders_enabled", "paper_publication_authorized",
                "trading_engine_evaluated", "economic_backtest_executed"):
        if tail.get(key) is not False:
            raise ValueError("TAIL_ORACLE_FORBIDDEN_"+key)
    expected = independent(doc)
    compare(expected, {k:tail[k] for k in expected})
    tampered = copy.deepcopy(tail)
    tampered["multipliers"]["1.5"]["assets"]["ETH"]["mean"] += 0.001
    try:
        compare(expected, {k:tampered[k] for k in expected})
    except ValueError as e:
        if "TAIL_ORACLE_NUMERIC_" not in str(e):
            raise
    else:
        raise ValueError("TAIL_ORACLE_CORRUPTION_NOT_REJECTED")
    result = dict(status="INDEPENDENT_ORIGINAL_SOURCE_DECIMAL_TAIL_STRESS_VERIFIED",
                  windows=15, assets=2, stress_scenarios=3,
                  corruption_rejected=True, no_promotion=True,
                  validation_opened=False, holdout_opened=False)
    dest = Path(tail_path).with_name("i1_gross_tail_independent_oracle.json")
    dest.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_gross_tail_oracle OKX_ROOT DVOL_ROOT ORIGINAL_JSON TAIL_JSON")
    main(*sys.argv[1:])
