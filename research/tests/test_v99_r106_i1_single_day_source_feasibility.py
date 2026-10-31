"""Offline-only adversarial controls: no paid source, no PnL, no orders."""
from __future__ import annotations

import csv
import gzip
import hashlib
import random
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_single_day_source_feasibility import inspect, _pair_counts
from research.verification.independent_v99_r106_i1_single_day_source import _synchronized_pairs

DAY = datetime(2022, 1, 23, tzinfo=timezone.utc)
FIELDS = ("exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount")
BTC1 = "BTC-25FEB22-30000-P"
BTC2 = "BTC-25FEB22-28000-P"
ETH1 = "ETH-25FEB22-2000-P"
ETH2 = "ETH-25FEB22-1800-P"


def row(symbol, hour, minute=0, second=2, *, bid="0.05", ask="0.052"):
    t = int(DAY.replace(hour=hour, minute=minute, second=second).timestamp() * 1_000_000)
    return dict(exchange="deribit", symbol=symbol, timestamp=str(t-1000),
                local_timestamp=str(t), bid_price=bid, ask_price=ask,
                bid_amount="2", ask_amount="2")


def source(*, bad_last=False, skew=False, missing_eth_hour=None, stale=False):
    rows = []
    for hour in range(24):
        rows.append(row(BTC1, hour))
        if hour != missing_eth_hour:
            rows.append(row(ETH1, hour))
    # These two-strike books are ex-ante, 28-35d, and fresh at Monday 00:00.
    if stale:
        minute, second = 50, 0
    else:
        minute, second = 59, 58
    rows.extend([row(BTC1, 23, minute, second),
                 row(BTC2, 23, minute, second - 3 if skew else second),
                 row(ETH1, 23, 59, 58), row(ETH2, 23, 59, 58)])
    if bad_last:
        rows.append(row(BTC1, 23, 59, 59, bid="0"))
    rows.sort(key=lambda r: int(r["local_timestamp"]))
    return rows


class OneDaySourceFeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "2022-01-23.csv.gz"
        self.license = Path(self.tmp.name) / "license.txt"
        self.license.write_text("SYNTHETIC TEST PLACEHOLDER; NOT A REAL LICENSE")

    def write(self, rows):
        with gzip.open(self.path, "wt", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_indexed_counters_match_bruteforce_on_boundary_and_duplicate_strikes(self):
        rng = random.Random(20261031)
        books = {"BTC": [], "ETH": []}
        for asset in ("BTC", "ETH"):
            for expiry in (1000, 2000, 3000):
                rows = []
                for i in range(170):
                    # Decimal-identical strikes may have distinct string forms.
                    k = rng.randrange(60)
                    strike = str(k) if i % 2 else str(k) + ".0"
                    rows.append({
                        "expiry_ms": expiry, "strike_usd": strike,
                        "arrival_us": rng.randrange(0, 3_000_001),
                        "venue_us": rng.randrange(0, 3_000_001),
                    })
                # Exact inclusive 1-second boundaries in both clock axes.
                rows.extend([
                    {"expiry_ms": expiry, "strike_usd": "900",
                     "arrival_us": 5_000_000, "venue_us": 5_000_000},
                    {"expiry_ms": expiry, "strike_usd": "901",
                     "arrival_us": 6_000_000, "venue_us": 6_000_000},
                    {"expiry_ms": expiry, "strike_usd": "902",
                     "arrival_us": 6_000_001, "venue_us": 6_000_001},
                ])
                rng.shuffle(rows)
                books[asset].extend(rows)
        expected = {}
        for asset in ("BTC", "ETH"):
            total = 0
            for expiry in (1000, 2000, 3000):
                rows = [r for r in books[asset] if r["expiry_ms"] == expiry]
                brute = sum(
                    Decimal(a["strike_usd"]) != Decimal(b["strike_usd"])
                    and abs(a["arrival_us"] - b["arrival_us"]) <= 1_000_000
                    and abs(a["venue_us"] - b["venue_us"]) <= 1_000_000
                    for i, a in enumerate(rows) for b in rows[i+1:]
                )
                independent = _synchronized_pairs([
                    (Decimal(r["strike_usd"]), r["venue_us"], r["arrival_us"])
                    for r in rows
                ])
                self.assertEqual(independent, brute)
                total += brute
            expected[asset] = total
        self.assertEqual(_pair_counts(books), expected)

    def test_6000_dense_original_strikes_count_without_quadratic_enumeration(self):
        n = 6000
        rows = [{"expiry_ms": 1000, "strike_usd": str(i),
                 "arrival_us": 10_000_000, "venue_us": 10_000_000}
                for i in range(n)]
        expected = n * (n - 1) // 2
        self.assertEqual(_pair_counts({"BTC": rows, "ETH": []}),
                         {"BTC": expected, "ETH": 0})
        self.assertEqual(_synchronized_pairs([
            (Decimal(r["strike_usd"]), r["venue_us"], r["arrival_us"])
            for r in rows
        ]), expected)

    def test_fixed_day_two_assets_independent_source_only(self):
        digest = self.write(source())
        result = inspect(self.path, fixture=True, expected_sha256=digest)
        self.assertEqual(result["status"], "SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS")
        self.assertEqual(result["fresh_synchronized_two_strike_pairs_by_asset"],
                         {"BTC": 1, "ETH": 1})
        self.assertEqual(result["source_hour_coverage"], {"BTC": 24, "ETH": 24})
        self.assertTrue(result["independent_original_byte_replay_passed"])
        self.assertTrue(result["external_sha256_matched"])
        self.assertEqual(result["certified_lifecycles"], 0)
        self.assertFalse(result["economic_train_executed"])
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["orders_enabled"])

    def test_last_invalid_quote_revokes_earlier_good_book(self):
        self.write(source(bad_last=True))
        report = inspect(self.path, fixture=True)
        self.assertEqual(report["fresh_synchronized_two_strike_pairs_by_asset"],
                         {"BTC": 0, "ETH": 1})
        self.assertEqual(report["latest_invalid_books_by_asset"]["BTC"], 1)

    def test_unsynchronized_or_stale_pair_not_executable(self):
        for kwargs in ({"skew": True}, {"stale": True}):
            with self.subTest(kwargs=kwargs):
                self.write(source(**kwargs))
                result = inspect(self.path, fixture=True)
                self.assertEqual(result["fresh_synchronized_two_strike_pairs_by_asset"]["BTC"], 0)
                self.assertEqual(result["fresh_synchronized_two_strike_pairs_by_asset"]["ETH"], 1)

    def test_missing_hour_fails_before_source_claim(self):
        self.write(source(missing_eth_hour=11))
        with self.assertRaisesRegex(ValueError, "HOURLY_CAPTURE_GAP"):
            inspect(self.path, fixture=True)

    def test_external_sha_mismatch_fails_closed(self):
        self.write(source())
        with self.assertRaisesRegex(ValueError, "EXTERNAL_SOURCE_SHA256_MISMATCH"):
            inspect(self.path, fixture=True, expected_sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "INVALID_EXTERNAL_SOURCE_SHA256"):
            inspect(self.path, fixture=True, expected_sha256="not-a-sha")

    def test_license_required_for_nonfixture_but_not_legally_certified(self):
        self.write(source())
        with self.assertRaisesRegex(ValueError, "LICENSE_EVIDENCE_REQUIRED"):
            inspect(self.path)
        result = inspect(self.path, license_evidence=self.license)
        self.assertFalse(result["written_license_legally_verified"])
        self.assertFalse(result["vendor_completeness_attested"])

    def test_only_preselected_day_and_missing_source(self):
        missing = inspect(self.path, fixture=True)
        self.assertEqual(missing["status"], "SOURCE_MISSING")
        self.assertFalse(missing["promotion_authorized"])
        with self.assertRaisesRegex(ValueError, "ONLY_PREREGISTERED_SOURCE_DAY"):
            inspect(Path(self.tmp.name) / "2022-06-15.csv.gz", fixture=True)

    def test_independent_oracle_disagreement_vetoes(self):
        self.write(source())
        fake = {"sha256": "0"*64, "rows": 48,
                "coverage_hours_by_asset": {"BTC": 24, "ETH": 24},
                "pairs_by_asset": {"BTC": 1, "ETH": 1}}
        with patch("research.tools.v99_r106_i1_single_day_source_feasibility.replay",
                   return_value=fake):
            with self.assertRaisesRegex(ValueError, "INDEPENDENT_ORIGINAL_DAY_REPLAY_DISAGREEMENT"):
                inspect(self.path, fixture=True)


if __name__ == "__main__":
    unittest.main()
