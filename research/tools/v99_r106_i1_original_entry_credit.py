"""Original Deribit BTC/ETH put vertical quoted credit screen, SOURCE ONLY.

Consumes independently verified real minute gzip and first-party instrument bytes.
No order, fill, lot conversion, historical fee, margin, PnL or trade selection.
Protocol: research/V99_R106_I1_REAL_ENTRY_CREDIT_SCREEN_PREREG_20261025.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import (
    historical_price_grid_ok, native_contracts,
)
from research.verification.independent_v99_r106_i1_sunday_ticker_oracle import verify

# Previously fixed modeled stress paths; NOT authenticated historical Deribit fees.
FRICTION_PER_LEG = {
    "severe": Decimal("0.0024"),
    "supersevere": Decimal("0.0048"),
}
TRAIN_STOP = datetime(2023, 10, 1, tzinfo=timezone.utc)


def screen(ticker_root, native_root, output):
    ticker_root, native_root, output = map(Path, (ticker_root, native_root, output))
    assert verify(ticker_root) == 4, "INCOMPLETE_OR_CORRUPT_ORIGINAL_SUNDAY_SOURCE"
    native = native_contracts(native_root)
    original = json.loads((ticker_root / "report.json").read_text())
    rows = []
    rejected = {"native_asof_or_tick": 0}
    for day in original["days"]:
        decision = datetime.fromisoformat(day["decision_utc"])
        if not decision < TRAIN_STOP:
            raise ValueError("SEALED_FUTURE_PARTITION")
        decision_ms = int(decision.timestamp() * 1000)
        groups = defaultdict(list)
        for book in day["last_eligible_books"]:
            meta = native[book["asset"]].get(book["symbol"])
            expiry = datetime.fromisoformat(book["expiry"])
            valid = bool(
                meta is not None
                and meta["creation_timestamp"] <= decision_ms
                and meta["expiration_timestamp"] == int(expiry.timestamp() * 1000)
                and meta["settlement_currency"] == book["asset"]
                and Decimal(str(meta["strike"])) == Decimal(book["strike"])
                and all(meta[k] is not None and Decimal(str(meta[k])) > 0
                        for k in ("contract_size", "min_trade_amount", "tick_size"))
                and historical_price_grid_ok(meta, decision, book["bid_coin"], book["ask_coin"])
            )
            if not valid:
                rejected["native_asof_or_tick"] += 1
                continue
            groups[(book["asset"], book["expiry"])].append((Decimal(book["strike"]), book, meta))
        for (asset, expiry), group in sorted(groups.items()):
            group.sort(key=lambda x: x[0])
            for (low_k, low, low_meta), (high_k, high, high_meta) in zip(group, group[1:]):
                if not low_k < high_k:
                    raise ValueError("DUPLICATED_NATIVE_STRIKE")
                gross = Decimal(high["bid_coin"]) - Decimal(low["ask_coin"])
                net = {s: gross - Decimal(2) * friction for s, friction in FRICTION_PER_LEG.items()}
                rows.append({
                    "decision_utc": day["decision_utc"],
                    "asset": asset,
                    "expiry_utc": expiry,
                    "short_symbol": high["symbol"],
                    "long_symbol": low["symbol"],
                    "short_strike_usd": str(high_k),
                    "long_strike_usd": str(low_k),
                    "width_usd": str(high_k - low_k),
                    "short_bid_coin": high["bid_coin"],
                    "long_ask_coin": low["ask_coin"],
                    "short_bid_size_source_units": high["bid_size_source_units"],
                    "long_ask_size_source_units": low["ask_size_source_units"],
                    "short_arrival_us": high["arrival_us"],
                    "long_arrival_us": low["arrival_us"],
                    "short_exchange_us": high["exchange_us"],
                    "long_exchange_us": low["exchange_us"],
                    "short_native_contract_size": str(high_meta["contract_size"]),
                    "long_native_contract_size": str(low_meta["contract_size"]),
                    "short_native_min_trade_amount": str(high_meta["min_trade_amount"]),
                    "long_native_min_trade_amount": str(low_meta["min_trade_amount"]),
                    "gross_credit_coin_per_source_unit_assumption": str(gross),
                    "net_credit_coin_per_source_unit_assumption": {s: str(v) for s, v in net.items()},
                    "positive_net_credit_screen": {s: v > 0 for s, v in net.items()},
                })
    result = {
        "schema": "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1",
        "original_ticker_report_sha256": hashlib.sha256(
            (ticker_root / "report.json").read_bytes()).hexdigest(),
        "original_native_registry_report_sha256": hashlib.sha256(
            (native_root / "native_instrument_registry.json").read_bytes()).hexdigest(),
        "sample_asset_weeks_with_original_two_strike_books": 4,
        "required_train_asset_weeks": 182,
        "adjacent_quote_pairs": len(rows),
        "positive_net_credit_pairs": {
            s: sum(row["positive_net_credit_screen"][s] for row in rows)
            for s in FRICTION_PER_LEG
        },
        "native_rejections": rejected,
        "rows": rows,
        "costs_historical_authenticated": False,
        "native_lot_and_quote_size_units_certified": False,
        "original_full_lifecycle_quotes_certified": False,
        "original_delivery_and_margin_certified": False,
        "economic_train_run": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
        "status": "SOURCE_ONLY_FOUR_OF_182_NO_EXECUTION_OR_ECONOMICS",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "adjacent_quote_pairs": result["adjacent_quote_pairs"],
        "positive_net_credit_pairs": result["positive_net_credit_pairs"],
        "native_rejections": rejected,
        "economic_train_run": False, "promotion": False,
    }))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_entry_credit TICKER_ROOT NATIVE_ROOT OUTPUT")
    screen(*sys.argv[1:])
