"""661-day synthetic fixtures only. Never original exchange economic evidence."""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import (
    FIRST, END, DAYS, build_manifest, run,
)
from research.tools.v99_r106_i1_lifecycle_daily_tape import audit
from research.verification.independent_v99_r106_i1_lifecycle_daily_oracle import verify

HEADERS = ("exchange", "symbol", "timestamp", "local_timestamp",
           "bid_price", "ask_price", "bid_amount", "ask_amount")


def write_day(root: Path, day: date, *, reverse=False):
    expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
    start = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp() * 1_000_000)
    b = io.StringIO(newline="")
    writer = csv.writer(b)
    writer.writerow(HEADERS)
    rows = [
        ("deribit", f"BTC-{expiry}-30000-P", start+1_000_000,
         start+1_000_000, "0.02", "0.025", "1", "1"),
        ("deribit", f"ETH-{expiry}-2000-P", start+2_000_000,
         start+2_000_000, "0.02", "0.025", "1", "1"),
    ]
    writer.writerows(reversed(rows) if reverse else rows)
    (root / (day.isoformat()+".csv.gz")).write_bytes(gzip.compress(b.getvalue().encode()))


class LocalTapeImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory()
        cls.original = Path(cls.base.name)
        for i in range(DAYS):
            write_day(cls.original, FIRST + timedelta(days=i))

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "tape"
        shutil.copytree(self.original, self.root)

    def test_real_661_day_import_to_existing_independent_oracle(self):
        result = run(self.root, fixture=True)
        self.assertEqual(len(result["days"]), 661)
        self.assertEqual(sum(d["rows"] for d in result["days"]), 1322)
        self.assertFalse(result["promotion_authorized"])
        self.assertTrue(result["source_manifest_self_declared_not_vendor_certified"])
        self.assertTrue(result["quote_content_presence_not_lifecycle_or_vendor_certified"])
        self.assertEqual(result["days"][0]["qualifying_original_put_quote_rows_by_asset"],
                         {"BTC": 1, "ETH": 1})
        source = audit(self.root)
        independent = verify(self.root, source)
        self.assertEqual(independent["days"], 661)
        self.assertEqual(independent["certified_complete_option_lifecycles"], 0)
        self.assertEqual(source["asset_weeks"], 180)
        self.assertFalse(source["economic_train_executed"])

    def test_missing_day_rejected_without_manifest(self):
        (self.root / (FIRST + timedelta(days=5)).isoformat().__add__(".csv.gz")).unlink()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_EXTRA"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_extra_sealed_day_rejected_without_manifest(self):
        write_day(self.root, END)
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_EXTRA"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_corrupted_gzip_rejected_without_manifest(self):
        (self.root / (FIRST.isoformat()+".csv.gz")).write_bytes(b"not gzip")
        with self.assertRaisesRegex(ValueError, "CORRUPT_ORIGINAL_GZIP"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_last_arrival_out_of_order_rejected(self):
        write_day(self.root, FIRST, reverse=True)
        with self.assertRaisesRegex(ValueError, "NONCAUSAL_OR_OUT_OF_ORDER_CLOCK"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def _rewrite_first_day(self, *, btc_symbol=None, eth_symbol=None,
                           eth_bid="0.02", eth_ask="0.025", eth_size="1",
                           include_eth=True, btc_event_age_us=0):
        day = FIRST
        expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
        start = int(datetime(day.year, day.month, day.day,
                             tzinfo=timezone.utc).timestamp() * 1_000_000)
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(HEADERS)
        writer.writerow(("deribit", btc_symbol or f"BTC-{expiry}-30000-P",
                         start+1_000_000-btc_event_age_us, start+1_000_000,
                         "0.02", "0.025", "1", "1"))
        if include_eth:
            writer.writerow(("deribit", eth_symbol or f"ETH-{expiry}-2000-P",
                             start+2_000_000, start+2_000_000,
                             eth_bid, eth_ask, eth_size, "1"))
        (self.root / (day.isoformat()+".csv.gz")).write_bytes(
            gzip.compress(buffer.getvalue().encode()))

    def test_single_asset_archive_day_rejected_atomically(self):
        self._rewrite_first_day(include_eth=False)
        with self.assertRaisesRegex(ValueError, "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:2021-12-09:ETH"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_future_instead_of_btc_put_rejected_atomically(self):
        self._rewrite_first_day(btc_symbol="BTC-PERPETUAL")
        with self.assertRaisesRegex(ValueError, "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:2021-12-09:BTC"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_expired_btc_put_rejected_atomically(self):
        self._rewrite_first_day(btc_symbol="BTC-01DEC21-30000-P")
        with self.assertRaisesRegex(ValueError, "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:2021-12-09:BTC"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_stale_only_btc_receipt_rejected_atomically(self):
        self._rewrite_first_day(btc_event_age_us=301_000_000)
        with self.assertRaisesRegex(ValueError, "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:2021-12-09:BTC"):
            run(self.root, fixture=True)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_crossed_or_zero_sized_eth_books_rejected_atomically(self):
        for kwargs in ({"eth_bid": "0.03", "eth_ask": "0.02"},
                       {"eth_size": "0"}):
            with self.subTest(kwargs=kwargs):
                self._rewrite_first_day(**kwargs)
                with self.assertRaisesRegex(ValueError, "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES:2021-12-09:ETH"):
                    run(self.root, fixture=True)
                self.assertFalse((self.root / "manifest.json").exists())

    def test_existing_manifest_never_overwritten(self):
        (self.root / "manifest.json").write_text("protected", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "REFUSE_OVERWRITE"):
            run(self.root, fixture=True)
        self.assertEqual((self.root / "manifest.json").read_text(), "protected")

    def test_nonfixture_requires_local_evidence_but_never_certifies_it(self):
        with self.assertRaisesRegex(ValueError, "NONFIXTURE_LICENSE_EVIDENCE_REQUIRED"):
            build_manifest(self.root, fixture=False)
        evidence = Path(self.tmp.name) / "license.txt"
        evidence.write_text("SELF DECLARED PLACEHOLDER: NOT A VALID LICENSE", encoding="utf-8")
        manifest = build_manifest(self.root, fixture=False, license_evidence=evidence)
        # This is a synthetic test of the input interface, NOT a nonfixture run.
        self.assertFalse((self.root / 'manifest.json').exists())
        self.assertEqual(manifest["license_evidence_sha256_not_legal_verification"],
                         hashlib.sha256(evidence.read_bytes()).hexdigest())
        self.assertTrue(manifest["source_manifest_self_declared_not_vendor_certified"])
        self.assertFalse(manifest["economic_train_executed"])
        self.assertFalse(manifest["promotion_authorized"])


if __name__ == "__main__":
    unittest.main()
