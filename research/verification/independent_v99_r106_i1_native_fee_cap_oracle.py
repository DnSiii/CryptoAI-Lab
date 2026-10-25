"""Independent Decimal fee-cap replay on original Deribit source inputs.

Does not import primary fee module. No historical 2021-2023 fee attestation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

SCHEDULES = {
    "published_2019_example": (Decimal("0.0004"), Decimal("0.0002"), Decimal("0.20")),
    "current_2026_example": (Decimal("0.0003"), Decimal("0.00015"), Decimal("0.125")),
}
D = lambda v: Decimal(str(v))
K = lambda r: (r["decision_utc"], r["short_symbol"], r["long_symbol"])


def audit(credit_path, terminal_path, output_path):
    raw_c, raw_t = Path(credit_path).read_bytes(), Path(terminal_path).read_bytes()
    source = json.loads(raw_c)
    terminal = json.loads(raw_t)
    out = json.loads(Path(output_path).read_text())
    assert source["schema"] == "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
    assert terminal["schema"] == "V99_I1_ORIGINAL_QUOTE_DELIVERY_TERMINAL_DIAGNOSTIC_V1"
    assert out["schema"] == "V99_I1_ORIGINAL_NATIVE_FEE_CAP_ENVELOPE_V1"
    assert out["source_credit_sha256"] == hashlib.sha256(raw_c).hexdigest()
    assert out["source_terminal_sha256"] == hashlib.sha256(raw_t).hexdigest()
    assert terminal["original_credit_sha256"] == hashlib.sha256(raw_c).hexdigest()
    assert (out["source_pairs"], out["sampled_asset_weeks"],
            out["required_asset_weeks"], out["certified_full_lifecycles"]) == (46, 4, 182, 0)
    assert out["status"] == "ILLUSTRATIVE_NATIVE_FEE_FORMULA_ONLY_HOLD"
    for k in ("historical_fee_tier_certified", "native_contract_quantity_certified",
              "economic_train_run", "roi_calculated", "validation_opened",
              "holdout_opened", "orders_enabled", "promotion_authorized"):
        assert out[k] is False, "FALSE_HISTORICAL_FEE_OR_PERFORMANCE_CLAIM"
    assert set(out["fee_examples"]) == set(SCHEDULES)
    assert len(source["rows"]) == len(terminal["rows"]) == len(out["rows"]) == 46
    s_rows = {K(x): x for x in source["rows"]}
    t_rows = {K(x): x for x in terminal["rows"]}
    o_rows = {K(x): x for x in out["rows"]}
    assert len(s_rows) == len(t_rows) == len(o_rows) == 46
    assert set(s_rows) == set(t_rows) == set(o_rows)
    counters = {s: {a: defaultdict(int) for a in ("BTC", "ETH")} for s in SCHEDULES}
    for key, src in s_rows.items():
        term, got = t_rows[key], o_rows[key]
        asset = src["asset"]
        assert asset in ("BTC", "ETH")
        assert term["asset"] == got["asset"] == asset
        assert got["expiry_utc"] == src["expiry_utc"]
        assert got["historical_native_quantity"] is None
        assert got["historical_fill"] is False
        assert got["actual_account_fee"] is None
        strike_hi, strike_lo = D(src["short_strike_usd"]), D(src["long_strike_usd"])
        price = D(term["delivery_index_usd"])
        assert strike_hi > strike_lo > 0 and price > 0
        short_bid, long_ask = D(src["short_bid_coin"]), D(src["long_ask_coin"])
        assert short_bid > 0 and long_ask > 0
        assert short_bid - long_ask == D(src["gross_credit_coin_per_source_unit_assumption"])
        due_short = max(Decimal(0), strike_hi-price) / price
        due_long = max(Decimal(0), strike_lo-price) / price
        assert ((max(Decimal(0), strike_hi-price) - max(Decimal(0), strike_lo-price)) / price
                == D(term["intrinsic_coin_per_assumed_unit"]))
        for label, (base, delivery, cap) in SCHEDULES.items():
            assert out["fee_examples"][label] == {
                "entry_per_unit": str(base),
                "delivery_per_unit": str(delivery),
                "cap_fraction": str(cap),
            }
            values = {}
            caps = {"entry_cap_hit_legs": 0, "delivery_cap_hit_legs": 0}
            for leg, entry_value, due_value in (
                ("short", short_bid, due_short), ("long", long_ask, due_long)
            ):
                entry_cost = min(base, cap*entry_value)
                expiry_cost = min(delivery, cap*due_value)
                values[leg+"_entry_coin"] = entry_cost
                values[leg+"_delivery_coin"] = expiry_cost
                caps["entry_cap_hit_legs"] += int(entry_value > 0 and cap*entry_value < base)
                caps["delivery_cap_hit_legs"] += int(due_value > 0 and cap*due_value < delivery)
            row = got["fees"][label]
            for name, expected in values.items():
                assert D(row[name]) == expected, "INCORRECT_NATIVE_FEE_"+name
                assert Decimal(0) <= expected <= (base if "entry" in name else delivery)
            assert D(row["total_entry_coin_per_assumed_unit"]) == (
                values["short_entry_coin"]+values["long_entry_coin"])
            assert D(row["total_delivery_coin_per_assumed_unit"]) == (
                values["short_delivery_coin"]+values["long_delivery_coin"])
            assert row["entry_cap_hit_legs"] == caps["entry_cap_hit_legs"]
            assert row["delivery_cap_hit_legs"] == caps["delivery_cap_hit_legs"]
            counters[label][asset]["pairs"] += 1
            for c in caps:
                counters[label][asset][c] += caps[c]
    for label in SCHEDULES:
        for asset in ("BTC", "ETH"):
            assert out["counts_by_asset_not_mixed_currency"][label][asset] == dict(
                counters[label][asset])
    print(json.dumps({"independent_original_fee_replay": "PASS", "pairs": 46,
                      "historical_fee_certified": False,
                      "counts_by_asset": out["counts_by_asset_not_mixed_currency"],
                      "promotion": False}, sort_keys=True))
    return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_native_fee_cap_oracle CREDIT TERMINAL RESULT")
    audit(*sys.argv[1:])
