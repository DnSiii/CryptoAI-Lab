"""Original I1 quote-size/temporal execution handoff: diagnostics, never fills.

All original 46 quoted pairs retained; no strategy, unit conversion, PnL,
orders, or promotion. Historical native size units, account fees and full
entry-through-expiry receipts are required before any executable quantity.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)
SCHEMA = "V99_I1_ORIGINAL_NATIVE_SIZE_EXECUTION_HANDOFF_V1"
BLOCKERS = (
    "historical_quote_size_unit_conversion_unverified",
    "historical_account_fee_tier_and_delivery_fee_unverified",
    "historical_coin_margin_and_liquidation_rules_unverified",
    "complete_entry_exit_or_settlement_depth_unavailable",
    "atomic_two_leg_fill_not_proven",
    "independent_self_financing_five_fold_economics_not_run",
)

def D(value):
    x = Decimal(str(value))
    if not x.is_finite() or x <= 0:
        raise ValueError("INVALID_ORIGINAL_NATIVE_QUANTITY")
    return x

def make(credit_path, index_path, native_path, output):
    credit_path, index_path, native_path, output = map(
        Path, (credit_path, index_path, native_path, output))
    cb, ib, nb = (p.read_bytes() for p in (credit_path, index_path, native_path))
    credit, index, native = (json.loads(x) for x in (cb, ib, nb))
    if (credit.get("schema") != "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
        or index.get("schema") != "V99_I1_ORIGINAL_SAME_UPDATE_UNDERLYING_BINDING_V1"
        or native.get("schema") != "V99_I1_DERIBIT_HISTORICAL_INSTRUMENT_REGISTRY_V1"
        or index["original_credit_report_sha256"] != hashlib.sha256(cb).hexdigest()
        or index["original_ticker_report_sha256"] != credit["original_ticker_report_sha256"]):
        raise ValueError("UNBOUND_ORIGINAL_SOURCE")
    if (credit["required_train_asset_weeks"] != 182
        or credit["sample_asset_weeks_with_original_two_strike_books"] != 4
        or len(credit["rows"]) != 46 or len(index["pairs"]) != 46):
        raise ValueError("NOT_THE_FIXED_ORIGINAL_TRAIN_SAMPLE")
    if any(index[k] for k in ("historical_lot_units_certified",
                              "historical_fee_margin_certified",
                              "complete_lifecycle_certified",
                              "economic_train_run", "validation_opened",
                              "holdout_opened", "orders_enabled", "promotion_authorized")):
        raise ValueError("FALSE_SOURCE_CERTIFICATION")
    original_index = {(p["decision_utc"], p["short_symbol"], p["long_symbol"]): p
                      for p in index["pairs"]}
    if len(original_index) != len(index["pairs"]):
        raise ValueError("DUPLICATE_ORIGINAL_PAIR")
    original_registry = {
        asset: {r["instrument_name"]: r for r in native["registry"][asset]}
        for asset in ("BTC", "ETH")
    }
    rows = []
    for c in credit["rows"]:
        t = datetime.fromisoformat(c["decision_utc"]).astimezone(timezone.utc)
        if not t < TRAIN_END or t.weekday() != 0:
            raise ValueError("SEALED_OR_NONDECISION_TIMESTAMP")
        k = (c["decision_utc"], c["short_symbol"], c["long_symbol"])
        p = original_index[k]
        if (p["asset"] != c["asset"] or
            p["short_arrival_us"] != c["short_arrival_us"] or
            p["long_arrival_us"] != c["long_arrival_us"]):
            raise ValueError("INDEX_NOT_SAME_CAPTURE")
        asset = c["asset"]
        if asset not in original_registry:
            raise ValueError("WRONG_ASSET")
        short = original_registry[asset][c["short_symbol"]]
        long = original_registry[asset][c["long_symbol"]]
        if (D(short["contract_size"]) != D(c["short_native_contract_size"])
            or D(long["contract_size"]) != D(c["long_native_contract_size"])
            or D(short["min_trade_amount"]) != D(c["short_native_min_trade_amount"])
            or D(long["min_trade_amount"]) != D(c["long_native_min_trade_amount"])):
            raise ValueError("NATIVE_TERMS_CHANGED")
        s, l = D(c["short_bid_size_source_units"]), D(c["long_ask_size_source_units"])
        ds = int(t.timestamp() * 1_000_000)
        sa, la = int(c["short_arrival_us"]), int(c["long_arrival_us"])
        se, le = int(c["short_exchange_us"]), int(c["long_exchange_us"])
        if not (0 <= ds-sa <= 300_000_000 and 0 <= ds-la <= 300_000_000
                and se <= sa and le <= la and ds-se <= 300_000_000
                and ds-le <= 300_000_000):
            raise ValueError("STALE_OR_NONCAUSAL_SOURCE")
        rows.append({
            "decision_utc": c["decision_utc"], "asset": asset,
            "short_symbol": c["short_symbol"], "long_symbol": c["long_symbol"],
            "short_bid_size_source_units": str(s),
            "long_ask_size_source_units": str(l),
            "minimum_displayed_source_units": str(min(s, l)),
            "short_native_contract_size": str(D(short["contract_size"])),
            "long_native_contract_size": str(D(long["contract_size"])),
            "short_native_min_trade_amount": str(D(short["min_trade_amount"])),
            "long_native_min_trade_amount": str(D(long["min_trade_amount"])),
            "short_quote_age_ms": str(Decimal(ds-sa)/1000),
            "long_quote_age_ms": str(Decimal(ds-la)/1000),
            "arrival_skew_ms": str(Decimal(abs(sa-la))/1000),
            "exchange_skew_ms": str(Decimal(abs(se-le))/1000),
            "same_exact_index_price": p["same_exact_index_price"],
            "historical_native_contract_qty": None,
            "two_leg_executable_fill": False,
            "reason": "SOURCE_SIZE_NOT_CERTIFIED_AS_NATIVE_LOTS_AND_NO_ATOMIC_FILL",
        })
    result = {
        "schema": SCHEMA,
        "source_credit_sha256": hashlib.sha256(cb).hexdigest(),
        "source_index_sha256": hashlib.sha256(ib).hexdigest(),
        "source_native_registry_sha256": hashlib.sha256(nb).hexdigest(),
        "required_asset_weeks": 182,
        "sampled_asset_weeks": 4,
        "source_pairs": len(rows),
        "native_executable_pairs": 0,
        "rows": rows,
        "blockers": list(BLOCKERS),
        "source_only": True, "economic_train_run": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
        "status": "SOURCE_ONLY_NATIVE_QUANTITY_AND_ATOMIC_EXECUTION_UNCERTIFIED",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"], "source_pairs": len(rows),
        "native_executable_pairs": 0,
        "max_arrival_skew_ms": str(max(Decimal(r["arrival_skew_ms"]) for r in rows)),
        "max_quote_age_ms": str(max(max(Decimal(r["short_quote_age_ms"]),
                                       Decimal(r["long_quote_age_ms"])) for r in rows)),
        "economic_train_run": False, "promotion": False,
    }, sort_keys=True))
    return result

if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_native_quote_size_handoff CREDIT INDEX NATIVE OUT")
    make(*sys.argv[1:])
