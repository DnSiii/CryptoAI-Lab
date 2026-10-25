"""Original I1 minimum native displayed depth on 46 real quote pairs.

Necessary source-unit check ONLY; no trades, portfolio, fee certification or ROI.
Prereg: research/V99_R106_I1_NATIVE_MINIMUM_DEPTH_PREREG_20261025.md
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import native_contracts

TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)
SCHEMA = "V99_I1_ORIGINAL_NATIVE_MINIMUM_DEPTH_SOURCE_ONLY_V1"


def positive(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("INVALID_NATIVE_SIZE") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("INVALID_NATIVE_SIZE")
    return number


def key(row):
    return (row["decision_utc"], row["short_symbol"], row["long_symbol"])


def run(credit_path, native_root, index_path, fee_path, output_path):
    credit_path, native_root, index_path, fee_path = (
        Path(credit_path), Path(native_root), Path(index_path), Path(fee_path))
    credit_bytes = credit_path.read_bytes()
    native_bytes = (native_root / "native_instrument_registry.json").read_bytes()
    index_bytes = index_path.read_bytes()
    fee_bytes = fee_path.read_bytes()
    credit = json.loads(credit_bytes)
    index = json.loads(index_bytes)
    fee = json.loads(fee_bytes)
    if (credit.get("schema") != "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1"
            or index.get("schema") != "V99_I1_ORIGINAL_SAME_UPDATE_UNDERLYING_BINDING_V1"
            or fee.get("schema") != "V99_I1_ORIGINAL_NATIVE_FEE_CAP_ENVELOPE_V2"):
        raise ValueError("WRONG_ORIGINAL_INPUT_SCHEMA")
    if (credit.get("original_native_registry_report_sha256") != hashlib.sha256(native_bytes).hexdigest()
            or index.get("original_credit_report_sha256") != hashlib.sha256(credit_bytes).hexdigest()
            or fee.get("source_credit_sha256") != hashlib.sha256(credit_bytes).hexdigest()):
        raise ValueError("ORIGINAL_SOURCE_IDENTITY_MISMATCH")
    if (credit.get("required_train_asset_weeks") != 182
            or credit.get("sample_asset_weeks_with_original_two_strike_books") != 4
            or fee.get("certified_full_lifecycles") != 0
            or len(credit.get("rows", [])) != 46
            or len(index.get("pairs", [])) != 46
            or len(fee.get("rows", [])) != 46):
        raise ValueError("NOT_FIXED_ORIGINAL_SAMPLE")
    for obj in (credit, index, fee):
        if any(obj.get(flag) for flag in ("economic_train_run", "economic_train_executed",
                                          "validation_opened", "holdout_opened",
                                          "orders_enabled", "promotion_authorized")):
            raise ValueError("UNAUTHORIZED_ECONOMIC_CLAIM")
    # The native original gzip and its exact registry are independently rechecked here.
    registry = native_contracts(native_root)
    indexes = {key(row): row for row in index["pairs"]}
    fees = {key(row): row for row in fee["rows"]}
    if len(indexes) != 46 or len(fees) != 46:
        raise ValueError("DUPLICATE_ORIGINAL_PAIR")
    rows = []
    counts = {asset: Counter() for asset in ("BTC", "ETH")}
    seen = set()
    for row in credit["rows"]:
        identity = key(row)
        if identity in seen or identity not in indexes or identity not in fees:
            raise ValueError("MISSING_OR_DUPLICATE_ORIGINAL_PAIR")
        seen.add(identity)
        asset = row["asset"]
        if asset not in counts or indexes[identity]["asset"] != asset or fees[identity]["asset"] != asset:
            raise ValueError("CROSS_ASSET_ORIGINAL_PAIR")
        decision = datetime.fromisoformat(row["decision_utc"]).astimezone(timezone.utc)
        if not decision < TRAIN_END:
            raise ValueError("SEALED_PARTITION")
        short = registry[asset].get(row["short_symbol"])
        long = registry[asset].get(row["long_symbol"])
        if short is None or long is None:
            raise ValueError("UNLISTED_NATIVE_INSTRUMENT")
        for instrument in (short, long):
            if (instrument["settlement_currency"] != asset
                    or instrument["creation_timestamp"] > int(decision.timestamp() * 1000)
                    or instrument["option_type"] != "put"
                    or positive(instrument["contract_size"]) != Decimal(1)
                    or instrument["expiration_timestamp"] != int(
                        datetime.fromisoformat(row["expiry_utc"]).timestamp() * 1000)):
                raise ValueError("NATIVE_CONTRACT_NOT_ORIGINAL_ASOF")
        minimum = max(positive(short["min_trade_amount"]),
                      positive(long["min_trade_amount"]))
        displayed = min(positive(row["short_bid_size_source_units"]),
                        positive(row["long_ask_size_source_units"]))
        eligible = displayed >= minimum
        counts[asset]["pairs"] += 1
        counts[asset]["provisional_minimum_depth_sufficient"] += int(eligible)
        rows.append({
            "decision_utc": row["decision_utc"], "asset": asset,
            "short_symbol": row["short_symbol"], "long_symbol": row["long_symbol"],
            "short_arrival_us": int(row["short_arrival_us"]),
            "long_arrival_us": int(row["long_arrival_us"]),
            "short_displayed_source_units": str(positive(row["short_bid_size_source_units"])),
            "long_displayed_source_units": str(positive(row["long_ask_size_source_units"])),
            "minimum_displayed_source_units": str(displayed),
            "minimum_native_order_units": str(minimum),
            "short_native_contract_size_coin": str(positive(short["contract_size"])),
            "long_native_contract_size_coin": str(positive(long["contract_size"])),
            "provisional_minimum_depth_sufficient": eligible,
            "quote_source_units_historically_certified": False,
            "historical_native_minimum_asof_certified": False,
        })
    result = {
        "schema": SCHEMA, "source_credit_sha256": hashlib.sha256(credit_bytes).hexdigest(),
        "source_native_registry_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "source_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "source_fee_sha256": hashlib.sha256(fee_bytes).hexdigest(),
        "original_pairs": 46, "sampled_asset_weeks": 4, "required_asset_weeks": 182,
        "certified_full_lifecycles": 0,
        "counts_by_asset": {asset: dict(counts[asset]) for asset in ("BTC", "ETH")},
        "rows": rows,
        "status": "SOURCE_ONLY_PROVISIONAL_NATIVE_MINIMUM_DEPTH_NO_EXECUTION",
        "historical_quote_size_units_certified": False,
        "historical_native_minimum_asof_certified": False,
        "historical_fee_margin_certified": False,
        "economic_train_run": False, "roi_calculated": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts_by_asset": result["counts_by_asset"],
                      "complete_lifecycles": 0, "promotion": False}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_native_minimum_depth CREDIT NATIVE_ROOT INDEX FEE OUT")
    run(*sys.argv[1:])
