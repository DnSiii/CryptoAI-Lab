"""V98-only adversarial tests for Phase243 native funding source provenance."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from phase243_funding_source_gate import (
    ASSETS, START, TRAIN_START, CUTOFF, audit_all, audit_bytes, millis,
)

UTC = timezone.utc
TEST_START = datetime(2025, 1, 1, tzinfo=UTC)
TEST_CUT = TEST_START + timedelta(days=3)
HEADER = "fundingTime_ms,fundingTime_utc,fundingRate,fundingIntervalHours"


def fixture(*, remove=None, duplicate=None, interval=None, jitter=None,
            mismatch=None, nonfinite=None, reverse=False, future=False,
            prewarmup=False):
    rows = [HEADER]
    if prewarmup:
        t = datetime(2022, 11, 10, 2, tzinfo=UTC)
        rows.append(f"{millis(t)},{t.isoformat()},-0.02000000,2")
    events = []
    for i in range(9):
        t = TEST_START + timedelta(hours=8 * i)
        j = 29 if jitter is None else (jitter if i == 4 else 29)
        ms = millis(t) + j
        iso = (t + timedelta(milliseconds=j)).isoformat()
        if mismatch == i:
            iso = t.isoformat()
        rate = "NaN" if nonfinite == i else ("-0.00080000" if i == 4 else "0.00010000")
        step = 4 if interval == i else 8
        events.append(f"{ms},{iso},{rate},{step}")
    if remove is not None:
        events.pop(remove)
    if duplicate is not None:
        events.insert(duplicate, events[duplicate])
    if reverse:
        events.reverse()
    rows.extend(events)
    if future:
        t = CUTOFF
        rows.append(f"{millis(t)},{t.isoformat()},0.0001,8")
    return ("\n".join(rows) + "\n").encode()


def check(raw):
    return audit_bytes(raw, "SOLUSDT", start=TEST_START, cut=TEST_CUT,
                       train_start=TEST_START)


class FundingGateTests(unittest.TestCase):
    def test_synthetic_pass_and_training_tail_count(self):
        result = check(fixture())
        self.assertEqual(result["selected_events"], 9)
        self.assertEqual(result["training_abs_gt_7bp"], 1)
        self.assertEqual(result["max_jitter_ms"], 29)
        self.assertEqual(result["jittered_events"], 9)

    def test_identical_bytes_identical_manifest(self):
        self.assertEqual(check(fixture()), check(fixture()))

    def test_2022_november_variable_interval_excluded(self):
        result = check(fixture(prewarmup=True))
        self.assertEqual(result["selected_events"], 9)
        self.assertEqual(result["training_abs_gt_7bp"], 1)

    def test_missing_settlement_rejected(self):
        with self.assertRaisesRegex(ValueError, "off-slot|incomplete"):
            check(fixture(remove=3))

    def test_duplicate_settlement_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate|off-slot"):
            check(fixture(duplicate=3))

    def test_interval_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "variable-interval"):
            check(fixture(interval=4))

    def test_jitter_over_50ms_rejected(self):
        with self.assertRaisesRegex(ValueError, "off-slot"):
            check(fixture(jitter=51))

    def test_timestamp_ms_utc_disagreement_rejected(self):
        with self.assertRaisesRegex(ValueError, "timestamp mismatch"):
            check(fixture(mismatch=4))

    def test_nonfinite_rate_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            check(fixture(nonfinite=4))

    def test_out_of_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonmonotone"):
            check(fixture(reverse=True))

    def test_future_holdout_row_rejected(self):
        with self.assertRaisesRegex(ValueError, "holdout"):
            check(fixture(future=True))

    def test_2026_cutoff_request_rejected(self):
        with self.assertRaisesRegex(ValueError, "holdout"):
            audit_bytes(fixture(), "SOLUSDT", start=TEST_START,
                        cut=CUTOFF + timedelta(hours=8), train_start=TEST_START)

    def test_unexpected_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError, "symbol"):
            audit_bytes(fixture(), "DOGEUSDT", start=TEST_START,
                        cut=TEST_CUT, train_start=TEST_START)

    def test_malformed_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "schema"):
            check(fixture().replace(b"fundingIntervalHours", b"interval"))

    def test_real_training_source_all_five_assets(self):
        root = Path(__file__).resolve().parent / "data" / "phase206_funding"
        result = audit_all(root)
        self.assertEqual(set(result["assets"]), set(ASSETS))
        for symbol in ASSETS:
            row = result["assets"][symbol]
            self.assertEqual(row["selected_events"], 3381)
            self.assertEqual(row["warmup_events"], 93)
            self.assertEqual(row["training_events"], 3288)
            self.assertLessEqual(row["max_jitter_ms"], 50)
        self.assertFalse(result["holdout_accessed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
