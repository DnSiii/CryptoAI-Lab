"""Independent original-gzip/native-byte replay of I1 entry credit screen.

Does NOT import the primary credit screener, cost constants or pairing function.
This checks quote-source integrity and arithmetic, not real fills or historical ROI.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.verification.independent_v99_r106_i1_sunday_ticker_oracle import verify as verify_original_gzip
from research.verification.independent_v99_r106_i1_full_archive_intake import (
    original_native_lookup, independently_check_historical_ticks,
)

COST = {"severe": Decimal("0.0024"), "supersevere": Decimal("0.0048")}


def audit(ticker_root, native_root, output):
    ticker_root, native_root, output = map(Path, (ticker_root, native_root, output))
    assert verify_original_gzip(ticker_root) == 4
    native = original_native_lookup(native_root)  # independent ORIGINAL Deribit bytes
    ticker = json.loads((ticker_root / "report.json").read_text())
    result = json.loads(output.read_text())
    assert result["schema"] == "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
    assert result["original_ticker_report_sha256"] == hashlib.sha256(
        (ticker_root / "report.json").read_bytes()).hexdigest()
    assert result["original_native_registry_report_sha256"] == hashlib.sha256(
        (native_root / "native_instrument_registry.json").read_bytes()).hexdigest()
    assert result["sample_asset_weeks_with_original_two_strike_books"] == 4
    assert result["required_train_asset_weeks"] == 182
    assert result["status"] == "SOURCE_ONLY_FOUR_OF_182_NO_EXECUTION_OR_ECONOMICS"
    for flag in ("costs_historical_authenticated", "native_lot_and_quote_size_units_certified",
                 "original_full_lifecycle_quotes_certified", "original_delivery_and_margin_certified",
                 "economic_train_run", "validation_opened", "holdout_opened",
                 "orders_enabled", "promotion_authorized"):
        assert result[flag] is False
    expected = []
    rejected = 0
    for day in ticker["days"]:
        decision = datetime.fromisoformat(day["decision_utc"]).astimezone(timezone.utc)
        assert decision < datetime(2023, 10, 1, tzinfo=timezone.utc)
        groups = defaultdict(dict)
        for b in day["last_eligible_books"]:
            rec = native[b["asset"]].get(b["symbol"])
            valid = rec is not None
            if valid:
                valid = (
                    int(rec["creation_timestamp"]) <= int(decision.timestamp()*1000)
                    and int(rec["expiration_timestamp"]) == int(datetime.fromisoformat(b["expiry"]).timestamp()*1000)
                    and rec["settlement_currency"] == b["asset"]
                    and Decimal(str(rec["strike"])) == Decimal(b["strike"])
                    and all(rec.get(k) is not None and Decimal(str(rec[k])) > 0
                            for k in ("contract_size", "min_trade_amount", "tick_size"))
                    and independently_check_historical_ticks(
                        rec, decision, (b["bid_coin"], b["ask_coin"]))
                )
            if not valid:
                rejected += 1
                continue
            strike = Decimal(b["strike"])
            assert strike not in groups[(b["asset"], b["expiry"])]
            groups[(b["asset"], b["expiry"])][strike] = (b, rec)
        for (asset, expiry) in sorted(groups):
            book_by_strike = groups[(asset, expiry)]
            levels = sorted(book_by_strike)
            for i in range(len(levels)-1):
                low_k, high_k = levels[i], levels[i+1]
                low, lm = book_by_strike[low_k]
                high, hm = book_by_strike[high_k]
                credit = Decimal(high["bid_coin"]) - Decimal(low["ask_coin"])
                net = {s: credit - 2 * f for s, f in COST.items()}
                expected.append({
                    "decision_utc": day["decision_utc"], "asset": asset, "expiry_utc": expiry,
                    "short_symbol": high["symbol"], "long_symbol": low["symbol"],
                    "short_strike_usd": str(high_k), "long_strike_usd": str(low_k),
                    "width_usd": str(high_k-low_k),
                    "short_bid_coin": high["bid_coin"], "long_ask_coin": low["ask_coin"],
                    "short_bid_size_source_units": high["bid_size_source_units"],
                    "long_ask_size_source_units": low["ask_size_source_units"],
                    "short_arrival_us": high["arrival_us"], "long_arrival_us": low["arrival_us"],
                    "short_exchange_us": high["exchange_us"], "long_exchange_us": low["exchange_us"],
                    "short_native_contract_size": str(hm["contract_size"]),
                    "long_native_contract_size": str(lm["contract_size"]),
                    "short_native_min_trade_amount": str(hm["min_trade_amount"]),
                    "long_native_min_trade_amount": str(lm["min_trade_amount"]),
                    "gross_credit_coin_per_source_unit_assumption": str(credit),
                    "net_credit_coin_per_source_unit_assumption": {s: str(v) for s,v in net.items()},
                    "positive_net_credit_screen": {s: v > 0 for s,v in net.items()},
                })
    assert result["rows"] == expected, "ORIGINAL_QUOTE_PAIR_OR_CREDIT_MISMATCH"
    assert result["adjacent_quote_pairs"] == len(expected)
    assert result["native_rejections"] == {"native_asof_or_tick": rejected}
    for s in COST:
        assert result["positive_net_credit_pairs"][s] == sum(
            r["positive_net_credit_screen"][s] for r in expected)
    return {
        "independent_original_quote_pairs": len(expected),
        "positive_net_credit_pairs": result["positive_net_credit_pairs"],
        "native_rejections": rejected,
        "original_gzip_replayed": True, "original_native_bytes_replayed": True,
        "economic_train": False, "promotion": False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_entry_credit_oracle TICKER_ROOT NATIVE_ROOT OUTPUT")
    print(json.dumps(audit(*sys.argv[1:]), sort_keys=True))
