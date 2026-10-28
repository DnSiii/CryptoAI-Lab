"""Independent original-byte re-execution of held-contract 661d event spine.

No imports from production compiler or original event identity helpers.
Verifies complete OPEN/MARK/expiry schedule and exact last as-of original
quotes; not original index, fees, margins, settlement or simulated fills.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research.verification.independent_v99_r106_i1_source_entry_book_oracle import (
    verify as verify_entry_source,
)

FIRST = date(2021, 12, 9)
DAYS = 661
START_MS = 1639094399000  # 2021-12-09 23:59:59 UTC
DAY_MS = 86_400_000
REQUIRED = {"exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount"}


def _num(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("ORACLE_INVALID_MARK_NUMBER") from exc
    if not n.is_finite():
        raise ValueError("ORACLE_NONFINITE_MARK_NUMBER")
    return n


def _last(path, day, clock, symbols, expected_rows):
    lower = int(datetime(day.year,day.month,day.day,
                         tzinfo=timezone.utc).timestamp()*1_000_000)
    latest = {}
    seen = 0
    previous = -1
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_MISSING_MARK_COLUMNS")
        for row in reader:
            seen += 1
            try:
                venue = int(row["timestamp"])
                arrival = int(row["local_timestamp"])
            except (ValueError, TypeError) as exc:
                raise ValueError("ORACLE_INVALID_MARK_CLOCK") from exc
            if (row["exchange"] != "deribit" or not 0 <= venue <= arrival
                    or not lower <= arrival < lower+86_400_000_000
                    or arrival < previous):
                raise ValueError("ORACLE_INVALID_OR_REORDERED_CAPTURE")
            previous = arrival
            if row["symbol"] in symbols and arrival < clock*1000:
                latest[row["symbol"]] = (row, venue, arrival, seen)
    if seen != expected_rows:
        raise ValueError("ORACLE_ORIGINAL_MARK_ROW_COUNT_MISMATCH")
    return latest


def verify(root, entry_report, spine):
    if (not isinstance(spine, dict)
            or spine.get("schema") != "V99_I1_SOURCE_DRIVEN_661D_MARK_EVENT_SPINE_V1"
            or spine.get("status") != "ORIGINAL_MARKET_SPINE_ONLY_NOT_ECONOMIC_JOURNAL"
            or spine.get("promotion_authorized") is not False
            or spine.get("native_economic_train_executed") is not False
            or spine.get("original_complete_option_lifecycles_certified") != 0
            or spine.get("original_underlying_index_authenticated") is not False
            or spine.get("original_native_lot_conversion_authenticated") is not False
            or spine.get("historical_native_fees_margin_liquidation_authenticated") is not False
            or spine.get("original_delivery_index_authenticated") is not False):
        raise ValueError("ORACLE_FALSE_SOURCE_SPINE_CERTIFICATION")
    verify_entry_source(root, entry_report)
    root = Path(root)
    manifest_path = root/"manifest.json"
    raw_manifest = manifest_path.read_bytes()
    if spine.get("original_manifest_sha256") != hashlib.sha256(raw_manifest).hexdigest():
        raise ValueError("ORACLE_SOURCE_SPINE_MANIFEST_MISMATCH")
    entry = {(r["decision_ms"],r["asset"]):r for r in entry_report["rows"]}
    rows = spine.get("days")
    if not isinstance(rows, list) or len(rows) != DAYS:
        raise ValueError("ORACLE_INCOMPLETE_661D_SPINE")
    positions = {}
    fixed_asset_weeks = set()
    for row in rows:
        for event in row.get("market_events", []):
            if event.get("kind") != "OPEN_SOURCE_ONLY":
                continue
            name = event.get("position_id")
            key = (event.get("at_ms"),event.get("asset"))
            source = entry.get(key)
            if (not isinstance(name,str) or not name or name in positions
                    or key in fixed_asset_weeks
                    or source is None or source["signal"] != "POSITIVE_EX_ANTE_PREMIUM"
                    or event.get("candidate_inventory") != source["original_books"]):
                raise ValueError("ORACLE_FORGED_OR_DUPLICATE_SOURCE_OPEN")
            short = event.get("short_symbol_unverified_selection")
            long = event.get("long_symbol_unverified_selection")
            books = {q["symbol"]:q for q in source["original_books"]}
            if short not in books or long not in books:
                raise ValueError("ORACLE_NONORIGINAL_SOURCE_OPEN_CONTRACT")
            s,l = books[short],books[long]
            if (s["expiry_ms"] != l["expiry_ms"]
                    or _num(s["strike_usd"]) <= _num(l["strike_usd"])
                    or _num(s["bid_coin"]) <= _num(l["ask_coin"])
                    or abs(s["arrival_us"]-l["arrival_us"]) > 1_000_000
                    or abs(s["venue_us"]-l["venue_us"]) > 1_000_000):
                raise ValueError("ORACLE_UNSYNCHRONIZED_SOURCE_OPEN")
            positions[name] = (key[0],key[1],s,l)
            fixed_asset_weeks.add(key)
    if not positions or spine.get("unverified_position_plan_count") != len(positions):
        raise ValueError("ORACLE_INCOMPLETE_POSITION_PLAN")
    count = 0
    settlement_count = 0
    manifest = __import__("json").loads(raw_manifest)
    manifest_days = manifest["days"]
    for i,row in enumerate(rows):
        clock = START_MS + DAY_MS*i
        day = FIRST+timedelta(days=i)
        if row.get("ts_ms") != clock:
            raise ValueError("ORACLE_SHIFTED_SOURCE_DAY")
        day_start = clock-86_399_000
        expected = []
        wanted = set()
        for name,(at,asset,short,long) in positions.items():
            if day_start <= at <= clock:
                expected.append(("OPEN_SOURCE_ONLY",at,asset,name))
            if at <= clock < short["expiry_ms"]:
                expected.append(("MARK_SOURCE_ONLY",clock,asset,name))
                wanted.update((short["symbol"],long["symbol"]))
                count += 1
            if day_start <= short["expiry_ms"] <= clock:
                expected.append(("SETTLEMENT_DUE_SOURCE_ONLY",short["expiry_ms"],asset,name))
                settlement_count += 1
        actual = [(e.get("kind"),e.get("at_ms"),e.get("asset"),e.get("position_id"))
                  for e in row.get("market_events", [])]
        if actual != sorted(expected, key=lambda e:(e[1],e[0],e[3])):
            raise ValueError("ORACLE_MISSING_DUPLICATED_OR_SHIFTED_SOURCE_EVENT")
        if not wanted:
            continue
        item = manifest_days[i]
        path = root/(day.isoformat()+".csv.gz")
        if (item.get("date") != day.isoformat()
                or item.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise ValueError("ORACLE_CHANGED_ORIGINAL_MARK_DAY")
        latest = _last(path,day,clock,wanted,item["rows"])
        for event in row["market_events"]:
            if event["kind"] != "MARK_SOURCE_ONLY":
                continue
            _,asset,short,long = positions[event["position_id"]]
            for label,contract in (("short",short),("long",long)):
                receipt = event[label]
                raw = latest.get(contract["symbol"])
                if raw is None:
                    raise ValueError("ORACLE_MISSING_EXACT_HELD_MARK")
                original,venue,arrival,ordinal = raw
                if (not 0 <= venue <= arrival < clock*1000
                        or clock*1000-arrival > 300_000_000
                        or clock*1000-venue > 300_000_000):
                    raise ValueError("ORACLE_STALE_OR_FUTURE_MARK")
                if (receipt.get("symbol") != contract["symbol"]
                        or receipt.get("venue_us") != venue
                        or receipt.get("arrival_us") != arrival
                        or receipt.get("original_source_row_ordinal") != ordinal):
                    raise ValueError("ORACLE_FORGED_MARK_IDENTITY")
                for key,original_key in (
                    ("bid_coin","bid_price"),("ask_coin","ask_price"),
                    ("bid_size_source_units","bid_amount"),
                    ("ask_size_source_units","ask_amount")):
                    if _num(receipt.get(key)) != _num(original[original_key]):
                        raise ValueError("ORACLE_MARK_NOT_EQUAL_ORIGINAL")
                if not (0 < _num(original["bid_price"]) < _num(original["ask_price"])
                        and _num(original["bid_amount"]) > 0
                        and _num(original["ask_amount"]) > 0):
                    raise ValueError("ORACLE_INVALID_LATEST_MARK")
    if (spine.get("same_contract_daily_marks") != count
            or spine.get("expiry_due_count") != settlement_count
            or settlement_count != len(positions)):
        raise ValueError("ORACLE_SOURCE_SPINE_TOTAL_MISMATCH")
    return {"independent_661_days": DAYS,
            "independent_held_contract_mark_pairs": count,
            "independent_expiry_due": settlement_count,
            "original_economics_certified": False,
            "promotion_authorized": False}
