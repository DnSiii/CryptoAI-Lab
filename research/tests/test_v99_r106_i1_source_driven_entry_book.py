"""Synthetic source-shaped controls; never an original Deribit economic result."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_local_tape_import import FIRST, DAYS, SCHEMA
from research.tools.v99_r106_i1_source_driven_entry_book import build
from research.verification.independent_v99_r106_i1_source_entry_book_oracle import verify

HEADER = ("exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount")
SUNDAY = datetime(2021, 12, 12, tzinfo=timezone.utc)


def source_row(symbol, day, hour, minute, second, bid="0.05", ask="0.052"):
    at = int(day.replace(hour=hour, minute=minute, second=second).timestamp()*1_000_000)
    return dict(exchange="deribit", symbol=symbol, timestamp=str(at-1000),
                local_timestamp=str(at), bid_price=bid, ask_price=ask,
                bid_amount="2", ask_amount="2")


def write_gzip(path, rows):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)


def intents():
    return [{"decision_ms": int(d.timestamp()*1000), "asset": asset,
             "fold": __import__(
                 "research.tools.v99_r106_i1_train_numeric_gate",
                 fromlist=["_fold"])._fold(int(d.timestamp()*1000)),
             "signal": ("POSITIVE_EX_ANTE_PREMIUM" if i == 0 else "NO_PREMIUM")}
            for i, d in enumerate(eligible(True)) for asset in ("BTC", "ETH")]


class SourceDrivenEntryBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.days = []
        cls.original = [
            source_row("BTC-14JAN22-36000-P", SUNDAY, 23, 59, 58),
            source_row("BTC-14JAN22-32000-P", SUNDAY, 23, 59, 58, "0.01", "0.012"),
            source_row("ETH-14JAN22-2700-P", SUNDAY, 23, 59, 58),
        ]
        for i in range(DAYS):
            d = FIRST + timedelta(days=i)
            path = cls.root / (d.isoformat()+".csv.gz")
            if d == SUNDAY.date():
                rows = cls.original
            else:
                dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
                rows = [source_row("BTC-14JAN22-36000-P", dt, 12, 0, 0)]
            write_gzip(path, rows)
            cls.days.append({"date": d.isoformat(), "file": path.name,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "rows": len(rows), "complete_capture": True})
        cls.manifest = {
            "schema": SCHEMA, "fixture": False, "venue": "deribit",
            "train_start": FIRST.isoformat(),
            "train_end_exclusive": (FIRST + timedelta(days=DAYS)).isoformat(),
            "license_evidence_sha256_not_legal_verification": "f"*64,
            "days": cls.days,
        }
        cls.save_manifest()

    @classmethod
    def save_manifest(cls):
        (cls.root/"manifest.json").write_text(json.dumps(cls.manifest))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def update_sunday(self, rows):
        path = self.root/"2021-12-12.csv.gz"
        write_gzip(path, rows)
        day = next(d for d in self.days if d["date"] == "2021-12-12")
        day["rows"] = len(rows)
        day["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.save_manifest()

    def tearDown(self):
        self.update_sunday(self.original)

    def test_all_fixed_mondays_and_source_selected_books(self):
        out = build(self.root, intents())
        self.assertEqual(out["asset_week_decisions"], 180)
        self.assertEqual(out["source_sundays_scanned"], 90)
        self.assertEqual(len(out["rows"][0]["original_books"]), 2)
        self.assertEqual(len(out["rows"][1]["original_books"]), 1)
        self.assertEqual(out["rows"][0]["original_books"][0]["symbol"],
                         "BTC-14JAN22-32000-P")
        self.assertEqual(out["rows"][0]["original_books"][0]["original_source_row_ordinal"], 2)
        self.assertFalse(out["economic_train_executed"])
        self.assertFalse(out["original_underlying_index_authenticated"])
        self.assertFalse(out["promotion_authorized"])

    def test_independent_original_byte_replay_and_adversarial_book(self):
        out = build(self.root, intents())
        verified = verify(self.root, out)
        self.assertEqual(verified['independently_verified_asset_weeks'], 180)
        self.assertEqual(verified['independently_verified_sundays'], 90)
        out['rows'][0]['original_books'][0]['bid_coin'] = '999'
        with self.assertRaisesRegex(ValueError, 'ORACLE_SOURCE_DRIVEN_BOOK_DIVERGENCE'):
            verify(self.root, out)

    def test_last_invalid_quote_revokes_earlier_valid(self):
        self.update_sunday(self.original + [
            source_row("BTC-14JAN22-36000-P", SUNDAY, 23, 59, 59, bid="0")])
        out = build(self.root, intents())
        self.assertEqual(out["rows"][0]["last_eligible_invalid_books"], 1)
        self.assertEqual([q["symbol"] for q in out["rows"][0]["original_books"]],
                         ["BTC-14JAN22-32000-P"])

    def test_after_decision_monday_not_scanned(self):
        # Sunday source contains only pre-decision rows. Monday noon quotes
        # are never eligible for the Monday 00:00 decision.
        out = build(self.root, intents())
        self.assertTrue(all(q["arrival_us"] < out["rows"][0]["decision_ms"]*1000
                            for q in out["rows"][0]["original_books"]))

    def test_out_of_order_capture_rejected(self):
        self.update_sunday([source_row("BTC-14JAN22-36000-P", SUNDAY, 23, 59, 59), self.original[0]])
        with self.assertRaisesRegex(ValueError, "ORIGINAL_CAPTURE_ORDER"):
            build(self.root, intents())

    def test_modified_bytes_without_manifest_update_rejected(self):
        path = self.root/"2021-12-12.csv.gz"
        with path.open("ab") as f:
            f.write(b"tamper")
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_SHA256_MISMATCH"):
            build(self.root, intents())

    def test_missing_archive_and_forged_grid_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "ORIGINAL_661D_MANIFEST_NOT_DELIVERED"):
                build(tmp, intents())
        bad = intents()
        bad[0]["decision_ms"] += 1000
        with self.assertRaisesRegex(ValueError, "UNBOUND_FIXED_TRAIN_INTENT_GRID"):
            build(self.root, bad)

    def test_out_of_tenor_not_a_source_candidate(self):
        self.update_sunday(self.original + [
            source_row("BTC-31DEC21-36000-P", SUNDAY, 23, 59, 59)])
        out = build(self.root, intents())
        self.assertEqual(len(out["rows"][0]["original_books"]), 2)


if __name__ == "__main__":
    unittest.main()
