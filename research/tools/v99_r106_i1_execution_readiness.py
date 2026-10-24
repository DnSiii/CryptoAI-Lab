"""I1 executable option quote readiness from ORIGINAL archived Tardis sample bytes.

This is a fail-closed pre-economic data contract, not an option backtest.
No orders, no PnL, no validation or holdout access.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, FOLD_EDGES

UTC = timezone.utc
MONDAY_MS = 7 * 24 * HOUR
MAX_AGE_US = 5 * 60 * 1_000_000
REQUIRED_ASSETS = ("BTC", "ETH")


def monday_decisions():
    return [t for t in range(START, END, HOUR)
            if datetime.fromtimestamp(t / 1000, UTC).weekday() == 0
            and datetime.fromtimestamp(t / 1000, UTC).hour == 0]


def parse_instrument(symbol):
    # Deribit instrument names: BTC-30DEC22-15000-P. Never infer from a substring.
    p = symbol.split("-")
    if len(p) != 4 or p[0] not in REQUIRED_ASSETS or p[3] != "P":
        return None
    try:
        expiry = datetime.strptime(p[1].upper(), "%d%b%y").replace(hour=8, tzinfo=UTC)
        strike = float(p[2])
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(strike) or strike <= 0:
        return None
    return p[0], int(expiry.timestamp() * 1_000_000), strike


def verify_and_load(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("classification") != "PARTIAL_SOURCE_SAMPLE_ONLY_NOT_EXECUTION_OR_PNL":
        raise ValueError("NOT_ORIGINAL_PARTIAL_QUOTE_MANIFEST")
    if manifest.get("complete_train") is not False or manifest.get("asof_quote_coverage") is not False:
        raise ValueError("UNTRUSTED_COMPLETENESS_CLAIM")
    if [x["date"] for x in manifest["days"]] != ["2022-01-01", "2023-01-01"]:
        raise ValueError("WRONG_PREREGISTERED_SAMPLE_DAYS")
    all_rows = []
    for day in manifest["days"]:
        path = root / day["sample_file"]
        if path.parent.resolve() != root.resolve():
            raise ValueError("PATH_TRAVERSAL")
        if hashlib.sha256(path.read_bytes()).hexdigest() != day["csv_sha256"]:
            raise ValueError("SOURCE_SHA_MISMATCH")
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"exchange", "symbol", "timestamp", "local_timestamp",
                        "bid_price", "ask_price", "bid_amount", "ask_amount"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("QUOTE_COLUMNS_MISSING")
            rows = list(reader)
        if len(rows) != day["rows_partial"] or len(rows) > 2000:
            raise ValueError("SAMPLE_ROW_COUNT_MISMATCH")
        day_start_us = int(datetime.strptime(day["date"], "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1_000_000)
        for row in rows:
            if row["exchange"] != "deribit":
                raise ValueError("WRONG_VENUE")
            exchange_us = int(row["timestamp"])
            arrival_us = int(row["local_timestamp"])
            if not day_start_us <= arrival_us < day_start_us + 86400 * 1_000_000:
                raise ValueError("QUOTE_OUTSIDE_ARCHIVED_SAMPLE_DAY")
            if arrival_us < exchange_us:
                continue  # anomalous arrival order cannot be used causally
            parsed = parse_instrument(row["symbol"])
            if parsed is None:
                continue
            try:
                bid, ask = float(row["bid_price"]), float(row["ask_price"])
                bs, az = float(row["bid_amount"]), float(row["ask_amount"])
            except (TypeError, ValueError):
                continue
            if not all(math.isfinite(v) for v in (bid, ask, bs, az)):
                continue
            if not (0 < bid < ask and bs > 0 and az > 0):
                continue
            all_rows.append((arrival_us, exchange_us, parsed[0], parsed[1],
                             parsed[2], row["symbol"]))
    return manifest, all_rows


def readiness(root):
    manifest, quotes = verify_and_load(root)
    decisions = monday_decisions()
    if len(decisions) != 94:
        raise ValueError(f"UNEXPECTED_WEEKLY_DECISION_COUNT:{len(decisions)}")
    # A 21-day-minimum option opened in the final three TRAIN Mondays cannot
    # expire inside TRAIN. Exclude these right-censored entries from *economic*
    # source-coverage denominator; never read validation to settle them.
    min_life_us = 21 * 86400 * 1_000_000
    eligible = [t for t in decisions if t * 1000 + min_life_us < END * 1000]
    censored = [t for t in decisions if t not in eligible]
    if len(eligible) != 91 or len(censored) != 3:
        raise ValueError("UNEXPECTED_TRAIN_EXPIRY_CENSORING")
    coverage = {str(f): {a: 0 for a in REQUIRED_ASSETS} for f in range(1, 6)}
    selected = []
    for t in eligible:
        f = next((i for i, (lo, hi) in enumerate(zip(FOLD_EDGES, FOLD_EDGES[1:]), 1)
                  if lo <= t < hi), None)
        if f is None:
            raise ValueError("DECISION_OUTSIDE_FROZEN_FOLDS")
        t_us = t * 1000
        # Only data received BEFORE the decision may be used. No nearest-future interpolation.
        groups = defaultdict(set)
        for arrival, exchange, asset, expiry, strike, symbol in quotes:
            if not (0 <= t_us - arrival <= MAX_AGE_US and exchange <= arrival):
                continue
            if not (21 * 86400 * 1_000_000 <= expiry - t_us <= 45 * 86400 * 1_000_000
                    and expiry < END * 1000):
                continue
            groups[(asset, expiry)].add(strike)
        for asset in REQUIRED_ASSETS:
            # Two distinct puts in one expiration: necessary, NOT sufficient for executable vertical.
            if any(a == asset and len(strikes) >= 2 for (a, _), strikes in groups.items()):
                coverage[str(f)][asset] += 1
                selected.append({"decision_ms": t, "asset": asset, "fold": f})
    folds = {a: sum(coverage[str(f)][a] > 0 for f in range(1, 6))
             for a in REQUIRED_ASSETS}
    # Even all weekly quote groups would NOT establish native multiplier, fee tier,
    # spot hedging, option margin, or actual hypothetical execution fills.
    return {
        "schema": "V99_I1_ORIGINAL_SAMPLE_CAUSAL_EXECUTION_READINESS_V1",
        "status": "BLOCKED_NO_FULL_FIVE_FOLD_EXECUTABLE_OPTIONS_SOURCE",
        "source_kind": "ARCHIVED_PARTIAL_TARDIS_RECONSTRUCTED_EXCHANGE_QUOTES",
        "original_sample_rows": sum(x["rows_partial"] for x in manifest["days"]),
        "valid_two_sided_source_rows": len(quotes),
        "train_decision_weeks": len(decisions),
        "maturity_eligible_decision_weeks": len(eligible),
        "right_censored_decision_weeks": len(censored),
        "right_censored_decision_utc": [datetime.fromtimestamp(t / 1000, UTC).isoformat() for t in censored],
        "required_asset_weekly_pairs": 2 * len(eligible),
        "causal_two_strike_asset_weeks": len(selected),
        "five_fold_coverage": coverage,
        "folds_with_any_candidate_quotes": folds,
        "complete_five_fold_coverage": False,
        "native_fee_tier_authenticated": False,
        "native_contract_multiplier_authenticated": False,
        "native_margin_settlement_authenticated": False,
        "economic_train_executed": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
        "next_dependency": "Authenticated complete 2021-12-09..2023-09-30 BTC+ETH options bid/ask/sizes and arrival timestamps, original contract multipliers/settlement/margin and historical fees",
    }


def main(root, output):
    report = readiness(root)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "i1_execution_readiness.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    assert report["status"].startswith("BLOCKED_")
    assert not report["economic_train_executed"] and not report["promotion_authorized"]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_execution_readiness ORIGINAL_SAMPLE_ROOT OUTPUT")
    main(sys.argv[1], sys.argv[2])
