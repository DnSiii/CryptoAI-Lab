"""Independent original-source lot-depth oracle, not an economic backtest.

Does not import the primary calculator. No ROI, fills, orders or promotion.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.verification.independent_v99_r106_i1_historical_instruments import audit as original_native_audit

END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def audit(credit_path, native_root, index_path, fee_path, result_path):
    credit_path, native_root, index_path, fee_path, result_path = (
        Path(credit_path), Path(native_root), Path(index_path), Path(fee_path), Path(result_path))
    original_native_audit(native_root)
    raw = [p.read_bytes() for p in (credit_path, native_root / "native_instrument_registry.json",
                                    index_path, fee_path)]
    credit, native, index, fee = [json.loads(b) for b in raw]
    result = json.loads(result_path.read_text())
    expected_hashes = {
        "source_credit_sha256": hashlib.sha256(raw[0]).hexdigest(),
        "source_native_registry_sha256": hashlib.sha256(raw[1]).hexdigest(),
        "source_index_sha256": hashlib.sha256(raw[2]).hexdigest(),
        "source_fee_sha256": hashlib.sha256(raw[3]).hexdigest(),
    }
    for name, value in expected_hashes.items():
        assert result[name] == value, "FORGED_SOURCE_IDENTITY"
    assert credit["original_native_registry_report_sha256"] == expected_hashes["source_native_registry_sha256"]
    assert index["original_credit_report_sha256"] == expected_hashes["source_credit_sha256"]
    assert fee["source_credit_sha256"] == expected_hashes["source_credit_sha256"]
    assert result["schema"] == "V99_I1_ORIGINAL_NATIVE_MINIMUM_DEPTH_SOURCE_ONLY_V1"
    assert result["status"] == "SOURCE_ONLY_PROVISIONAL_NATIVE_MINIMUM_DEPTH_NO_EXECUTION"
    assert result["original_pairs"] == 46 and result["sampled_asset_weeks"] == 4
    assert result["required_asset_weeks"] == 182 and result["certified_full_lifecycles"] == 0
    assert len(result["rows"]) == len(credit["rows"]) == len(index["pairs"]) == len(fee["rows"]) == 46
    for flag in ("historical_quote_size_units_certified", "historical_native_minimum_asof_certified",
                 "historical_fee_margin_certified", "economic_train_run", "roi_calculated",
                 "validation_opened", "holdout_opened", "orders_enabled", "promotion_authorized"):
        assert result[flag] is False, "FORGED_ECONOMIC_PERMISSION"
    original_registry = {}
    for asset in ("BTC", "ETH"):
        original_registry[asset] = {r["instrument_name"]: r for r in native["registry"][asset]}
    pair_key = lambda r: (r["decision_utc"], r["short_symbol"], r["long_symbol"])
    assert {pair_key(r) for r in credit["rows"]} == {pair_key(r) for r in index["pairs"]} == {
        pair_key(r) for r in fee["rows"]}
    assert len({pair_key(r) for r in credit["rows"]}) == 46
    expected = {}
    counts = {a: Counter() for a in ("BTC", "ETH")}
    for r in credit["rows"]:
        asset = r["asset"]
        assert asset in counts
        when = datetime.fromisoformat(r["decision_utc"]).astimezone(timezone.utc)
        assert when < END
        s = original_registry[asset][r["short_symbol"]]
        l = original_registry[asset][r["long_symbol"]]
        for item in (s, l):
            assert item["settlement_currency"] == asset and item["option_type"] == "put"
            assert Decimal(str(item["contract_size"])) == Decimal("1")
            assert int(item["creation_timestamp"]) <= int(when.timestamp() * 1000)
            assert int(item["expiration_timestamp"]) == int(datetime.fromisoformat(r["expiry_utc"]).timestamp() * 1000)
        minimum = max(Decimal(str(s["min_trade_amount"])), Decimal(str(l["min_trade_amount"])))
        bid = Decimal(str(r["short_bid_size_source_units"]))
        ask = Decimal(str(r["long_ask_size_source_units"]))
        assert all(x.is_finite() and x > 0 for x in (minimum, bid, ask))
        displayed = min(bid, ask)
        feasible = displayed >= minimum
        counts[asset]["pairs"] += 1
        counts[asset]["provisional_minimum_depth_sufficient"] += int(feasible)
        expected[pair_key(r)] = {
            "decision_utc": r["decision_utc"], "asset": asset,
            "short_symbol": r["short_symbol"], "long_symbol": r["long_symbol"],
            "short_arrival_us": int(r["short_arrival_us"]),
            "long_arrival_us": int(r["long_arrival_us"]),
            "short_displayed_source_units": str(bid),
            "long_displayed_source_units": str(ask),
            "minimum_displayed_source_units": str(displayed),
            "minimum_native_order_units": str(minimum),
            "short_native_contract_size_coin": str(Decimal(str(s["contract_size"]))),
            "long_native_contract_size_coin": str(Decimal(str(l["contract_size"]))),
            "provisional_minimum_depth_sufficient": feasible,
            "quote_source_units_historically_certified": False,
            "historical_native_minimum_asof_certified": False,
        }
    actual = {pair_key(r): r for r in result["rows"]}
    assert len(actual) == 46 and actual == expected, "FORGED_NATIVE_QUANTITY_OR_LOT"
    assert result["counts_by_asset"] == {a: dict(counts[a]) for a in ("BTC", "ETH")}
    return {"verified_pairs": 46, "counts_by_asset": result["counts_by_asset"],
            "economic_train": False, "promotion": False}


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_native_minimum_depth CREDIT NATIVE_ROOT INDEX FEE RESULT")
    print(json.dumps(audit(*sys.argv[1:]), sort_keys=True))
