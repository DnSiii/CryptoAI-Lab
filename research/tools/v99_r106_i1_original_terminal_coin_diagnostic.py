"""Original BTC/ETH quoted vertical entry -> original delivery-index diagnostic.

NO HISTORICAL TRADES OR PNL. Original quote sizes cannot be converted to native
lots; original exchange fees, margin/liquidation and holding-period execution
are not certified. No order, validation, holdout, paper or promotion paths.
Prereg: research/V99_R106_I1_ORIGINAL_TERMINAL_COIN_DIAGNOSTIC_PREREG_20261025.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

SCHEMA = "V99_I1_ORIGINAL_QUOTE_DELIVERY_TERMINAL_DIAGNOSTIC_V1"
END = datetime(2023, 10, 1, tzinfo=timezone.utc)
START_DAY = date(2021, 12, 9)
END_DAY = date(2023, 10, 1)
FRICTION = {"severe": Decimal("0.0048"), "supersevere": Decimal("0.0096")}


def dec(v):
    d = Decimal(str(v))
    if not d.is_finite():
        raise ValueError("NONFINITE_SOURCE")
    return d


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def run(credit_path, index_path, handoff_path, delivery_path, output):
    credit, credit_sha = read(credit_path)
    index, index_sha = read(index_path)
    hand, hand_sha = read(handoff_path)
    delivery, delivery_sha = read(delivery_path)
    if (credit.get("schema") != "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
        or index.get("schema") != "V99_I1_ORIGINAL_SAME_UPDATE_UNDERLYING_BINDING_V1"
        or hand.get("schema") != "V99_I1_ORIGINAL_NATIVE_SIZE_EXECUTION_HANDOFF_V1"
        or delivery.get("schema") != "V99_I1_DERIBIT_TRAIN_DELIVERY_PRICE_RECEIPTS_V1"
        or index.get("original_credit_report_sha256") != credit_sha
        or hand.get("source_credit_sha256") != credit_sha
        or hand.get("source_index_sha256") != index_sha):
        raise ValueError("UNBOUND_ORIGINAL_INPUTS")
    if (len(credit.get("rows", [])) != 46 or len(hand.get("rows", [])) != 46
        or credit.get("sample_asset_weeks_with_original_two_strike_books") != 4
        or hand.get("sampled_asset_weeks") != 4
        or hand.get("required_asset_weeks") != 182
        or hand.get("native_executable_pairs") != 0):
        raise ValueError("WRONG_FIXED_SOURCE_SAMPLE")
    if (any(credit.get(k) for k in ("economic_train_run", "orders_enabled", "promotion_authorized"))
        or any(hand.get(k) for k in ("economic_train_run", "validation_opened",
                                   "holdout_opened", "orders_enabled", "promotion_authorized"))
        or any(delivery.get(k) is not True for k in ("read_only", "no_orders",
                                                     "no_promotion", "not_executable_quotes"))):
        raise ValueError("FALSE_SOURCE_CLASSIFICATION")
    if set(delivery.get("assets", {})) != {"btc_usd", "eth_usd"}:
        raise ValueError("MISSING_DELIVERY_ASSET")
    prices = {}
    expected_days = [(START_DAY + timedelta(days=i)).isoformat()
                     for i in range((END_DAY - START_DAY).days)]
    for asset, source in delivery["assets"].items():
        if (source.get("index") != asset or source.get("train_start") != START_DAY.isoformat()
            or source.get("train_end_exclusive") != END_DAY.isoformat()
            or not source.get("pages")):
            raise ValueError("UNTRUSTED_DELIVERY_SOURCE")
        entries = source.get("records", [])
        if [r.get("date") for r in entries] != expected_days:
            raise ValueError("DELIVERY_GAP_DUPLICATE_OR_FUTURE")
        prices[asset] = {r["date"]: dec(r["delivery_price"]) for r in entries}
        if any(v <= 0 for v in prices[asset].values()):
            raise ValueError("BAD_DELIVERY_INDEX")
    key = lambda r: (r["decision_utc"], r["short_symbol"], r["long_symbol"])
    hand_rows = {key(r): r for r in hand["rows"]}
    index_rows = {key(r): r for r in index["pairs"]}
    if len(hand_rows) != 46 or len(index_rows) != 46:
        raise ValueError("DUPLICATE_ORIGINAL_PAIR")
    out = []
    for c in credit["rows"]:
        k = key(c)
        if k not in hand_rows or k not in index_rows:
            raise ValueError("UNBOUND_PAIR")
        h, ix = hand_rows[k], index_rows[k]
        if h["asset"] != c["asset"] or ix["asset"] != c["asset"]:
            raise ValueError("PAIR_ASSET_MISMATCH")
        if h["two_leg_executable_fill"] or h["historical_native_contract_qty"] is not None:
            raise ValueError("FABRICATED_EXECUTION")
        decision = datetime.fromisoformat(c["decision_utc"]).astimezone(timezone.utc)
        expiry = datetime.fromisoformat(c["expiry_utc"]).astimezone(timezone.utc)
        if not (datetime(2021, 12, 9, tzinfo=timezone.utc) <= decision < expiry < END
                and decision.weekday() == 0 and expiry.hour == 8
                and expiry.minute == 0 and expiry.second == 0):
            raise ValueError("SEALED_OR_NONSTANDARD_EXPIRY")
        asset = c["asset"]
        if asset not in ("BTC", "ETH"):
            raise ValueError("UNKNOWN_ASSET")
        high, low = dec(c["short_strike_usd"]), dec(c["long_strike_usd"])
        bid, ask = dec(c["short_bid_coin"]), dec(c["long_ask_coin"])
        if not high > low or bid <= 0 or ask <= 0:
            raise ValueError("BAD_NATIVE_QUOTE_OR_STRIKES")
        settlement = prices[asset.lower() + "_usd"][expiry.date().isoformat()]
        intrinsic_usd = max(high - settlement, Decimal(0)) - max(low - settlement, Decimal(0))
        intrinsic_coin = intrinsic_usd / settlement
        gross = bid - ask
        if gross != dec(c["gross_credit_coin_per_source_unit_assumption"]):
            raise ValueError("ORIGINAL_GROSS_CREDIT_MISMATCH")
        net = {}
        for scenario, friction in FRICTION.items():
            opening = gross - friction
            if opening != dec(c["net_credit_coin_per_source_unit_assumption"][scenario]):
                raise ValueError("ORIGINAL_MODELED_CREDIT_MISMATCH")
            net[scenario] = str(opening - intrinsic_coin)
        out.append({
            "decision_utc": c["decision_utc"], "expiry_utc": c["expiry_utc"],
            "asset": asset, "short_symbol": c["short_symbol"],
            "long_symbol": c["long_symbol"], "delivery_index_usd": str(settlement),
            "intrinsic_usd_per_assumed_unit": str(intrinsic_usd),
            "intrinsic_coin_per_assumed_unit": str(intrinsic_coin),
            "gross_quoted_credit_coin_per_assumed_unit": str(gross),
            "modeled_terminal_coin_delta_per_assumed_unit": net,
            "historical_fill": False, "account_pnl": None,
        })
    if len(out) != 46 or len({key(r) for r in out}) != 46:
        raise ValueError("INCOMPLETE_FIXED_ORIGINAL_SAMPLE")
    summary = {}
    for scenario in FRICTION:
        vals = [dec(r["modeled_terminal_coin_delta_per_assumed_unit"][scenario]) for r in out]
        summary[scenario] = {
            "positive_conditional_deltas": sum(v > 0 for v in vals),
            "nonpositive_conditional_deltas": sum(v <= 0 for v in vals),
            "worst_coin_delta_per_assumed_unit": str(min(vals)),
            "sum_coin_deltas_across_untradeable_source_units": str(sum(vals)),
        }
    result = {
        "schema": SCHEMA, "original_credit_sha256": credit_sha,
        "original_index_binding_sha256": index_sha,
        "original_native_handoff_sha256": hand_sha,
        "original_delivery_sha256": delivery_sha,
        "source_pairs": 46, "sampled_asset_weeks": 4,
        "required_asset_weeks": 182, "native_executable_pairs": 0,
        "certified_full_lifecycles": 0, "rows": out, "summary": summary,
        "status": "ORIGINAL_SOURCE_TERMINAL_DIAGNOSTIC_ONLY_HOLD",
        "historical_fee_margin_or_size_certified": False,
        "economic_train_run": False, "validation_opened": False,
        "holdout_opened": False, "orders_enabled": False,
        "promotion_authorized": False, "roi_calculated": False,
    }
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "pairs": len(out),
                      "summary": summary, "roi": False, "promotion": False},
                     sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_terminal_coin_diagnostic CREDIT INDEX HANDOFF DELIVERY OUT")
    run(*sys.argv[1:])
