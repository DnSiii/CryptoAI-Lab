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
from unittest import mock
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import (
    FIRST, END, DAYS, build_manifest, run, scan_day, require_hourly_original_coverage,
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

    def test_concurrent_manifest_writer_never_overwritten(self):
        # Simulate a separate process publishing after the pre-scan check,
        # but before our atomic link. os.replace() would clobber its bytes.
        target = self.root / "manifest.json"
        def concurrent_publish(_temporary, _target):
            self.assertEqual(Path(_target), target)
            target.write_bytes(b"COMPETING_WRITER_ORIGINAL_BYTES")
            raise FileExistsError("atomic link refuses overwrite")
        with mock.patch(
            "research.tools.v99_r106_i1_local_tape_import.os.link",
            side_effect=concurrent_publish,
        ):
            with self.assertRaisesRegex(ValueError, "REFUSE_OVERWRITE_EXISTING_MANIFEST"):
                run(self.root, fixture=True)
        self.assertEqual(target.read_bytes(), b"COMPETING_WRITER_ORIGINAL_BYTES")
        self.assertEqual(list(self.root.glob(".manifest.*.tmp")), [])

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
        # A self-declared license document cannot turn a partial-day synthetic
        # archive into 661 complete original source days.
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            build_manifest(self.root, fixture=False, license_evidence=evidence)
        self.assertFalse((self.root / 'manifest.json').exists())

    def test_repeated_symbol_cache_never_caches_market_quote_validity(self):
        # Same contract appears with changing market fields. Only the immutable
        # expiry/strike may be cached; later crossed books stay invalid.
        day = FIRST
        expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
        start = int(datetime(day.year, day.month, day.day,
                             tzinfo=timezone.utc).timestamp() * 1_000_000)
        path = self.root / (day.isoformat() + ".csv.gz")
        buf = io.StringIO(newline="")
        writer = csv.writer(buf)
        writer.writerow(HEADERS)
        for hour in range(24):
            t = start + hour * 3_600_000_000
            btc = f"BTC-{expiry}-30000-P"
            eth = f"ETH-{expiry}-2000-P"
            writer.writerow(("deribit", btc, t+1, t+1,
                             "0.02", "0.025", "1", "1"))
            writer.writerow(("deribit", btc, t+2, t+2,
                             "0.03", "0.025", "1", "1"))
            writer.writerow(("deribit", eth, t+3, t+3,
                             "0.02", "0.025", "1", "1"))
            writer.writerow(("deribit", "BTC-NOTADATE-30000-P", t+4, t+4,
                             "0.02", "0.025", "1", "1"))
        path.write_bytes(gzip.compress(buf.getvalue().encode()))
        result = scan_day(path, day)
        self.assertEqual(result["rows"], 96)
        self.assertEqual(result["qualifying_original_put_quote_rows_by_asset"],
                         {"BTC": 24, "ETH": 24})
        self.assertEqual(result["descriptive_28_45d_put_quote_rows_by_asset"],
                         {"BTC": 24, "ETH": 24})
        require_hourly_original_coverage(result)

    def test_single_day_full_hourly_presence_is_necessary_not_sufficient(self):
        day = FIRST
        expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
        start = int(datetime(day.year, day.month, day.day,
                             tzinfo=timezone.utc).timestamp() * 1_000_000)
        path = self.root / (day.isoformat() + ".csv.gz")
        def write_hours(skip=None):
            buf = io.StringIO(newline="")
            w = csv.writer(buf)
            w.writerow(HEADERS)
            for hour in range(24):
                if hour == skip:
                    continue
                for i, asset in enumerate(("BTC", "ETH")):
                    t = start + hour*3_600_000_000 + (i+1)*1_000_000
                    w.writerow(("deribit", f"{asset}-{expiry}-30000-P",
                                t, t, "0.02", "0.025", "1", "1"))
            path.write_bytes(gzip.compress(buf.getvalue().encode()))
        write_hours()
        full = scan_day(path, day)
        require_hourly_original_coverage(full)
        self.assertEqual(full["qualifying_original_put_arrival_hours_by_asset"],
                         {"BTC": 24, "ETH": 24})
        write_hours(skip=12)
        partial = scan_day(path, day)
        self.assertEqual(partial["qualifying_original_put_arrival_hours_by_asset"],
                         {"BTC": 23, "ETH": 23})
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            require_hourly_original_coverage(partial)


    def test_live_any_tenor_feed_does_not_forge_fixed_tenor_availability(self):
        # A real options feed can have no puts inside the strategy tenor.
        # That is a market-universe zero, not a 24-hour transport gap.
        day = FIRST
        expiry = (day + timedelta(days=60)).strftime("%d%b%y").upper()
        start = int(datetime(day.year, day.month, day.day,
                             tzinfo=timezone.utc).timestamp() * 1_000_000)
        path = self.root / (day.isoformat() + ".csv.gz")
        def write_hours(missing=None):
            buf = io.StringIO(newline="")
            writer = csv.writer(buf)
            writer.writerow(HEADERS)
            for hour in range(24):
                if hour == missing:
                    continue
                for i, asset in enumerate(("BTC", "ETH")):
                    t = start + hour*3_600_000_000 + (i+1)*1_000_000
                    writer.writerow(("deribit", f"{asset}-{expiry}-30000-P",
                                     t, t, "0.02", "0.025", "1", "1"))
            path.write_bytes(gzip.compress(buf.getvalue().encode()))
        write_hours()
        source = scan_day(path, day)
        self.assertEqual(source["live_original_put_arrival_hours_by_asset"],
                         {"BTC": 24, "ETH": 24})
        self.assertEqual(source["qualifying_original_put_quote_rows_by_asset"],
                         {"BTC": 0, "ETH": 0})
        self.assertEqual(source["descriptive_28_45d_put_quote_rows_by_asset"],
                         {"BTC": 0, "ETH": 0})
        require_hourly_original_coverage(source)
        manifest = run(self.root, fixture=True)
        self.assertEqual(manifest["days"][0]["qualifying_original_put_quote_rows_by_asset"],
                         {"BTC": 0, "ETH": 0})
        lifecycle = audit(self.root)
        independent = verify(self.root, lifecycle)
        self.assertTrue(lifecycle["daily"][0]["BTC"])
        self.assertTrue(lifecycle["daily"][0]["ETH"])
        self.assertEqual(independent["days"], 661)
        self.assertEqual(independent["certified_complete_option_lifecycles"], 0)
        manifest["days"][0]["live_original_put_arrival_hours_by_asset"]["BTC"] = 23
        (self.root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_LIVE_OPTION_FEED_COVERAGE_MISMATCH"):
            verify(self.root, lifecycle)
        manifest["days"][0]["live_original_put_arrival_hours_by_asset"]["BTC"] = 24
        (self.root / "manifest.json").write_text(json.dumps(manifest))
        write_hours(missing=12)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP"):
            require_hourly_original_coverage(scan_day(path, day))


if __name__ == "__main__":
    unittest.main()
