"""Adversarial fixtures for preregistered second Sunday, NEVER original evidence."""
from __future__ import annotations

import csv
import gzip
import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_second_sunday_probe import (
    SUNDAY, DECISION_MS, analyze, live)
from research.tools.v99_r106_i1_train_numeric_gate import _fold


def intents():
    return [
        {"decision_ms": int(d.timestamp()*1000), "asset": a,
         "fold": _fold(int(d.timestamp()*1000)),
         "signal": ("POSITIVE_EX_ANTE_PREMIUM"
                    if int(d.timestamp()*1000) == DECISION_MS else "NO_PREMIUM")}
        for d in eligible(True) for a in ("BTC", "ETH")
    ]


def fake_day(*, missing_hour=None, omit_eth=False, crossed_last=False,
             wrong_day=False):
    out = io.StringIO(newline="")
    w = csv.writer(out)
    w.writerow(("exchange", "symbol", "timestamp", "local_timestamp",
                "bid_price", "ask_price", "bid_amount", "ask_amount"))
    base = int(datetime(SUNDAY.year, SUNDAY.month, SUNDAY.day,
                        tzinfo=timezone.utc).timestamp() * 1_000_000)
    if wrong_day:
        base += 86_400_000_000
    for hour in range(24):
        if hour == missing_hour:
            continue
        for asset in (("BTC",) if omit_eth else ("BTC", "ETH")):
            for strike in (2000, 2100):
                us = base + hour*3_600_000_000 + 10_000_000
                w.writerow(("deribit", f"{asset}-03FEB23-{strike}-P",
                            us, us, ".01", ".02", "3", "4"))
    for asset in (("BTC",) if omit_eth else ("BTC", "ETH")):
        for strike in (2000, 2100):
            us = base + 86_398_000_000
            w.writerow(("deribit", f"{asset}-03FEB23-{strike}-P",
                        us, us, ".01", ".02", "3", "4"))
    if crossed_last:
        us = base + 86_399_000_000
        w.writerow(("deribit", "BTC-03FEB23-2000-P",
                    us, us, ".03", ".02", "3", "4"))
    return gzip.compress(out.getvalue().encode())


class SecondSundayTests(unittest.TestCase):
    def check(self, body, failure=None, original_intents=None):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"sample.csv.gz"
            p.write_bytes(body)
            if failure:
                with self.assertRaisesRegex(ValueError, failure):
                    analyze(p, intents() if original_intents is None else original_intents)
            else:
                return analyze(p, intents() if original_intents is None else original_intents)

    def test_positive_fixture_never_certifies_economics(self):
        r = self.check(fake_day())
        self.assertEqual(r["original_books_by_asset"], {"BTC":2, "ETH":2})
        self.assertEqual(r["hourly_qualifying_put_coverage"], {"BTC":24, "ETH":24})
        self.assertTrue(r["independent_original_byte_reexecution"])
        self.assertFalse(r["real_original_day_verified"])
        self.assertFalse(r["economic_train_executed"])
        self.assertFalse(r["promotion_authorized"])

    def test_crossed_last_revokes_contract(self):
        r = self.check(fake_day(crossed_last=True))
        self.assertEqual(r["original_books_by_asset"], {"BTC":1, "ETH":2})
        self.assertEqual(r["invalid_last_books_by_asset"]["BTC"], 1)

    def test_missing_hour_fails_closed(self):
        self.check(fake_day(missing_hour=11), "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP")

    def test_missing_eth_fails_closed(self):
        self.check(fake_day(omit_eth=True), "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES")

    def test_wrong_day_fails_closed(self):
        self.check(fake_day(wrong_day=True), "NONCAUSAL_OR_OUT_OF_ORDER_CLOCK")

    def test_missing_original_intent_fails_closed(self):
        self.check(fake_day(), "SECOND_SUNDAY_ORIGINAL_SIGNAL_GRID_INVALID",
                   original_intents=intents()[:-1])

    def test_no_fake_live_receipt(self):
        with patch("research.tools.v99_r106_i1_second_sunday_probe.bind",
                   side_effect=ValueError("UNTRUSTED_OR_NONORIGINAL_SIGNAL_REPORT")):
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_OR_NONORIGINAL"):
                live(Path("fake.json"))


if __name__ == "__main__":
    unittest.main()
