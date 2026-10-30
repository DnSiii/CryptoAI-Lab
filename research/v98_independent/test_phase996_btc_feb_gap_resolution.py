"""V98 Phase996 deterministic synthetic source-gap regression; no network/PnL."""
import copy
import csv
import hashlib
import io
import unittest
from phase996_btc_feb_gap_resolution import TIMES, GAP, reconcile


def row(t):
    # Canonical 12-column Binance mark candle shape; entirely synthetic prices.
    return [str(t), "100.00", "101.00", "99.00", "100.50", "0",
            str(t + 3599999), "0", "0", "0", "0", "0"]


def fixture():
    all_rows = [row(t) for t in TIMES]
    monthly = [r[:] for r in all_rows if int(r[0]) not in GAP]
    daily = {day: [r[:] for r in all_rows[(day-1)*24:day*24]]
             for day in range(1, 29)}
    return monthly, daily


class Phase996Tests(unittest.TestCase):
    def test_exact_24_hour_hole_passes(self):
        monthly, daily = fixture()
        rows, audit = reconcile(monthly, daily)
        self.assertEqual(len(rows), 672)
        self.assertEqual(audit["shared"], 648)
        self.assertEqual(audit["missing_left"], 24)
        self.assertEqual(audit["different_rows"], 0)
        self.assertEqual(rows[551], monthly[551])
        self.assertEqual(rows[552], daily[24][0])

    def test_repeatable_output_hash(self):
        monthly, daily = fixture()
        first, _ = reconcile(monthly, daily)
        second, _ = reconcile(monthly, daily)
        def digest(rows):
            stream = io.StringIO(newline="")
            csv.writer(stream, lineterminator="\n").writerows(rows)
            return hashlib.sha256(stream.getvalue().encode()).hexdigest()
        self.assertEqual(digest(first), digest(second))

    def test_monthly_other_hole_rejected(self):
        monthly, daily = fixture()
        monthly.pop(2)
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)

    def test_monthly_overlap_price_mismatch_rejected(self):
        monthly, daily = fixture()
        daily[1][0][4] = "100.60"
        with self.assertRaisesRegex(ValueError, "OVERLAP_CONFLICT"):
            reconcile(monthly, daily)

    def test_daily_duplicate_rejected(self):
        monthly, daily = fixture()
        daily[24][1] = daily[24][0][:]
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)

    def test_daily_incomplete_rejected(self):
        monthly, daily = fixture()
        daily[24].pop()
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)

    def test_extra_day_rejected(self):
        monthly, daily = fixture()
        daily[29] = []
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)

    def test_monthly_ohlc_geometry_rejected(self):
        monthly, daily = fixture()
        monthly[0][2] = "90"
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)

    def test_nonfinite_daily_rejected(self):
        monthly, daily = fixture()
        daily[24][0][4] = "NaN"
        with self.assertRaises(ValueError):
            reconcile(monthly, daily)


if __name__ == "__main__":
    unittest.main()
