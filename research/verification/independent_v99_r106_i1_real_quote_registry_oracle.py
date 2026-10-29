"""Independent source-byte oracle for original 2022-05-01 quoted symbols.

Does not import production parser, contract selector or registry builder.
No economic validation or trading.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ORIGINAL_SHA = "e22d150bbe4e2cbe7c2230905f939b32e1bbbc73d94279258f699cd9e5948b0d"
MONDAY_MS = 1651449600000
LOW, HIGH = 28 * 86400000, 35 * 86400000
METRICS = (
    "unique_quoted_put_symbols", "valid_bbo_quoted_put_symbols",
    "fixed_28_35d_quote_symbols", "fixed_28_35d_valid_bbo_symbols",
    "quoted_symbols_missing_from_firstparty_registry",
    "fixed_28_35d_symbols_missing_from_registry",
    "quoted_symbols_present_in_firstparty_registry",
    "firstparty_created_after_original_quote_arrival",
    "fixed_created_after_quote_arrival",
)


def original_records(root):
    manifest = json.loads((root / "native_instrument_registry.json").read_text())
    out = {}
    for coin in ("BTC", "ETH"):
        entry = manifest["sources"][coin]
        original = gzip.decompress((root / entry["original_gzip"]).read_bytes())
        if hashlib.sha256(original).hexdigest() != entry["original_raw_sha256"]:
            raise ValueError("ORACLE_REGISTRY_RAW_SHA_INVALID")
        parsed = json.loads(original)["result"]
        if len(parsed) != entry["original_instruments"]:
            raise ValueError("ORACLE_REGISTRY_ORIGINAL_COUNT_INVALID")
        out[coin] = {item["instrument_name"]: item for item in parsed
                     if item.get("kind") == "option" and item.get("option_type") == "put"}
    return out


def replay(sample, root):
    if hashlib.sha256(sample.read_bytes()).hexdigest() != ORIGINAL_SHA:
        raise ValueError("ORACLE_ORIGINAL_SAMPLE_SHA_INVALID")
    registry = original_records(root)
    quotes = {}
    count = 0
    with gzip.open(sample, "rt", newline="") as f:
        data = csv.reader(f)
        names = next(data)
        columns = {name: i for i, name in enumerate(names)}
        required = ("exchange", "symbol", "timestamp", "local_timestamp",
                    "bid_price", "ask_price", "bid_amount", "ask_amount")
        if not set(required).issubset(columns):
            raise ValueError("ORACLE_ORIGINAL_COLUMNS_MISSING")
        for cells in data:
            count += 1
            if cells[columns["exchange"]] != "deribit":
                raise ValueError("ORACLE_WRONG_VENUE")
            name = cells[columns["symbol"]]
            bits = name.split("-")
            if len(bits) != 4 or bits[0] not in ("BTC", "ETH") or bits[3] != "P":
                continue
            try:
                expiry = datetime.strptime(bits[1].upper(), "%d%b%y").replace(
                    hour=8, tzinfo=timezone.utc)
                strike = float(bits[2])
            except (ValueError, OverflowError):
                continue
            if not math.isfinite(strike) or strike <= 0:
                continue
            venue = int(cells[columns["timestamp"]])
            arrival = int(cells[columns["local_timestamp"]])
            if not 0 <= venue <= arrival < MONDAY_MS * 1000:
                raise ValueError("ORACLE_BAD_ORIGINAL_CLOCK")
            try:
                nums = [float(cells[columns[key]]) for key in
                        ("bid_price", "ask_price", "bid_amount", "ask_amount")]
                valid = all(math.isfinite(n) and n > 0 for n in nums) and nums[0] < nums[1]
            except (ValueError, TypeError):
                valid = False
            old = quotes.get(name)
            if old is None:
                quotes[name] = [arrival, valid]
            else:
                if arrival < old[0]:
                    old[0] = arrival
                old[1] = old[1] or valid
    if count != 4_253_565:
        raise ValueError("ORACLE_ORIGINAL_QUOTE_COUNT_INVALID")
    result = {coin: {key: 0 for key in METRICS} for coin in ("BTC", "ETH")}
    for name, (first_arrival, has_valid) in quotes.items():
        bits = name.split("-")
        coin = bits[0]
        exp_ms = int(datetime.strptime(bits[1].upper(), "%d%b%y").replace(
            hour=8, tzinfo=timezone.utc).timestamp() * 1000)
        fixed = LOW <= exp_ms - MONDAY_MS <= HIGH
        r = result[coin]
        r["unique_quoted_put_symbols"] += 1
        r["valid_bbo_quoted_put_symbols"] += int(has_valid)
        r["fixed_28_35d_quote_symbols"] += int(fixed)
        r["fixed_28_35d_valid_bbo_symbols"] += int(fixed and has_valid)
        native = registry[coin].get(name)
        if native is None:
            r["quoted_symbols_missing_from_firstparty_registry"] += 1
            r["fixed_28_35d_symbols_missing_from_registry"] += int(fixed)
        else:
            r["quoted_symbols_present_in_firstparty_registry"] += 1
            if (int(native["expiration_timestamp"]) != exp_ms
                    or float(native["strike"]) != float(bits[2])):
                raise ValueError("ORACLE_NATIVE_CONTRACT_ID_MISMATCH")
            if int(native["creation_timestamp"]) > first_arrival // 1000:
                r["firstparty_created_after_original_quote_arrival"] += 1
                r["fixed_created_after_quote_arrival"] += int(fixed)
    contradicted = any(result[coin][key] for coin in ("BTC", "ETH") for key in
                     ("quoted_symbols_missing_from_firstparty_registry",
                      "firstparty_created_after_original_quote_arrival"))
    return {"schema": "V99_I1_ORIGINAL_QUOTE_REGISTRY_RECONCILIATION_V1",
            "status": ("REGISTRY_COMPLETENESS_OR_CHRONOLOGY_FALSIFIED" if contradicted
                       else "SAMPLED_DAY_NO_REGISTRY_CONTRADICTION"),
            "source_day": "2022-05-01", "decision_day": "2022-05-02",
            "original_sample_sha256": ORIGINAL_SHA, "original_quote_rows": count,
            "assets": result, "source_only": True,
            "economic_train_executed": False, "roi_calculated": False,
            "validation_opened": False, "holdout_opened": False,
            "promotion_authorized": False, "orders_enabled": False,
            "historical_option_lifecycles_certified": 0}


def verify_expected(actual, expected):
    if actual != expected:
        raise ValueError("INDEPENDENT_ORIGINAL_QUOTE_REGISTRY_DISAGREEMENT")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_real_quote_registry_oracle SAMPLE REGISTRY_DIR REPORT")
    sample, registry, report = map(Path, sys.argv[1:])
    expected = replay(sample, registry)
    actual = json.loads(report.read_text())
    verify_expected(actual, expected)
    # Deterministic adversarial output mutation, with no third raw-file scan.
    forged = json.loads(json.dumps(actual))
    forged["assets"]["BTC"]["unique_quoted_put_symbols"] += 1
    try:
        verify_expected(forged, expected)
    except ValueError as exc:
        if str(exc) != "INDEPENDENT_ORIGINAL_QUOTE_REGISTRY_DISAGREEMENT":
            raise
    else:
        raise AssertionError("FORGED_SOURCE_RECONCILIATION_ACCEPTED")
    print(json.dumps({"status": expected["status"], "independent_raw_bytes_verified": True,
                      "source_rows": expected["original_quote_rows"],
                      "assets": expected["assets"], "mutation_rejected": True,
                      "economic_train_executed": False, "promotion_authorized": False},
                     sort_keys=True))
