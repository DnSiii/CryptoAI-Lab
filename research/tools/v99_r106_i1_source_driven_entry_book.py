"""Derive all 90x2 fixed I1 Monday predecision option books from ORIGINAL gzip bytes.

SOURCE ONLY: Tardis quotes have NO authenticated underlying index or native-lot
unit; this output cannot be fed to an economic replay as a certified trade.
Preregistered: V99_R106_I1_SOURCE_DRIVEN_ENTRY_BOOK_PREREG_20261028.md
"""
from __future__ import annotations

import csv
import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_original_event_quote_identity import (
    _original_manifest, COLUMNS,
)
from research.tools.v99_r106_i1_original_intent_binding import bind
from research.tools.v99_r106_i1_native_coin_account_replay import D, END
from research.tools.v99_r106_i1_train_numeric_gate import _fold

SCHEMA = "V99_I1_SOURCE_DRIVEN_90W_ORIGINAL_ENTRY_BOOK_V1"
AGE_US = 300_000_000
MIN_TENOR_MS = 28 * 86_400_000
MAX_TENOR_MS = 35 * 86_400_000


def _contract(symbol):
    """Return literal native contract identity; never invent an index."""
    if not isinstance(symbol, str):
        return None
    parts = symbol.split("-")
    if len(parts) != 4 or parts[0] not in ("BTC", "ETH") or parts[3] != "P":
        return None
    try:
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(
            hour=8, tzinfo=timezone.utc)
        strike = D(parts[2])
    except (ValueError, OverflowError, InvalidOperation):
        return None
    if strike <= 0:
        return None
    return parts[0], int(expiry.timestamp() * 1000), str(strike)


def _one_sunday(source, expected_rows, day, decision_ms):
    """Latest physically arrived row wins, including invalid last books."""
    cutoff = decision_ms * 1000
    start = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp() * 1_000_000)
    latest = {}
    count = 0
    last_arrival = -1
    with gzip.open(source, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError("ORIGINAL_BOOK_COLUMNS_MISSING")
        for row in reader:
            count += 1
            if row["exchange"] != "deribit":
                raise ValueError("WRONG_ORIGINAL_VENUE")
            try:
                venue, arrival = int(row["timestamp"]), int(row["local_timestamp"])
            except (ValueError, TypeError) as exc:
                raise ValueError("INVALID_ORIGINAL_CLOCK") from exc
            if not (0 <= venue <= arrival and start <= arrival < start + 86_400_000_000
                    and arrival >= last_arrival):
                raise ValueError("ORIGINAL_CAPTURE_ORDER_OR_CLOCK_INVALID")
            last_arrival = arrival
            # Sunday arrival is strictly earlier than Monday 00:00. No Monday
            # postdecision quote may be used as a replacement.
            if arrival >= cutoff:
                raise ValueError("FUTURE_OR_SEALED_ENTRY_CAPTURE")
            parsed = _contract(row["symbol"])
            if parsed is None:
                continue
            asset, expiry_ms, strike = parsed
            if not (MIN_TENOR_MS <= expiry_ms-decision_ms <= MAX_TENOR_MS
                    and expiry_ms < END):
                continue
            latest[row["symbol"]] = (venue, arrival, count, row, asset, expiry_ms, strike)
    if count != expected_rows:
        raise ValueError("ORIGINAL_ENTRY_DAY_ROW_COUNT_MISMATCH")
    books = {"BTC": [], "ETH": []}
    invalid = {"BTC": 0, "ETH": 0}
    stale = {"BTC": 0, "ETH": 0}
    for symbol, (venue, arrival, ordinal, row, asset, expiry, strike) in sorted(latest.items()):
        if not (0 <= cutoff-arrival <= AGE_US and 0 <= cutoff-venue <= AGE_US):
            stale[asset] += 1
            continue
        try:
            bid, ask, bid_size, ask_size = (D(row[k]) for k in (
                "bid_price", "ask_price", "bid_amount", "ask_amount"))
        except (ValueError, TypeError, KeyError, InvalidOperation):
            invalid[asset] += 1
            continue
        if not (0 < bid < ask and bid_size > 0 and ask_size > 0):
            invalid[asset] += 1
            continue
        books[asset].append({
            "symbol": symbol, "expiry_ms": expiry, "strike_usd": strike,
            "bid_coin": str(bid), "ask_coin": str(ask),
            "bid_size_source_units": str(bid_size),
            "ask_size_source_units": str(ask_size),
            "venue_us": venue, "arrival_us": arrival,
            "original_source_row_ordinal": ordinal,
        })
    return books, invalid, stale, count


def build(root, original_intents):
    """Build 180 fixed asset-week books. Caller must independently bind signals."""
    if (not isinstance(original_intents, list) or len(original_intents) != 180):
        raise ValueError("ORIGINAL_FIXED_180_INTENTS_REQUIRED")
    grid = [(int(d.timestamp()*1000), a) for d in eligible(True)
            for a in ("BTC", "ETH")]
    for intent, (clock, asset) in zip(original_intents, grid):
        if (not isinstance(intent, dict) or intent.get("decision_ms") != clock
                or intent.get("asset") != asset or intent.get("fold") != _fold(clock)
                or intent.get("signal") not in (
                    "POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY")):
            raise ValueError("UNBOUND_FIXED_TRAIN_INTENT_GRID")
    # Fail BEFORE producing partial output, even if only one day is missing.
    files, manifest_sha = _original_manifest(root)
    day_hashes = {item['date']: item['sha256'] for item in
                  json.loads((Path(root)/'manifest.json').read_text(encoding='utf-8'))['days']}
    rows = []
    for i in range(0, 180, 2):
        clock = grid[i][0]
        sunday = datetime.fromtimestamp(clock/1000, timezone.utc).date()-timedelta(days=1)
        if sunday not in files:
            raise ValueError("ORIGINAL_SUNDAY_SOURCE_DAY_MISSING")
        path, expected_rows = files[sunday]
        books, invalid, stale, count = _one_sunday(path, expected_rows, sunday, clock)
        for offset, asset in enumerate(("BTC", "ETH")):
            intent = original_intents[i+offset]
            rows.append({
                "decision_ms": clock, "asset": asset,
                "fold": intent["fold"], "signal": intent["signal"],
                "source_day": sunday.isoformat(),
                "source_day_sha256": day_hashes[sunday.isoformat()],
                "source_rows_scanned": count,
                "last_eligible_invalid_books": invalid[asset],
                "last_eligible_stale_books": stale[asset],
                "original_books": books[asset],
            })
    return {
        "schema": SCHEMA,
        "status": "ORIGINAL_BBO_ONLY_NO_INDEX_LOT_FEE_MARGIN_OR_FILLS",
        "source_manifest_sha256": manifest_sha,
        "asset_week_decisions": len(rows),
        "source_sundays_scanned": 90,
        "source_original_quote_rows_scanned": sum(r["source_rows_scanned"]
                                                  for r in rows[::2]),
        "rows": rows,
        "original_underlying_index_authenticated": False,
        "original_native_lot_units_authenticated": False,
        "historical_fee_margin_delivery_authenticated": False,
        "original_execution_or_fills_certified": False,
        "economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        "freeze_authorized": False, "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "paper_publication_authorized": False,
    }



def bind_full_open_inventories(source_book_report, journal):
    """An OPEN must expose the ENTIRE original eligible candidate book.

    This prevents caller-selected source subsets. Index and native lot unit
    provenance remain external and explicitly UNVERIFIED.
    """
    books = {(r["decision_ms"], r["asset"]): r["original_books"]
             for r in source_book_report["rows"]}
    opens = 0
    for scenario in ("severe", "supersevere"):
        for day in journal["scenarios"][scenario]:
            for event in day["events"]:
                if event.get("kind") != "OPEN":
                    continue
                opens += 1
                key = (event.get("at_ms"), event.get("asset"))
                expected = books.get(key)
                if expected is None or not expected:
                    raise ValueError("SOURCE_DRIVEN_OPEN_HAS_NO_ELIGIBLE_ORIGINAL_BOOK")
                received = event.get("quotes")
                if not isinstance(received, list) or len(received) != len(expected):
                    raise ValueError("SOURCE_DRIVEN_OPEN_INVENTORY_MISMATCH")
                expected_by_symbol = {q["symbol"]: q for q in expected}
                received_by_symbol = {q.get("symbol"): q for q in received
                                      if isinstance(q, dict)}
                if (len(received_by_symbol) != len(received)
                        or set(received_by_symbol) != set(expected_by_symbol)):
                    raise ValueError("SOURCE_DRIVEN_OPEN_INVENTORY_MISMATCH")
                for symbol, original in expected_by_symbol.items():
                    q = received_by_symbol[symbol]
                    if (q.get("asset") != key[1]
                            or q.get("expiry_ms") != original["expiry_ms"]
                            or D(q.get("strike_usd")) != D(original["strike_usd"])
                            or D(q.get("bid_coin")) != D(original["bid_coin"])
                            or D(q.get("ask_coin")) != D(original["ask_coin"])
                            or D(q.get("bid_native_lots")) != D(original["bid_size_source_units"])
                            or D(q.get("ask_native_lots")) != D(original["ask_size_source_units"])
                            or q.get("venue_ms") != original["venue_us"] // 1000
                            or q.get("arrival_ms") != original["arrival_us"] // 1000):
                        raise ValueError("SOURCE_DRIVEN_OPEN_ORIGINAL_BOOK_MISMATCH")
    return {"source_driven_open_inventories_checked": opens,
            "original_index_authenticated": False,
            "source_size_unit_native_lot_certified": False,
            "economic_train_certified": False, "promotion_authorized": False}

def main(root, original_signal_path, output_path):
    original = bind(Path(original_signal_path))
    report = build(root, original["intents"])
    Path(output_path).write_text(
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+"\n",
        encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "source_sundays_scanned": 90,
        "asset_week_decisions": 180, "economic_train_executed": False,
        "promotion_authorized": False,
    }, sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_source_driven_entry_book ORIGINAL_661D_ROOT ORIGINAL_SIGNAL_JSON OUT_JSON")
    main(*sys.argv[1:])
