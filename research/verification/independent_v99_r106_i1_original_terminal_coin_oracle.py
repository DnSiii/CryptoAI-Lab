"""Independent original quote/delivery coin terminal diagnostic oracle.

Does NOT import the production calculation. No trade, NAV, ROI, paper or order.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

D = lambda x: Decimal(str(x))
START, END = date(2021, 12, 9), date(2023, 10, 1)
COST = {"severe": Decimal("0.0048"), "supersevere": Decimal("0.0096")}
KEY = lambda r: (r["decision_utc"], r["short_symbol"], r["long_symbol"])


def audit(credit_file, index_file, handoff_file, delivery_file, result_file):
    paths = [Path(p) for p in (credit_file, index_file, handoff_file, delivery_file)]
    blobs = [p.read_bytes() for p in paths]
    credit, index, handoff, delivery = [json.loads(b) for b in blobs]
    output = json.loads(Path(result_file).read_text())
    shas = [hashlib.sha256(b).hexdigest() for b in blobs]
    for field, value in zip(("original_credit_sha256",
                             "original_index_binding_sha256",
                             "original_native_handoff_sha256",
                             "original_delivery_sha256"), shas):
        assert output[field] == value, "SOURCE_HASH_MISMATCH"
    assert index["original_credit_report_sha256"] == shas[0]
    assert handoff["source_credit_sha256"] == shas[0]
    assert handoff["source_index_sha256"] == shas[1]
    assert output["schema"] == "V99_I1_ORIGINAL_QUOTE_DELIVERY_TERMINAL_DIAGNOSTIC_V1"
    assert output["status"] == "ORIGINAL_SOURCE_TERMINAL_DIAGNOSTIC_ONLY_HOLD"
    assert (output["source_pairs"], output["sampled_asset_weeks"],
            output["required_asset_weeks"], output["native_executable_pairs"],
            output["certified_full_lifecycles"]) == (46, 4, 182, 0, 0)
    for name in ("economic_train_run", "validation_opened", "holdout_opened",
                 "orders_enabled", "promotion_authorized", "roi_calculated",
                 "historical_fee_margin_or_size_certified"):
        assert output[name] is False, "UNAUTHORIZED_ECONOMIC_CLAIM"
    assert len(output["rows"]) == len(credit["rows"]) == len(handoff["rows"]) == 46
    assert len(index["pairs"]) == 46
    index_keys = {KEY(p) for p in index["pairs"]}
    handoff_keys = {KEY(p) for p in handoff["rows"]}
    assert len(index_keys) == len(handoff_keys) == 46
    assert set(delivery["assets"]) == {"btc_usd", "eth_usd"}
    calendar = [(START + timedelta(days=i)).isoformat() for i in range((END - START).days)]
    settlement = {}
    for a, payload in delivery["assets"].items():
        assert payload["index"] == a
        assert payload["train_start"] == START.isoformat()
        assert payload["train_end_exclusive"] == END.isoformat()
        assert [x["date"] for x in payload["records"]] == calendar
        settlement[a] = {r["date"]: D(r["delivery_price"]) for r in payload["records"]}
        assert all(x > 0 and x.is_finite() for x in settlement[a].values())
    produced = {KEY(r): r for r in output["rows"]}
    assert len(produced) == 46
    sums = {scenario: [] for scenario in COST}
    for row in credit["rows"]:
        k = KEY(row)
        assert k in index_keys and k in handoff_keys and k in produced
        r = produced[k]
        t = datetime.fromisoformat(row["decision_utc"]).astimezone(timezone.utc)
        e = datetime.fromisoformat(row["expiry_utc"]).astimezone(timezone.utc)
        assert date(2021, 12, 9) <= t.date() < e.date() < END
        assert t.weekday() == 0 and e.hour == 8 and e.minute == 0
        assert r["expiry_utc"] == row["expiry_utc"] and r["asset"] == row["asset"]
        high, low = D(row["short_strike_usd"]), D(row["long_strike_usd"])
        assert high > low
        price = settlement[row["asset"].lower() + "_usd"][e.date().isoformat()]
        intrinsic = max(Decimal(0), high - price) - max(Decimal(0), low - price)
        due_coin = intrinsic / price
        gross = D(row["short_bid_coin"]) - D(row["long_ask_coin"])
        assert gross == D(row["gross_credit_coin_per_source_unit_assumption"])
        assert D(r["delivery_index_usd"]) == price
        assert D(r["intrinsic_usd_per_assumed_unit"]) == intrinsic
        assert D(r["intrinsic_coin_per_assumed_unit"]) == due_coin
        assert D(r["gross_quoted_credit_coin_per_assumed_unit"]) == gross
        assert r["historical_fill"] is False and r["account_pnl"] is None
        for scenario, cost in COST.items():
            opening = gross - cost
            assert opening == D(row["net_credit_coin_per_source_unit_assumption"][scenario])
            delta = opening - due_coin
            assert D(r["modeled_terminal_coin_delta_per_assumed_unit"][scenario]) == delta
            sums[scenario].append(delta)
    for scenario, values in sums.items():
        s = output["summary"][scenario]
        assert s["positive_conditional_deltas"] == sum(v > 0 for v in values)
        assert s["nonpositive_conditional_deltas"] == sum(v <= 0 for v in values)
        assert D(s["worst_coin_delta_per_assumed_unit"]) == min(values)
        assert D(s["sum_coin_deltas_across_untradeable_source_units"]) == sum(values)
    print(json.dumps({"independent_original_source_replay": "PASS",
                      "pairs": 46,
                      "summary": output["summary"],
                      "native_fills": 0, "roi": False, "promotion": False},
                     sort_keys=True))
    return True


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_original_terminal_coin_oracle CREDIT INDEX HANDOFF DELIVERY RESULT")
    audit(*sys.argv[1:])
