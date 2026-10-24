"""Post-screen I1 five-fold gross-variance uncertainty; no trading or PnL."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from research.tools.v99_r106_i1_gross_tail import validate_original

ASSETS = ("BTC", "ETH")
NO_PROMOTION = {
    "validation_opened": False, "holdout_opened": False,
    "orders_enabled": False, "paper_publication_authorized": False,
    "promotion_authorized": False, "economic_backtest_executed": False,
    "trading_engine_evaluated": False,
}


def one_sided_sign_tail(positive: int) -> float:
    if not 0 <= positive <= 5:
        raise ValueError("I1_SIGN_TEST_COUNT")
    return sum(math.comb(5, k) for k in range(positive, 6)) / 32.0


def describe(fold_means: list[float]) -> dict:
    if len(fold_means) != 5 or not all(math.isfinite(x) for x in fold_means):
        raise ValueError("I1_FOLD_MEANS")
    positive = sum(x > 0 for x in fold_means)
    positive_sum = math.fsum(max(0.0, x) for x in fold_means)
    leave_one_out = [math.fsum(fold_means[:i] + fold_means[i + 1:]) / 4
                     for i in range(5)]
    return {
        "fold_means": fold_means,
        "positive_folds": positive,
        "idealized_one_sided_sign_tail": one_sided_sign_tail(positive),
        "equal_fold_mean": math.fsum(fold_means) / 5,
        "leave_one_fold_out_means": leave_one_out,
        "min_leave_one_fold_out_mean": min(leave_one_out),
        "largest_positive_fold_share": (max(fold_means) / positive_sum
                                        if positive_sum > 0 else None),
    }


def calculate(original: dict) -> dict:
    rows, paired = validate_original(original)
    if original.get("observations") != 30 or original.get("structural_only") is not True:
        raise ValueError("I1_NOT_ORIGINAL_STRUCTURAL_REPORT")
    for k in ("native_fee_tier_authenticated", "actual_account_fills_authenticated"):
        if original.get(k) is not False:
            raise ValueError("I1_UNAUTHENTICATED_SOURCE_FLAG")
    groups = {}
    for asset in ASSETS:
        groups[asset] = describe([
            statistics.fmean(r["premium"] for r in rows
                             if r["asset"] == asset and r["fold"] == fold)
            for fold in range(1, 6)
        ])
    paired_by_fold = []
    for fold in range(1, 6):
        vals = [
            math.fsum(r["premium"] for r in pair) / 2.0
            for (f, _), pair in sorted(paired.items()) if f == fold
        ]
        if len(vals) != 3:
            raise ValueError("I1_PAIRED_FOLD_MISMATCH")
        paired_by_fold.append(statistics.fmean(vals))
    groups["btc_eth_equal_pair_not_portfolio"] = describe(paired_by_fold)
    return {
        "schema": "I1_POST_SCREEN_FOLD_UNCERTAINTY_V1",
        "status": "GROSS_VARIANCE_UNCERTAINTY_ONLY_NO_EXECUTABLE_OPTIONS",
        "source_i1_run": 40087572354,
        "train_start_ms": 1639008000000,
        "train_end_exclusive_ms": 1696118400000,
        "original_windows_per_asset": 15,
        "chronological_folds": 5,
        "gross_only": True,
        "fold_independence_unverified": True,
        "sign_test_is_descriptive_not_exchange_profit_proof": True,
        "asset_results": groups,
        **NO_PROMOTION,
    }


def main(original_path: str, out_dir: str) -> dict:
    original_bytes = Path(original_path).read_bytes()
    doc = json.loads(original_bytes)
    result = calculate(doc)
    result["original_report_sha256"] = hashlib.sha256(original_bytes).hexdigest()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "i1_fold_uncertainty.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "fold_results": {
            k: {"positive_folds": v["positive_folds"],
                "idealized_one_sided_sign_tail": v["idealized_one_sided_sign_tail"],
                "equal_fold_mean": v["equal_fold_mean"],
                "min_leave_one_fold_out_mean": v["min_leave_one_fold_out_mean"],
                "largest_positive_fold_share": v["largest_positive_fold_share"]}
            for k, v in result["asset_results"].items()
        },
        "no_promotion": True,
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_fold_uncertainty ORIGINAL_JSON OUT_DIR")
    main(*sys.argv[1:])
