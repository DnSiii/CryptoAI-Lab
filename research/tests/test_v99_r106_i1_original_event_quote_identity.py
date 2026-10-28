"""Adversarial original-byte quote/event identity tests; all sources SYNTHETIC."""
from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tests.test_v99_r106_i1_native_event_equity import (
    flat_fixture, ms, quote,
)
from research.tools.v99_r106_i1_original_event_quote_identity import (
    _equal, _last_original_quotes, _requests, audit,
)
from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS, SCHEMA as ARCHIVE_SCHEMA
from research.tools.v99_r106_i1_native_event_equity import _quote

HEADER = ["exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount"]


def original_row(q, *, arrival_offset_us=0, bid=None):
    return {"exchange": "deribit", "symbol": q["symbol"],
            "timestamp": str(q["venue_ms"] * 1000),
            "local_timestamp": str(q["arrival_ms"] * 1000 + arrival_offset_us),
            "bid_price": str(bid if bid is not None else q["bid_coin"]),
            "ask_price": str(q["ask_coin"]),
            "bid_amount": str(q["bid_native_lots"]),
            "ask_amount": str(q["ask_native_lots"]),
            "index_price": str(q["index_usd"])}


def input_document():
    doc = flat_fixture()
    doc["fixture"] = False
    at = ms(2021, 12, 13)
    short = quote("BTC-14JAN22-36000-P", "0.05", "0.052", at)
    long = quote("BTC-14JAN22-32000-P", "0.008", "0.01", at)
    for scenario in ("severe", "supersevere"):
        row = next(d for d in doc["scenarios"][scenario]
                   if d["ts_ms"] == ms(2021, 12, 13, 23, 59, 59))
        row["events"].append({"kind": "OPEN", "at_ms": at,
                              "asset": "BTC", "quotes": [short, long]})
    return doc, short, long


def write_csv_gz(path, rows):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


class OriginalQuoteIdentityTests(unittest.TestCase):
    def test_last_asof_source_quote_exact_equality(self):
        doc, short, long = input_document()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2021-12-12.csv.gz"
            write_csv_gz(path, [original_row(short), original_row(long)])
            req = _requests(doc)
            last = _last_original_quotes(
                {datetime(2021, 12, 12, tzinfo=timezone.utc).date(): (path, 2)}, req)
            self.assertEqual(len(req), 2)
            for key, q in req.items():
                self.assertTrue(_equal(q, last.get(key), key[0]))

    def test_later_invalid_receipt_revokes_earlier_valid(self):
        doc, short, long = input_document()
        at = ms(2021, 12, 13)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2021-12-12.csv.gz"
            invalid = original_row(short, arrival_offset_us=100, bid="0")
            write_csv_gz(path, [original_row(short), original_row(long), invalid])
            req = _requests(doc)
            last = _last_original_quotes(
                {datetime(2021, 12, 12, tzinfo=timezone.utc).date(): (path, 3)}, req)
            with self.assertRaisesRegex(ValueError, "LATEST_ORIGINAL_RECEIPT_INVALID"):
                _equal(_quote(short), last[(at, "BTC", short["symbol"])], at)

    def test_forged_bid_or_size_rejected(self):
        doc, short, long = input_document()
        at = ms(2021, 12, 13)
        source = (short["arrival_ms"] * 1000, 1, 1, short["venue_ms"] * 1000,
                  original_row(short))
        for field, value in (("bid_coin", "0.06"), ("ask_native_lots", "3"),
                             ("index_usd", "41000")):
            fake = dict(short)
            fake[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "NOT_EQUAL_ORIGINAL_SOURCE"):
                _equal(_quote(fake), source, at)

    def test_quote_csv_cannot_certify_underlying_index(self):
        doc, short, _ = input_document()
        at = ms(2021, 12, 13)
        source = (short["arrival_ms"] * 1000, 1, 1, short["venue_ms"] * 1000,
                  original_row(short))
        forged = dict(short)
        forged["index_usd"] = "41000"
        # BBO-only oracle must not claim it detected or authenticated index.
        self.assertTrue(_equal(_quote(forged), source, at))

    def test_postdecision_original_row_not_usable(self):
        doc, short, long = input_document()
        at = ms(2021, 12, 13)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2021-12-13.csv.gz"
            later = original_row(short)
            later["timestamp"] = str((at + 1000) * 1000)
            later["local_timestamp"] = str((at + 2000) * 1000)
            write_csv_gz(path, [later])
            req = _requests(doc)
            last = _last_original_quotes(
                {datetime(2021, 12, 13, tzinfo=timezone.utc).date(): (path, 1)}, req)
            with self.assertRaisesRegex(ValueError, "MISSING_ORIGINAL_LAST"):
                _equal(_quote(short), last.get((at, "BTC", short["symbol"])), at)

    def test_missing_661d_original_archive_blocks_real_run(self):
        doc, _, _ = input_document()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "ORIGINAL_661D_MANIFEST_NOT_DELIVERED"):
                audit(tmp, doc)

    def test_full_661d_synthetic_byte_inventory_and_tamper(self):
        doc, short, long = input_document()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            days = []
            for i in range(DAYS):
                day = FIRST + timedelta(days=i)
                name = day.isoformat() + ".csv.gz"
                path = root / name
                if day.isoformat() == "2021-12-12":
                    rows = [original_row(short), original_row(long)]
                else:
                    at = int(datetime(day.year, day.month, day.day, 12,
                                      tzinfo=timezone.utc).timestamp() * 1000)
                    dummy = quote("BTC-14JAN22-36000-P", "0.05", "0.052",
                                  ms(2021, 12, 13))
                    dummy["venue_ms"] = at - 1000
                    dummy["arrival_ms"] = at
                    rows = [original_row(dummy)]
                write_csv_gz(path, rows)
                days.append({"date": day.isoformat(), "file": name,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "rows": len(rows), "complete_capture": True})
            manifest = {"schema": ARCHIVE_SCHEMA, "fixture": False, "venue": "deribit",
                        "train_start": FIRST.isoformat(),
                        "train_end_exclusive": (FIRST + timedelta(days=DAYS)).isoformat(),
                        "license_evidence_sha256_not_legal_verification": "a"*64,
                        "days": days}
            (root / "manifest.json").write_text(json.dumps(manifest))
            result = audit(root, doc)
            self.assertEqual(result["original_quote_events_checked"], 2)
            self.assertFalse(result["source_size_unit_is_native_lot_certified"])
            self.assertFalse(result["original_underlying_index_bound"])
            self.assertFalse(result["promotion_authorized"])
            with gzip.open(root / "2021-12-12.csv.gz", "ab") as stream:
                stream.write(b"tamper")
            with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_SHA256_MISMATCH"):
                audit(root, doc)


if __name__ == "__main__":
    unittest.main()
