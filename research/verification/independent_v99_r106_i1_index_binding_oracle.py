"""Independent raw-gzip reexecution of original same-update index binding.

Never imports the primary binding code. Source-only, no native fills or ROI.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.verification.independent_v99_r106_i1_sunday_ticker_oracle import verify as raw_oracle
from research.verification.independent_v99_r106_i1_entry_credit_oracle import audit as credit_oracle


def audit(ticker_root, native_root, credit_path, result_path):
    ticker_root, native_root, credit_path, result_path = map(
        Path, (ticker_root, native_root, credit_path, result_path))
    assert raw_oracle(ticker_root) == 4, "ORIGINAL_TICKER_GZIP_INVALID"
    credit_oracle(ticker_root, native_root, credit_path)
    original_bytes = (ticker_root / "report.json").read_bytes()
    original = json.loads(original_bytes)
    credit_bytes = credit_path.read_bytes()
    credit = json.loads(credit_bytes)
    result = json.loads(result_path.read_text())
    assert result["schema"] == "V99_I1_ORIGINAL_SAME_UPDATE_UNDERLYING_BINDING_V1"
    assert result["original_ticker_report_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert result["original_credit_report_sha256"] == hashlib.sha256(credit_bytes).hexdigest()
    assert result["status"] == "SOURCE_ONLY_ORIGINAL_INDEX_BINDING_NO_EXECUTION"
    assert result["source_only"] is True
    for field in ("historical_lot_units_certified", "historical_fee_margin_certified",
                  "complete_lifecycle_certified", "economic_train_run",
                  "validation_opened", "holdout_opened", "orders_enabled",
                  "promotion_authorized"):
        assert result[field] is False, "FALSE_ECONOMIC_CERTIFICATION"

    found = {}
    for day in original["days"]:
        decision = datetime.fromisoformat(day["decision_utc"]).astimezone(timezone.utc)
        assert decision < datetime(2023, 10, 1, tzinfo=timezone.utc)
        wanted = {(b["symbol"], int(b["arrival_us"]), int(b["exchange_us"])): b
                  for b in day["last_eligible_books"]}
        assert len(wanted) == len(day["last_eligible_books"])
        matches = {}
        for receipt in day["original_receipts"]:
            path = ticker_root / receipt["file"]
            assert path.parent.resolve() == ticker_root.resolve()
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
            for line in gzip.decompress(raw).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                stamp, delim, payload = line.partition(" ")
                assert delim
                envelope = json.loads(payload)
                params = envelope.get("params")
                if not isinstance(params, dict) or not str(params.get("channel", "")).startswith("ticker."):
                    continue
                ticker = params.get("data")
                if not isinstance(ticker, dict) or not isinstance(ticker.get("instrument_name"), str):
                    continue
                arrival = int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() * 1_000_000)
                try:
                    exchange = int(Decimal(str(ticker["timestamp"])) * 1000)
                except (KeyError, ValueError, TypeError):
                    continue
                key = (ticker["instrument_name"], arrival, exchange)
                if key not in wanted:
                    continue
                book = wanted[key]
                assert exchange <= arrival < int(decision.timestamp() * 1_000_000)
                for original_field, book_field in (
                    ("best_bid_price", "bid_coin"), ("best_ask_price", "ask_coin"),
                    ("best_bid_amount", "bid_size_source_units"),
                    ("best_ask_amount", "ask_size_source_units")
                ):
                    assert Decimal(str(ticker[original_field])) == Decimal(str(book[book_field]))
                assert key not in matches, "DUPLICATE_CAPTURE"
                values = {}
                for field in ("index_price", "underlying_price"):
                    v = ticker.get(field)
                    if v is None:
                        values[field] = None
                    else:
                        d = Decimal(str(v))
                        assert d.is_finite() and d > 0
                        values[field] = str(d)
                matches[key] = {
                    "decision_utc": day["decision_utc"], "asset": book["asset"],
                    "symbol": key[0], "arrival_us": arrival, "exchange_us": exchange,
                    "original_receipt_sha256": receipt["sha256"],
                    "index_price_usd": values["index_price"],
                    "underlying_price_usd": values["underlying_price"],
                    "underlying_index": ticker.get("underlying_index"),
                }
        assert set(matches) == set(wanted), "EXACT_ORIGINAL_UPDATE_NOT_FOUND"
        for key, book in matches.items():
            bound = (day["decision_utc"],) + key
            assert bound not in found
            found[bound] = book
    expected_books = sorted(found.values(), key=lambda b: (
        b["decision_utc"], b["symbol"], b["arrival_us"], b["exchange_us"]))
    assert sorted(result["books"], key=lambda b: (
        b["decision_utc"], b["symbol"], b["arrival_us"], b["exchange_us"])) == expected_books, "INDEX_BOOK_FORGERY"
    expected_pairs = []
    for row in credit["rows"]:
        key_s = (row["decision_utc"], row["short_symbol"],
                 int(row["short_arrival_us"]), int(row["short_exchange_us"]))
        key_l = (row["decision_utc"], row["long_symbol"],
                 int(row["long_arrival_us"]), int(row["long_exchange_us"]))
        s, l = found[key_s], found[key_l]
        assert s["asset"] == l["asset"] == row["asset"]
        a, b = s["index_price_usd"], l["index_price_usd"]
        expected_pairs.append({
            "decision_utc": row["decision_utc"], "asset": row["asset"],
            "short_symbol": row["short_symbol"], "long_symbol": row["long_symbol"],
            "short_arrival_us": s["arrival_us"], "long_arrival_us": l["arrival_us"],
            "short_index_price_usd": a, "long_index_price_usd": b,
            "same_exact_index_price": bool(a is not None and b is not None
                                            and Decimal(a) == Decimal(b)),
            "short_underlying_price_usd": s["underlying_price_usd"],
            "long_underlying_price_usd": l["underlying_price_usd"],
        })
    assert result["pairs"] == expected_pairs, "INDEX_PAIR_FORGERY"
    assert result["books_with_index_price"] == sum(
        b["index_price_usd"] is not None for b in expected_books)
    assert result["pairs_with_both_index_prices"] == sum(
        p["short_index_price_usd"] is not None and p["long_index_price_usd"] is not None
        for p in expected_pairs)
    assert result["pairs_with_exact_same_index_price"] == sum(
        p["same_exact_index_price"] for p in expected_pairs)
    return {"original_books_verified": len(expected_books),
            "original_pairs_verified": len(expected_pairs),
            "index_books": result["books_with_index_price"],
            "both_leg_index_pairs": result["pairs_with_both_index_prices"],
            "identical_index_pairs": result["pairs_with_exact_same_index_price"],
            "promotion": False, "economic_train": False}


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_index_binding_oracle TICKER NATIVE CREDIT OUTPUT")
    print(json.dumps(audit(*sys.argv[1:]), sort_keys=True))
