"""Independent original 90-week source-driven book re-execution, no production imports.

Checks byte hashes, latest physical-arrival record per put symbol, freshness,
contract tenor and source book fields. Does NOT certify vendor completeness,
index, native lot units, fills, economics or promotion.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIRST = date(2021, 12, 9)
LAST = date(2023, 10, 1)
DAY_MS = 86_400_000
COLUMNS = {"exchange", "symbol", "timestamp", "local_timestamp",
           "bid_price", "ask_price", "bid_amount", "ask_amount"}
SCHEMA = "V99_I1_SOURCE_DRIVEN_90W_ORIGINAL_ENTRY_BOOK_V1"


def _number(value):
    try:
        v = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("ORACLE_BAD_SOURCE_NUMBER") from exc
    if not v.is_finite():
        raise ValueError("ORACLE_NONFINITE_SOURCE_NUMBER")
    return v


def _replay_day(path, day, clock):
    start_us = int(datetime(day.year, day.month, day.day,
                            tzinfo=timezone.utc).timestamp()*1_000_000)
    latest = {}
    seen = 0
    last_arrival = -1
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError("ORACLE_MISSING_SOURCE_COLUMNS")
        for row in reader:
            seen += 1
            try:
                venue = int(row["timestamp"])
                arrival = int(row["local_timestamp"])
            except (ValueError, TypeError) as exc:
                raise ValueError("ORACLE_INVALID_CLOCK") from exc
            if (row["exchange"] != "deribit" or not 0 <= venue <= arrival
                    or not start_us <= arrival < start_us+86_400_000_000
                    or arrival < last_arrival or arrival >= clock*1000):
                raise ValueError("ORACLE_UNSAFE_OR_NONCAUSAL_SOURCE")
            last_arrival = arrival
            parts = row["symbol"].split("-")
            if len(parts) != 4 or parts[0] not in ("BTC", "ETH") or parts[3] != "P":
                continue
            try:
                expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(
                    hour=8, tzinfo=timezone.utc)
                strike = _number(parts[2])
            except (ValueError, OverflowError):
                continue
            exp_ms = int(expiry.timestamp()*1000)
            if not (strike > 0 and 28*DAY_MS <= exp_ms-clock <= 35*DAY_MS
                    and exp_ms < int(datetime(2023, 10, 1,
                                             tzinfo=timezone.utc).timestamp()*1000)):
                continue
            latest[row["symbol"]] = (row, venue, arrival, seen, exp_ms, strike)
    books = {"BTC": [], "ETH": []}
    invalid = {"BTC": 0, "ETH": 0}
    stale = {"BTC": 0, "ETH": 0}
    for symbol in sorted(latest):
        row, venue, arrival, ordinal, exp_ms, strike = latest[symbol]
        asset = symbol.split("-")[0]
        if clock*1000-arrival > 300_000_000 or clock*1000-venue > 300_000_000:
            stale[asset] += 1
            continue
        try:
            bid, ask, bs, a_s = [_number(row[k]) for k in (
                "bid_price", "ask_price", "bid_amount", "ask_amount")]
        except (ValueError, KeyError):
            invalid[asset] += 1
            continue
        if not (0 < bid < ask and bs > 0 and a_s > 0):
            invalid[asset] += 1
            continue
        books[asset].append({
            "symbol": symbol, "expiry_ms": exp_ms, "strike_usd": str(strike),
            "bid_coin": str(bid), "ask_coin": str(ask),
            "bid_size_source_units": str(bs), "ask_size_source_units": str(a_s),
            "venue_us": venue, "arrival_us": arrival,
            "original_source_row_ordinal": ordinal,
        })
    return books, invalid, stale, seen


def verify(root, report):
    root = Path(root)
    if (not isinstance(report, dict) or report.get("schema") != SCHEMA
            or report.get("economic_train_executed") is not False
            or report.get("promotion_authorized") is not False
            or report.get("original_underlying_index_authenticated") is not False):
        raise ValueError("ORACLE_FORGED_ENTRY_REPORT")
    manifest_path = root/"manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("ORACLE_ORIGINAL_MANIFEST_MISSING")
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if (manifest.get("fixture") is not False or manifest.get("venue") != "deribit"
            or manifest.get("train_start") != FIRST.isoformat()
            or manifest.get("train_end_exclusive") != LAST.isoformat()
            or report.get("source_manifest_sha256") != hashlib.sha256(raw).hexdigest()):
        raise ValueError("ORACLE_SOURCE_MANIFEST_MISMATCH")
    dates = [FIRST+timedelta(days=i) for i in range((LAST-FIRST).days)]
    manifest_days = manifest.get("days")
    if not isinstance(manifest_days, list) or len(manifest_days) != len(dates):
        raise ValueError("ORACLE_INCOMPLETE_661_DAY_ARCHIVE")
    sundays = {}
    for d, item in zip(dates, manifest_days):
        name = d.isoformat()+".csv.gz"
        if (item.get("date") != d.isoformat() or item.get("file") != name
                or item.get("complete_capture") is not True):
            raise ValueError("ORACLE_MISSING_OR_FORGED_SOURCE_DAY")
        path = root/name
        if not path.is_file() or path.is_symlink():
            raise ValueError("ORACLE_ORIGINAL_DAY_MISSING")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            raise ValueError("ORACLE_ORIGINAL_DAY_HASH_MISMATCH")
        if d.weekday() == 6:
            sundays[d] = (path, item, digest)
    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != 180:
        raise ValueError("ORACLE_INCOMPLETE_180_ENTRY_BOOKS")
    first_monday = date(2021, 12, 13)
    total = 0
    for week in range(90):
        monday = first_monday+timedelta(days=7*week)
        sunday = monday-timedelta(days=1)
        clock = int(datetime(monday.year, monday.month, monday.day,
                             tzinfo=timezone.utc).timestamp()*1000)
        path, item, digest = sundays[sunday]
        books, invalid, stale, seen = _replay_day(path, sunday, clock)
        if seen != item.get("rows"):
            raise ValueError("ORACLE_ORIGINAL_SUNDAY_ROW_COUNT_MISMATCH")
        total += seen
        for offset, asset in enumerate(("BTC", "ETH")):
            row = rows[week*2+offset]
            if (row.get("decision_ms") != clock or row.get("asset") != asset
                    or row.get("source_day") != sunday.isoformat()
                    or row.get("source_day_sha256") != digest
                    or row.get("source_rows_scanned") != seen
                    or row.get("original_books") != books[asset]
                    or row.get("last_eligible_invalid_books") != invalid[asset]
                    or row.get("last_eligible_stale_books") != stale[asset]):
                raise ValueError("ORACLE_SOURCE_DRIVEN_BOOK_DIVERGENCE")
    if (report.get("source_sundays_scanned") != 90
            or report.get("asset_week_decisions") != 180
            or report.get("source_original_quote_rows_scanned") != total):
        raise ValueError("ORACLE_SOURCE_COUNTS_MISMATCH")
    return {"independently_verified_asset_weeks": 180,
            "independently_verified_sundays": 90,
            "independently_reparsed_quote_rows": total,
            "source_only": True, "economic_train_certified": False,
            "promotion_authorized": False}
