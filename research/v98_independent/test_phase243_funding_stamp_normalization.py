"""V98-only regression: native settlement timestamps must not be shifted arbitrarily."""
import csv
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.phase243_native_funding_cashflow import load_funding, HOUR_MS

class FundingTimestampTests(unittest.TestCase):
    def read(self, stamps):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "BTCUSDT_native_funding.csv"
            with p.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["funding_time_ms", "funding_rate"])
                w.writeheader()
                for t in stamps:
                    w.writerow({"funding_time_ms": t, "funding_rate": "0.0001"})
            return load_funding(p)

    def test_exact_one_millisecond_exchange_stamp(self):
        start = 1669852800000
        self.assertEqual(self.read([start + 1, start + 8*HOUR_MS + 1]),
                         {start: 0.0001, start + 8*HOUR_MS: 0.0001})

    def test_exact_hour_is_unchanged(self):
        start = 1669852800000
        self.assertEqual(self.read([start]), {start: 0.0001})

    def test_other_offsets_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "non_hour_boundary"):
            self.read([1669852800002])

    def test_normalization_collision_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate_normalized_settlement"):
            self.read([1669852800000, 1669852800001])

if __name__ == "__main__":
    unittest.main()
