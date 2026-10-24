"""Original Deribit TRAIN-only daily-index overlap stress. Risk proxy, NO PnL/orders.

Precommitted: research/V99_R106_I1_OVERLAPPING_COIN_EXPOSURE_PREREG_20261024.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

D = lambda v: Decimal(str(v))
Q = Decimal("0.0000000001")
START, END = date(2021, 12, 9), date(2023, 10, 1)
FIRST = date(2021, 12, 13)
EDGES = [
    datetime(2021, 12, 9, tzinfo=timezone.utc),
    datetime(2022, 4, 20, 4, tzinfo=timezone.utc),
    datetime(2022, 8, 30, 9, tzinfo=timezone.utc),
    datetime(2023, 1, 9, 14, tzinfo=timezone.utc),
    datetime(2023, 5, 21, 19, tzinfo=timezone.utc),
    datetime(2023, 10, 1, tzinfo=timezone.utc),
]


def original_index(source):
    raw = Path(source).read_bytes()
    payload = json.loads(raw)
    if payload.get("schema") != "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1":
        raise ValueError("INVALID_ORIGINAL_INDEX_SCHEMA")
    if any(payload.get(k) is not True for k in
           ("read_only", "no_orders", "no_promotion", "not_executable_quotes")):
        raise ValueError("UNTRUSTED_ORIGINAL_INDEX_CLASSIFICATION")
    if set(payload.get("assets", {})) != {"btc_usd", "eth_usd"}:
        raise ValueError("MISSING_OR_EXTRA_ASSET")
    dates = [(START + timedelta(days=i)).isoformat()
             for i in range((END - START).days)]
    series = {}
    for asset in ("btc_usd", "eth_usd"):
        part = payload["assets"][asset]
        if (part.get("index") != asset or
                part.get("train_start") != START.isoformat() or
                part.get("train_end_exclusive") != END.isoformat() or
                not part.get("pages")):
            raise ValueError("UNBOUND_SOURCE_OR_FUTURE_DATA")
        rows = part.get("records", [])
        if [row.get("date") for row in rows] != dates:
            raise ValueError("MISSING_DUPLICATE_OR_FUTURE_INDEX_DAY")
        values = [D(row["delivery_price"]) for row in rows]
        if any(not x.is_finite() or x <= 0 for x in values):
            raise ValueError("INVALID_INDEX_PRICE")
        series[asset] = dict(zip((date.fromisoformat(x) for x in dates), values))
    return hashlib.sha256(raw).hexdigest(), series


def run(source):
    digest, index = original_index(source)
    decisions = [FIRST + timedelta(days=7 * i) for i in range(91)]
    if not all(START <= day - timedelta(days=1) < day
               and day + timedelta(days=21) < END for day in decisions):
        raise ValueError("SEALED_PARTITION_OR_EXPIRY")
    final_day = decisions[-1] + timedelta(days=21)
    rows, summary = [], {}
    for asset in ("btc_usd", "eth_usd"):
        strikes = [(day, day + timedelta(days=21),
                    D("0.95") * index[asset][day - timedelta(days=1)],
                    D("0.90") * index[asset][day - timedelta(days=1)])
                   for day in decisions]
        ever = set()
        expiry_breaches = 0
        peak_coin = D(0)
        max_ratio = D(0)
        max_active = 0
        breach_snapshots = 0
        fold_max = {str(i): D(0) for i in range(1, 6)}
        day = FIRST
        while day <= final_day:
            spot = index[asset][day]
            active = [(n, short, long, expiry)
                      for n, (entry, expiry, short, long) in enumerate(strikes)
                      if entry <= day <= expiry]
            if not active:
                raise ValueError("EMPTY_SNAPSHOT")
            obligation = D(0)
            for n, short, long, expiry in active:
                intrinsic = max(short - spot, D(0)) - max(long - spot, D(0))
                coin = intrinsic / spot
                obligation += coin
                if coin > D("0.05"):
                    ever.add(n)
                    if day == expiry:
                        expiry_breaches += 1
            reserve = D("0.05") * len(active)
            ratio = obligation / reserve
            fold_dt = datetime(day.year, day.month, day.day, 8, tzinfo=timezone.utc)
            fold = next((i for i in range(1, 6)
                         if EDGES[i - 1] <= fold_dt < EDGES[i]), None)
            if fold is None:
                raise ValueError("SNAPSHOT_OUTSIDE_TRAIN_FOLDS")
            peak_coin = max(peak_coin, obligation)
            max_ratio = max(max_ratio, ratio)
            max_active = max(max_active, len(active))
            fold_max[str(fold)] = max(fold_max[str(fold)], ratio)
            breach_snapshots += int(ratio > 1)
            rows.append({
                "asset": asset, "snapshot_date": day.isoformat(), "fold": fold,
                "active_positions": len(active),
                "aggregate_intrinsic_coin": str(obligation.quantize(Q)),
                "aggregate_to_earmarked_reserve": str(ratio.quantize(Q)),
                "earmarked_coin": str(reserve.quantize(Q)),
                "earmark_breached": ratio > 1,
            })
            day += timedelta(days=1)
        summary[asset] = {
            "daily_snapshots": (final_day - FIRST).days + 1,
            "max_active_positions": max_active,
            "max_aggregate_intrinsic_coin": str(peak_coin.quantize(Q)),
            "max_aggregate_to_earmarked_reserve": str(max_ratio.quantize(Q)),
            "earmark_breached_snapshots": breach_snapshots,
            "distinct_spreads_ever_exceeding_own_earmark": len(ever),
            "expiry_only_breaches": expiry_breaches,
            "max_ratio_by_snapshot_fold": {
                k: str(v.quantize(Q)) for k, v in fold_max.items()},
        }
    if (summary["btc_usd"]["expiry_only_breaches"] != 25 or
            summary["eth_usd"]["expiry_only_breaches"] != 27):
        raise ValueError("PRIOR_INDEPENDENT_EXPIRY_STRESS_MISMATCH")
    return {
        "schema": "I1_ORIGINAL_INDEX_OVERLAPPING_COIN_RISK_V1",
        "status": "HISTORICAL_UNDERLYING_SYNTHETIC_STRIKES_INTRINSIC_ONLY_NO_ECONOMICS",
        "source_sha256": digest,
        "original_index_first_party": True,
        "option_quotes_fills_or_native_margin": False,
        "economic_train_executed": False,
        "validation_opened": False, "holdout_opened": False,
        "promotion_authorized": False, "orders_enabled": False,
        "summary": summary, "daily": rows,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_overlapping_coin_exposure SOURCE_JSON OUTPUT_JSON")
    result = run(sys.argv[1])
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "summary": result["summary"],
                      "promotion": False, "option_roi": False}, sort_keys=True))
