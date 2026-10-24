"""Independent Decimal fold sign/leave-one-out oracle for original I1 report."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from decimal import Decimal, localcontext
from pathlib import Path

ASSETS = ("BTC", "ETH")
ZERO = Decimal(0)


def independent(raw: bytes) -> dict:
    doc = json.loads(raw, parse_float=Decimal)
    if doc.get("schema") != "I1_FIRSTPARTY_VARIANCE_PREMIUM_NONOVERLAP_STRUCTURAL_V1":
        raise ValueError("I1_ORACLE_SCHEMA")
    if doc.get("train_start_ms") != 1639008000000 or doc.get("train_end_exclusive_ms") != 1696118400000:
        raise ValueError("I1_ORACLE_TRAIN_BOUNDARY")
    if doc.get("observations") != 30 or doc.get("windows") != 15:
        raise ValueError("I1_ORACLE_WINDOW_COUNT")
    if doc.get("structural_only") is not True:
        raise ValueError("I1_ORACLE_NOT_STRUCTURAL")
    for flag in ("promotion_authorized", "validation_opened", "holdout_opened",
                 "orders_enabled", "paper_publication_authorized", "economic_backtest_executed",
                 "trading_engine_evaluated", "native_fee_tier_authenticated",
                 "actual_account_fills_authenticated"):
        if doc.get(flag) is not False:
            raise ValueError("I1_ORACLE_SOURCE_FLAG_" + flag)
    rows = doc["rows"]
    unique = set()
    grouped = {}
    with localcontext() as ctx:
        ctx.prec = 42
        for r in rows:
            f, asset, t = r["fold"], r["asset"], r["decision_ms"]
            if f not in range(1, 6) or asset not in ASSETS:
                raise ValueError("I1_ORACLE_FOLD_ASSET")
            key = (f, asset, t)
            if key in unique:
                raise ValueError("I1_ORACLE_DUPLICATE")
            unique.add(key)
            iv, rv, prem = r["implied_variance"], r["realized_variance"], r["premium"]
            if iv <= 0 or rv < 0 or abs((iv-rv)-prem) > Decimal("1e-12"):
                raise ValueError("I1_ORACLE_PREMIUM")
            grouped.setdefault((f, asset), []).append((t, prem))
        if any(len(grouped.get((f, a), ())) != 3 for f in range(1, 6) for a in ASSETS):
            raise ValueError("I1_ORACLE_THREE_WINDOWS")
        for f in range(1, 6):
            if {t for t, _ in grouped[(f, "BTC")]} != {t for t, _ in grouped[(f, "ETH")]}:
                raise ValueError("I1_ORACLE_UNPAIRED")
        fold_means = {
            asset: [sum((v for _, v in grouped[(f, asset)]), ZERO) / 3
                    for f in range(1, 6)]
            for asset in ASSETS
        }
        fold_means["btc_eth_equal_pair_not_portfolio"] = [
            (fold_means["BTC"][i] + fold_means["ETH"][i]) / 2
            for i in range(5)
        ]
        result = {}
        for label, means in fold_means.items():
            positive = sum(v > ZERO for v in means)
            positives = [v for v in means if v > ZERO]
            total_pos = sum(positives, ZERO)
            loo = [(sum(means, ZERO) - means[i]) / 4 for i in range(5)]
            result[label] = {
                "fold_means": means,
                "positive_folds": positive,
                "idealized_one_sided_sign_tail": Decimal(sum(math.comb(5, k)
                                                            for k in range(positive, 6))) / 32,
                "equal_fold_mean": sum(means, ZERO) / 5,
                "leave_one_fold_out_means": loo,
                "min_leave_one_fold_out_mean": min(loo),
                "largest_positive_fold_share": max(positives) / total_pos if positives else None,
            }
    return result


def compare(expected, actual, path="root"):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise ValueError("I1_ORACLE_KEYS_" + path)
        for k, v in expected.items():
            compare(v, actual[k], path + "." + str(k))
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError("I1_ORACLE_LENGTH_" + path)
        for i, (x, y) in enumerate(zip(expected, actual)):
            compare(x, y, path + "." + str(i))
    elif isinstance(expected, Decimal):
        if not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(
                float(expected), float(actual), rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("I1_ORACLE_NUMERIC_" + path)
    elif expected != actual:
        raise ValueError("I1_ORACLE_VALUE_" + path)


def main(source_path: str, result_path: str) -> dict:
    raw = Path(source_path).read_bytes()
    result = json.loads(Path(result_path).read_text())
    if result.get("schema") != "I1_POST_SCREEN_FOLD_UNCERTAINTY_V1":
        raise ValueError("I1_ORACLE_RESULT_SCHEMA")
    if result.get("original_report_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("I1_ORACLE_HASH")
    for flag in ("promotion_authorized", "validation_opened", "holdout_opened",
                 "orders_enabled", "paper_publication_authorized",
                 "economic_backtest_executed", "trading_engine_evaluated"):
        if result.get(flag) is not False:
            raise ValueError("I1_ORACLE_RESULT_FLAG_" + flag)
    expected = independent(raw)
    compare(expected, result["asset_results"])
    tampered = copy.deepcopy(result["asset_results"])
    tampered["BTC"]["equal_fold_mean"] += 0.001
    try:
        compare(expected, tampered)
    except ValueError as e:
        if not str(e).startswith("I1_ORACLE_NUMERIC_"):
            raise
    else:
        raise ValueError("I1_ORACLE_FAILED_TO_DETECT_CORRUPTION")
    proof = {
        "status": "I1_ORIGINAL_TRAIN_DECIMAL_FOLD_UNCERTAINTY_VERIFIED",
        "folds": 5, "windows_per_asset": 15, "corruption_rejected": True,
        "no_promotion": True, "options_pnl_computed": False,
    }
    Path(result_path).with_name("i1_fold_uncertainty_oracle.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(proof, sort_keys=True))
    return proof


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_fold_uncertainty_oracle SOURCE_JSON RESULT_JSON")
    main(*sys.argv[1:])
