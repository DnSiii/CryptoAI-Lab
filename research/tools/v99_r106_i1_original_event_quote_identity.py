"""Fail-closed ORIGINAL Deribit CSV -> native OPEN/MARK quote identity audit.

Checks the actual last pre-event original receipt, not caller supplied flags.
No fee/margin/settlement/fill certification, NAV, PnL or orders.
Prereg: research/V99_R106_I1_ORIGINAL_EVENT_QUOTE_IDENTITY_PREREG_20261028.md
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_native_event_equity import _quote, SCHEMA
from research.tools.v99_r106_i1_local_tape_import import FIRST, END, DAYS, SCHEMA as ARCHIVE_SCHEMA
from research.tools.v99_r106_i1_native_coin_account_replay import D

SCHEMA_OUT = "V99_I1_ORIGINAL_NATIVE_EVENT_QUOTE_IDENTITY_V1"
COLUMNS = {"exchange", "symbol", "timestamp", "local_timestamp",
           "bid_price", "ask_price", "bid_amount", "ask_amount", "index_price"}


def _digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _original_manifest(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("ORIGINAL_661D_ARCHIVE_NOT_DELIVERED")
    path = root / "manifest.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("ORIGINAL_661D_MANIFEST_NOT_DELIVERED")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("schema") != ARCHIVE_SCHEMA or doc.get("fixture") is not False
            or doc.get("venue") != "deribit"
            or doc.get("train_start") != FIRST.isoformat()
            or doc.get("train_end_exclusive") != END.isoformat()
            or not isinstance(doc.get("days"), list) or len(doc["days"]) != DAYS
            or not isinstance(doc.get("license_evidence_sha256_not_legal_verification"), str)
            or len(doc["license_evidence_sha256_not_legal_verification"]) != 64):
        raise ValueError("INCOMPLETE_OR_SELF_DECLARED_FIXTURE_ARCHIVE")
    files = {}
    for i, item in enumerate(doc["days"]):
        day = FIRST + timedelta(days=i)
        name = day.isoformat() + ".csv.gz"
        if (not isinstance(item, dict) or item.get("date") != day.isoformat()
                or item.get("file") != name or item.get("complete_capture") is not True
                or type(item.get("rows")) is not int or item["rows"] <= 0
                or not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64):
            raise ValueError("FORGED_OR_MISSING_ORIGINAL_DAY")
        source = root / name
        if not source.is_file() or source.is_symlink():
            raise ValueError("MISSING_OR_UNSAFE_ORIGINAL_DAY:" + day.isoformat())
        if _digest(source) != item["sha256"]:
            raise ValueError("ORIGINAL_DAY_SHA256_MISMATCH:" + day.isoformat())
        files[day] = (source, item["rows"])
    return files, _digest(path)


def _requests(journal):
    if (not isinstance(journal, dict) or journal.get("schema") != SCHEMA
            or journal.get("fixture") is not False
            or set(journal.get("scenarios", {})) != {"severe", "supersevere"}):
        raise ValueError("NONFIXTURE_NATIVE_EVENT_JOURNAL_REQUIRED")
    requests = {}
    for scenario in ("severe", "supersevere"):
        days = journal["scenarios"][scenario]
        if not isinstance(days, list) or len(days) != DAYS:
            raise ValueError("INCOMPLETE_NATIVE_EVENT_DAYS")
        for day in days:
            if not isinstance(day, dict) or not isinstance(day.get("events"), list):
                raise ValueError("MISSING_NATIVE_EVENT_JOURNAL")
            for event in day["events"]:
                kind = event.get("kind")
                if kind not in ("OPEN", "MARK", "SETTLE_BATCH"):
                    raise ValueError("UNREGISTERED_NATIVE_EVENT")
                if kind == "SETTLE_BATCH":
                    continue  # delivery index is a SEPARATE original receipt gate
                at = event.get("at_ms")
                if type(at) is not int:
                    raise ValueError("INVALID_NATIVE_EVENT_CLOCK")
                quotes = event.get("quotes") if kind == "OPEN" else [
                    event.get("short"), event.get("long")]
                if not isinstance(quotes, list) or not quotes:
                    raise ValueError("MISSING_NATIVE_EVENT_QUOTES")
                for raw in quotes:
                    q = _quote(raw)
                    q.check(at)
                    if q.asset != event.get("asset"):
                        raise ValueError("CROSS_ASSET_EVENT_QUOTE")
                    key = (at, q.asset, q.symbol)
                    previous = requests.get(key)
                    if previous is not None and previous != q:
                        raise ValueError("SCENARIO_SOURCE_QUOTE_MISMATCH")
                    requests[key] = q
    return requests


def _last_original_quotes(files, requests):
    """Stream only relevant arrival-day gzip files; latest invalid row revokes."""
    wanted = defaultdict(lambda: defaultdict(list))
    for key in requests:
        at, _, symbol = key
        clock_day = datetime.fromtimestamp(at / 1000, timezone.utc).date()
        for day in (clock_day - timedelta(days=1), clock_day):
            if day in files:
                wanted[day][symbol].append(key)
    best = {}
    for day in sorted(wanted):
        path, expected_rows = files[day]
        lower = int(datetime(day.year, day.month, day.day,
                             tzinfo=timezone.utc).timestamp() * 1_000_000)
        upper = lower + 86_400_000_000
        previous_arrival = -1
        count = 0
        with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not COLUMNS.issubset(reader.fieldnames or []):
                raise ValueError("ORIGINAL_INDEX_OR_QUOTE_COLUMNS_MISSING")
            for row in reader:
                count += 1
                if row["exchange"] != "deribit":
                    raise ValueError("ORIGINAL_EXCHANGE_MISMATCH")
                try:
                    venue_us = int(row["timestamp"])
                    arrival_us = int(row["local_timestamp"])
                except (ValueError, TypeError) as exc:
                    raise ValueError("INVALID_ORIGINAL_MICROSECOND_CLOCK") from exc
                if not (0 <= venue_us <= arrival_us
                        and lower <= arrival_us < upper
                        and arrival_us >= previous_arrival):
                    raise ValueError("NONCAUSAL_OR_REORDERED_ORIGINAL_RECEIPT")
                previous_arrival = arrival_us
                for key in wanted[day].get(row["symbol"], ()):
                    if arrival_us >= key[0] * 1000:
                        continue
                    # The LAST pre-event raw record wins, even if crossed,
                    # stale, zero-size or missing an original index.
                    candidate = (arrival_us, day.toordinal(), count, venue_us, row)
                    if key not in best or candidate[:3] > best[key][:3]:
                        best[key] = candidate
        if count != expected_rows:
            raise ValueError("ORIGINAL_SOURCE_ROW_COUNT_MISMATCH")
    return best


def _equal(q, source, at):
    if source is None:
        raise ValueError("MISSING_ORIGINAL_LAST_ASOF_RECEIPT")
    arrival, _, _, venue, row = source
    if not (0 <= venue <= arrival < at * 1000
            and at * 1000 - arrival <= 300_000_000
            and at * 1000 - venue <= 300_000_000
            and venue // 1000 == q.venue_ms
            and arrival // 1000 == q.arrival_ms):
        raise ValueError("STALE_FUTURE_OR_FORGED_ORIGINAL_CLOCK")
    try:
        fields = (D(row["bid_price"]), D(row["ask_price"]),
                  D(row["bid_amount"]), D(row["ask_amount"]), D(row["index_price"]))
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("MISSING_OR_INVALID_ORIGINAL_INDEX_OR_BOOK") from exc
    if not (fields[0] > 0 and fields[0] < fields[1]
            and fields[2] > 0 and fields[3] > 0 and fields[4] > 0):
        raise ValueError("LATEST_ORIGINAL_RECEIPT_INVALID_REVOKES_EARLIER")
    if fields != (q.bid_coin, q.ask_coin, q.bid_native_lots,
                  q.ask_native_lots, q.index_usd):
        raise ValueError("NATIVE_EVENT_QUOTE_NOT_EQUAL_ORIGINAL_SOURCE")
    # Equality of displayed source size and native_lots is NOT proof that
    # the source unit is a Deribit native contract. Never certify quantity.
    return True


def audit(root, journal):
    files, manifest_sha = _original_manifest(Path(root))
    requests = _requests(journal)
    last = _last_original_quotes(files, requests)
    for key, q in requests.items():
        _equal(q, last.get(key), key[0])
    return {
        "schema": SCHEMA_OUT,
        "status": "ORIGINAL_QUOTE_BYTES_EQUAL_ONLY_NATIVE_TERMS_UNCERTIFIED",
        "original_manifest_sha256": manifest_sha,
        "original_quote_events_checked": len(requests),
        "original_source_quote_equality": True,
        "vendor_completeness_independently_certified": False,
        "source_size_unit_is_native_lot_certified": False,
        "original_delivery_index_and_fee_certified": False,
        "historical_native_margin_liquidation_certified": False,
        "historical_execution_or_fills_certified": False,
        "original_historical_economic_train_executed": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False, "promotion_authorized": False,
    }


def main(root, journal_path, output_path):
    journal = json.loads(Path(journal_path).read_text(encoding="utf-8"))
    report = audit(root, journal)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                                 encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "original_quote_events_checked": report["original_quote_events_checked"],
                      "economic_train_certified": False, "promotion_authorized": False}))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_original_event_quote_identity ORIGINAL_661D_ROOT NONFIXTURE_NATIVE_EVENT_JSON OUTPUT_JSON")
    main(*sys.argv[1:])
