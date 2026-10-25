"""Independent original-byte audit of the native size execution veto.

No import of the primary handoff; verifies archived raw gzip and native
instrument originals through separately implemented source oracles.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.verification.independent_v99_r106_i1_index_binding_oracle import audit as original_index_oracle
from research.verification.independent_v99_r106_i1_entry_credit_oracle import audit as original_credit_oracle
from research.verification.independent_v99_r106_i1_full_archive_intake import original_native_lookup

FIELDS = ("source_only", "economic_train_run", "validation_opened",
          "holdout_opened", "orders_enabled", "promotion_authorized")

def verify(ticker_root, native_root, credit_path, index_path, handoff_path):
    ticker_root, native_root, credit_path, index_path, handoff_path = map(
        Path, (ticker_root, native_root, credit_path, index_path, handoff_path))
    # These two separate source implementations replay original gzip and
    # first-party native registry and detect forged source index/credit.
    original_credit_oracle(ticker_root, native_root, credit_path)
    original_index_oracle(ticker_root, native_root, credit_path, index_path)
    native = original_native_lookup(native_root)
    credit = json.loads(credit_path.read_bytes())
    idx = json.loads(index_path.read_bytes())
    report = json.loads(handoff_path.read_bytes())
    assert report["schema"] == "V99_I1_ORIGINAL_NATIVE_SIZE_EXECUTION_HANDOFF_V1"
    for field, path in (("source_credit_sha256", credit_path),
                        ("source_index_sha256", index_path),
                        ("source_native_registry_sha256", native_root/"native_instrument_registry.json")):
        assert report[field] == hashlib.sha256(path.read_bytes()).hexdigest(), field
    assert report["source_only"] is True
    assert all(report[k] is False for k in FIELDS if k != "source_only")
    assert report["required_asset_weeks"] == 182
    assert report["sampled_asset_weeks"] == 4
    assert report["source_pairs"] == len(credit["rows"]) == len(idx["pairs"]) == 46
    assert report["native_executable_pairs"] == 0
    assert report["status"] == "SOURCE_ONLY_NATIVE_QUANTITY_AND_ATOMIC_EXECUTION_UNCERTIFIED"
    assert report["blockers"] == [
        "historical_quote_size_unit_conversion_unverified",
        "historical_account_fee_tier_and_delivery_fee_unverified",
        "historical_coin_margin_and_liquidation_rules_unverified",
        "complete_entry_exit_or_settlement_depth_unavailable",
        "atomic_two_leg_fill_not_proven",
        "independent_self_financing_five_fold_economics_not_run",
    ]
    by_key = {(p["decision_utc"], p["short_symbol"], p["long_symbol"]): p
              for p in idx["pairs"]}
    assert len(by_key) == 46
    expected = []
    for pair in credit["rows"]:
        asset = pair["asset"]
        assert asset in ("BTC", "ETH")
        p = by_key[(pair["decision_utc"], pair["short_symbol"], pair["long_symbol"])]
        t = datetime.fromisoformat(pair["decision_utc"]).astimezone(timezone.utc)
        assert t < datetime(2023,10,1,tzinfo=timezone.utc) and t.weekday() == 0
        assert p["asset"] == asset
        a = int(pair["short_arrival_us"])
        b = int(pair["long_arrival_us"])
        x = int(pair["short_exchange_us"])
        y = int(pair["long_exchange_us"])
        end = int(t.timestamp()*1_000_000)
        assert p["short_arrival_us"] == a and p["long_arrival_us"] == b
        assert all(0 <= end-v <= 300_000_000 for v in (a,b,x,y))
        assert x <= a and y <= b
        source_bid = Decimal(pair["short_bid_size_source_units"])
        source_ask = Decimal(pair["long_ask_size_source_units"])
        assert source_bid.is_finite() and source_bid > 0
        assert source_ask.is_finite() and source_ask > 0
        short = native[asset][pair["short_symbol"]]
        long = native[asset][pair["long_symbol"]]
        for leg, record in (("short",short),("long",long)):
            assert Decimal(str(record["contract_size"])) == Decimal(
                pair[leg+"_native_contract_size"])
            assert Decimal(str(record["min_trade_amount"])) == Decimal(
                pair[leg+"_native_min_trade_amount"])
        expected.append({
            "decision_utc": pair["decision_utc"], "asset": asset,
            "short_symbol": pair["short_symbol"], "long_symbol": pair["long_symbol"],
            "short_bid_size_source_units": source_bid,
            "long_ask_size_source_units": source_ask,
            "minimum_displayed_source_units": min(source_bid,source_ask),
            "short_native_contract_size": Decimal(str(short["contract_size"])),
            "long_native_contract_size": Decimal(str(long["contract_size"])),
            "short_native_min_trade_amount": Decimal(str(short["min_trade_amount"])),
            "long_native_min_trade_amount": Decimal(str(long["min_trade_amount"])),
            "short_quote_age_ms": Decimal(end-a)/Decimal(1000),
            "long_quote_age_ms": Decimal(end-b)/Decimal(1000),
            "arrival_skew_ms": Decimal(abs(a-b))/Decimal(1000),
            "exchange_skew_ms": Decimal(abs(x-y))/Decimal(1000),
            "same_exact_index_price": p["same_exact_index_price"],
        })
    assert len(report["rows"]) == len(expected)
    for got, want in zip(report["rows"],expected):
        for k,v in want.items():
            if isinstance(v,Decimal):
                assert Decimal(str(got[k])) == v, "FORGED_SIZE_OR_TEMPORAL_FIELD:"+k
            else:
                assert got[k] == v, "FORGED_SOURCE_FIELD:"+k
        assert set(got) == set(want)|{
            "historical_native_contract_qty","two_leg_executable_fill","reason"}
        assert got["historical_native_contract_qty"] is None
        assert got["two_leg_executable_fill"] is False
        assert got["reason"] == "SOURCE_SIZE_NOT_CERTIFIED_AS_NATIVE_LOTS_AND_NO_ATOMIC_FILL"
    return {"original_pairs_independently_replayed":len(expected),
            "native_executable_pairs":0,
            "max_arrival_skew_ms":str(max(r["arrival_skew_ms"] for r in expected)),
            "max_quote_age_ms":str(max(max(r["short_quote_age_ms"],r["long_quote_age_ms"]) for r in expected)),
            "promotion":False,"economic_train":False}

if __name__ == "__main__":
    if len(sys.argv)!=6:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_native_quote_size_oracle TICKER NATIVE CREDIT INDEX HANDOFF")
    print(json.dumps(verify(*sys.argv[1:]),sort_keys=True))
