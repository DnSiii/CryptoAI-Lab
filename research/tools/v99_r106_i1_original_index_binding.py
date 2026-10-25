"""Bind original Deribit option quotes to SAME UPDATE index fields, SOURCE ONLY.

No inferred fills, quantity conversion, NAV, PnL, margin or historical fee tier.
Prereg: research/V99_R106_I1_ORIGINAL_ASOF_UNDERLYING_BINDING_PREREG_20261025.md
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.verification.independent_v99_r106_i1_sunday_ticker_oracle import verify

TRAIN_END = datetime(2023, 10, 1, tzinfo=timezone.utc)
FIELDS = ("index_price", "underlying_price", "underlying_index")
BOOK_FIELDS = (
    ("best_bid_price", "bid_coin"), ("best_ask_price", "ask_coin"),
    ("best_bid_amount", "bid_size_source_units"),
    ("best_ask_amount", "ask_size_source_units"),
)


def positive_price(raw, key):
    value = raw.get(key)
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("INVALID_ORIGINAL_INDEX_FIELD:" + key) from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("INVALID_ORIGINAL_INDEX_FIELD:" + key)
    return str(number)


def bind(root, credit_path, output):
    root, credit_path, output = map(Path, (root, credit_path, output))
    assert verify(root) == 4, "ORIGINAL_GZIP_OR_REPORT_CORRUPTED"
    report_bytes = (root / "report.json").read_bytes()
    report = json.loads(report_bytes)
    credit_bytes = credit_path.read_bytes()
    credit = json.loads(credit_bytes)
    if credit["schema"] != "V99_I1_ORIGINAL_ENTRY_UNIT_CREDIT_SCREEN_V1":
        raise ValueError("UNEXPECTED_ORIGINAL_CREDIT_SCHEMA")
    if credit["original_ticker_report_sha256"] != hashlib.sha256(report_bytes).hexdigest():
        raise ValueError("CREDIT_NOT_BOUND_TO_ORIGINAL_SOURCE")
    if len(credit["rows"]) != credit["adjacent_quote_pairs"]:
        raise ValueError("INCONSISTENT_ORIGINAL_CREDIT_ROWS")
    books = []
    for day in report["days"]:
        decision = datetime.fromisoformat(day["decision_utc"]).astimezone(timezone.utc)
        if decision >= TRAIN_END:
            raise ValueError("SEALED_PARTITION")
        targets = {(b["symbol"], int(b["arrival_us"]), int(b["exchange_us"])): b
                   for b in day["last_eligible_books"]}
        if len(targets) != len(day["last_eligible_books"]):
            raise ValueError("DUPLICATED_TARGET_CAPTURE")
        matches = {}
        for receipt in day["original_receipts"]:
            path = root / receipt["file"]
            if path.parent.resolve() != root.resolve():
                raise ValueError("UNSAFE_RECEIPT_PATH")
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != receipt["sha256"]:
                raise ValueError("ORIGINAL_RECEIPT_SHA_CHANGED")
            for line in gzip.decompress(raw).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                stamp, sep, payload = line.partition(" ")
                if not sep:
                    raise ValueError("MALFORMED_ORIGINAL_CAPTURE")
                data = json.loads(payload).get("params", {})
                if not isinstance(data, dict) or not str(data.get("channel", "")).startswith("ticker."):
                    continue
                data = data.get("data")
                if not isinstance(data, dict):
                    continue
                symbol = data.get("instrument_name")
                if not isinstance(symbol, str):
                    continue
                arrival = int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() * 1_000_000)
                try:
                    exchange = int(Decimal(str(data["timestamp"])) * 1000)
                except (KeyError, TypeError, ValueError, InvalidOperation):
                    continue
                key = (symbol, arrival, exchange)
                if key not in targets:
                    continue
                b = targets[key]
                if not exchange <= arrival < int(decision.timestamp() * 1_000_000):
                    raise ValueError("NONCAUSAL_ORIGINAL_CAPTURE")
                for raw_key, book_key in BOOK_FIELDS:
                    if Decimal(str(data[raw_key])) != Decimal(str(b[book_key])):
                        raise ValueError("BOOK_NOT_SAME_ORIGINAL_TICKER_UPDATE")
                if key in matches:
                    raise ValueError("DUPLICATE_EXACT_ORIGINAL_UPDATE")
                matches[key] = {
                    "decision_utc": day["decision_utc"], "asset": b["asset"],
                    "symbol": symbol, "arrival_us": arrival, "exchange_us": exchange,
                    "original_receipt_sha256": digest,
                    "index_price_usd": positive_price(data, "index_price"),
                    "underlying_price_usd": positive_price(data, "underlying_price"),
                    "underlying_index": data.get("underlying_index"),
                }
        if set(matches) != set(targets):
            raise ValueError("MISSING_EXACT_ORIGINAL_INDEX_BINDING")
        books.extend(matches[k] for k in sorted(matches))
    lookup = {(b["decision_utc"], b["symbol"], b["arrival_us"], b["exchange_us"]): b
              for b in books}
    pairs = []
    for row in credit["rows"]:
        short = lookup[(row["decision_utc"], row["short_symbol"],
                        int(row["short_arrival_us"]), int(row["short_exchange_us"]))]
        long = lookup[(row["decision_utc"], row["long_symbol"],
                       int(row["long_arrival_us"]), int(row["long_exchange_us"]))]
        if short["asset"] != long["asset"] or short["asset"] != row["asset"]:
            raise ValueError("CROSS_ASSET_PAIR")
        a, b = short["index_price_usd"], long["index_price_usd"]
        pairs.append({
            "decision_utc": row["decision_utc"], "asset": row["asset"],
            "short_symbol": row["short_symbol"], "long_symbol": row["long_symbol"],
            "short_arrival_us": short["arrival_us"], "long_arrival_us": long["arrival_us"],
            "short_index_price_usd": a, "long_index_price_usd": b,
            "same_exact_index_price": a is not None and b is not None
                and Decimal(a) == Decimal(b),
            "short_underlying_price_usd": short["underlying_price_usd"],
            "long_underlying_price_usd": long["underlying_price_usd"],
        })
    result = {
        "schema": "V99_I1_ORIGINAL_SAME_UPDATE_UNDERLYING_BINDING_V1",
        "original_ticker_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "original_credit_report_sha256": hashlib.sha256(credit_bytes).hexdigest(),
        "books": books, "pairs": pairs,
        "books_with_index_price": sum(b["index_price_usd"] is not None for b in books),
        "pairs_with_both_index_prices": sum(p["short_index_price_usd"] is not None
                                           and p["long_index_price_usd"] is not None for p in pairs),
        "pairs_with_exact_same_index_price": sum(p["same_exact_index_price"] for p in pairs),
        "source_only": True, "historical_lot_units_certified": False,
        "historical_fee_margin_certified": False, "complete_lifecycle_certified": False,
        "economic_train_run": False, "validation_opened": False,
        "holdout_opened": False, "orders_enabled": False, "promotion_authorized": False,
        "status": "SOURCE_ONLY_ORIGINAL_INDEX_BINDING_NO_EXECUTION",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "original_books": len(books),
                      "original_pairs": len(pairs),
                      "books_with_index_price": result["books_with_index_price"],
                      "pairs_with_both_index_prices": result["pairs_with_both_index_prices"],
                      "pairs_with_exact_same_index_price": result["pairs_with_exact_same_index_price"],
                      "promotion": False}))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_index_binding TICKER_ROOT CREDIT_JSON OUT")
    bind(*sys.argv[1:])
