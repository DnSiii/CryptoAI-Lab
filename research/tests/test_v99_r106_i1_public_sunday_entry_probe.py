"""Offline adversarial tests: these never certify original market data."""
from __future__ import annotations

import csv
import gzip
import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_public_sunday_entry_probe import (
    SUNDAY, DECISION_MS, analyze_file, probe_live,
)
from research.tools.v99_r106_i1_train_numeric_gate import _fold


def intents():
    return [
        {"decision_ms": int(d.timestamp()*1000), "asset": asset,
         "fold": _fold(int(d.timestamp()*1000)),
         "signal": "POSITIVE_EX_ANTE_PREMIUM" if int(d.timestamp()*1000) == DECISION_MS
                   else "NO_PREMIUM"}
        for d in eligible(True) for asset in ("BTC", "ETH")
    ]


def make_day(*, crossed_last=False, stale=False, omit_eth=False, missing_hour=None,
             wrong_day=False):
    day = SUNDAY + timedelta(days=1 if wrong_day else 0)
    rows = io.StringIO(newline="")
    writer = csv.writer(rows)
    writer.writerow(("exchange", "symbol", "timestamp", "local_timestamp",
                     "bid_price", "ask_price", "bid_amount", "ask_amount"))
    start = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp()*1_000_000)
    for hour in range(24):
        if hour == missing_hour:
            continue
        for asset in (("BTC",) if omit_eth else ("BTC", "ETH")):
            for strike in (2000, 2100):
                us = start + hour*3_600_000_000 + 10_000_000
                symbol = f"{asset}-03JUN22-{strike}-P"
                writer.writerow(("deribit", symbol, us, us, ".01", ".02", "3", "4"))
    # Full-day hourly capture is distinct from a fresh pre-Monday entry book.
    # Four valid latest rows physically arrive at 23:59:58 UTC.
    for asset in (("BTC",) if omit_eth else ("BTC", "ETH")):
        for strike in (2000, 2100):
            us = start + 86_398_000_000
            writer.writerow(("deribit", f"{asset}-03JUN22-{strike}-P",
                             us, us, ".01", ".02", "3", "4"))
    if crossed_last:
        us = start + 86_399_000_000
        writer.writerow(("deribit", "BTC-03JUN22-2000-P", us, us,
                         ".03", ".02", "3", "4"))
    if stale:
        # last row remains stale for one strike, but 24h BTC/ETH coverage stays.
        pass
    return gzip.compress(rows.getvalue().encode())


class SundayEntryTests(unittest.TestCase):
    def check(self, body, expected_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"2022-05-01.csv.gz"
            p.write_bytes(body)
            if expected_error:
                with self.assertRaisesRegex(ValueError, expected_error):
                    analyze_file(p, intents())
            else:
                result = analyze_file(p, intents())
                self.assertTrue(result["independent_original_byte_entry_replay"])
                self.assertTrue(result["source_fixture"])
                self.assertFalse(result["real_original_day_verified"])
                self.assertFalse(result["economic_train_executed"])
                self.assertFalse(result["promotion_authorized"])
                return result

    def test_valid_original_shaped_book_is_fixture_not_certified(self):
        r = self.check(make_day())
        self.assertEqual(r["source_rows"], 100)
        self.assertEqual(r["hourly_qualifying_put_coverage"], {"BTC": 24, "ETH": 24})
        self.assertEqual(r["original_books_by_asset"], {"BTC": 2, "ETH": 2})
        self.assertEqual(r["fixed_original_signal_by_asset"], {
            "BTC": "POSITIVE_EX_ANTE_PREMIUM", "ETH": "POSITIVE_EX_ANTE_PREMIUM"})

    def test_crossed_latest_revokes_one_book(self):
        r = self.check(make_day(crossed_last=True))
        self.assertEqual(r["original_books_by_asset"], {"BTC": 1, "ETH": 2})
        self.assertEqual(r["invalid_last_books_by_asset"]["BTC"], 1)

    def test_missing_hour_rejected(self):
        self.check(make_day(missing_hour=12), "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP")

    def test_missing_eth_rejected(self):
        self.check(make_day(omit_eth=True), "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES")

    def test_wrong_day_rejected(self):
        self.check(make_day(wrong_day=True), "NONCAUSAL_OR_OUT_OF_ORDER_CLOCK")

    def test_missing_fixed_intents_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"2022-05-01.csv.gz"
            p.write_bytes(make_day())
            with self.assertRaisesRegex(ValueError, "UNBOUND_OR_MISSING"):
                analyze_file(p, intents()[:-1])

    def test_no_live_source_fallback_when_http_denied(self):
        class Forbidden(Exception):
            pass
        # The live path requires a real original signal receipt; no fixture
        # can be injected through this entry point.
        with patch("research.tools.v99_r106_i1_public_sunday_entry_probe.bind",
                   side_effect=ValueError("UNTRUSTED_OR_NONORIGINAL_SIGNAL_REPORT")):
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_OR_NONORIGINAL"):
                probe_live(Path("fake_signal.json"))


if __name__ == "__main__":
    unittest.main()
