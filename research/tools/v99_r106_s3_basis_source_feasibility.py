"""V99 S3 preregistered spot/perp basis SOURCE feasibility, TRAIN only, no PnL/orders."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import (
    START, END, HOURS, HOUR, FOLD_EDGES, strict_json,
)
from research.verification.independent_d1_native_train_receipts import verify

THRESHOLD = 0.029  # 4 * 60bp two-leg round trip + 50bp buffer; NOT an alpha claim
WARMUP = 720
COINS = ("BTC", "ETH")
NO_PROMOTION = {
    "economic_trial_run": False, "native_funding_authenticated": False,
    "native_fee_tier_authenticated": False, "historical_fills_authenticated": False,
    "validation_opened": False, "final_holdout_opened": False,
    "promotion_authorized": False, "paper_publication_authorized": False,
    "orders_enabled": False,
}


def load(root: Path) -> dict:
    if verify(root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("S3_ORIGINAL_FOUR_LEG_SOURCE_VETO")
    expected = list(range(START, END, HOUR))
    result = {}
    for coin in COINS:
        for kind, suffix in (("spot", "-USDT"), ("swap", "-USDT-SWAP")):
            rows = strict_json(root / (coin + suffix) / "train_opens.json")
            if len(rows) != HOURS or [x["ts"] for x in rows] != expected:
                raise ValueError("S3_SEALED_OR_INCOMPLETE_TRAIN_GRID")
            values = [float(x["open"]) for x in rows]
            if any(not math.isfinite(x) or x <= 0 for x in values):
                raise ValueError("S3_BAD_ORIGINAL_OPEN")
            result[(coin, kind)] = values
    return result


def fold(timestamp: int) -> int:
    for i, (left, right) in enumerate(zip(FOLD_EDGES, FOLD_EDGES[1:])):
        if left <= timestamp < right:
            return i
    raise ValueError("S3_TRAIN_BOUNDARY_VIOLATION")


def run(root: Path, output: Path) -> dict:
    px = load(root)
    by_coin = {coin: 0 for coin in COINS}
    by_fold = [0] * 5
    by_fold_coin = {coin: [0] * 5 for coin in COINS}
    by_regime = {f"{trend}_{vol}": {"eligible_days": 0, "daily_observations": 0}
                 for trend in ("bull", "bear", "sideways") for vol in ("low", "high")}
    observed = 0
    eligible_days = 0
    digest = hashlib.sha256()
    max_premium = {coin: -float("inf") for coin in COINS}
    for t in range(WARMUP, HOURS, 24):
        timestamp = START + t * HOUR
        if timestamp >= END:
            raise ValueError("S3_SEALED_HOUR")
        # STRICT t-1: no use of price[t] for the eligibility decision.
        premiums = {
            coin: px[(coin, "swap")][t - 1] / px[(coin, "spot")][t - 1] - 1.
            for coin in COINS
        }
        flags = {coin: premiums[coin] >= THRESHOLD for coin in COINS}
        for coin in COINS:
            max_premium[coin] = max(max_premium[coin], premiums[coin])
        digest.update(f"{timestamp},{int(flags['BTC'])},{int(flags['ETH'])}\n".encode())
        btc = px[("BTC", "spot")]
        trailing = btc[t - 1] / btc[t - 720] - 1
        log_returns = [math.log(btc[k] / btc[k - 1]) for k in range(t - 72, t)]
        sigma = statistics.pstdev(log_returns) * math.sqrt(24)
        trend = "bull" if trailing > .05 else "bear" if trailing < -.05 else "sideways"
        vol = "high" if sigma >= .04 else "low"
        regime = f"{trend}_{vol}"
        by_regime[regime]["daily_observations"] += 1
        observed += 1
        if any(flags.values()):
            eligible_days += 1
            by_fold[fold(timestamp)] += 1
            by_regime[regime]["eligible_days"] += 1
        for coin in COINS:
            if flags[coin]:
                by_coin[coin] += 1
                by_fold_coin[coin][fold(timestamp)] += 1
    folds_with_eligibility = sum(v > 0 for v in by_fold)
    result = {
        "schema": "V99_R106_S3_ORIGINAL_BASIS_SOURCE_FEASIBILITY_V1",
        "status": ("FEASIBILITY_ONLY_NO_PROMOTION" if folds_with_eligibility >= 4
                   else "OPPORTUNITY_VETO_NO_ECONOMIC_TRIAL"),
        "source": "FIRST_PARTY_OKX_ORIGINAL_HOURLY_OPENS_NOT_EXECUTABLE_QUOTES",
        "train_start_ms": START, "train_end_exclusive_ms": END,
        "original_train_hours_per_leg": HOURS, "legs": 4,
        "warmup_hours": WARMUP, "decision_interval_hours": 24,
        "threshold_premium": THRESHOLD, "daily_observations": observed,
        "eligible_unique_days": eligible_days, "eligible_by_coin": by_coin,
        "eligible_by_fold": by_fold, "eligible_by_fold_coin": by_fold_coin,
        "folds_with_eligibility": folds_with_eligibility,
        "eligible_by_regime": by_regime,
        "maximum_indicative_premium": max_premium,
        "eligibility_trace_sha256": digest.hexdigest(),
        "first_party_original_receipts_verified": True,
        "historical_opens_are_not_fills": True,
        "funding_and_execution_require_independent_provenance": True,
        **NO_PROMOTION,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "s3_basis_source_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: result[k] for k in (
        "status", "daily_observations", "eligible_unique_days",
        "eligible_by_coin", "eligible_by_fold", "folds_with_eligibility",
        "maximum_indicative_premium", "economic_trial_run", "promotion_authorized",
    )}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_s3_basis_source_feasibility PRICE_ROOT OUTPUT")
    run(Path(sys.argv[1]), Path(sys.argv[2]))
