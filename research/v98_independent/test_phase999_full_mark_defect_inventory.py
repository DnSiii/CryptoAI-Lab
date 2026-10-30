"""V98 Phase999 no-network source-inventory tests."""
import unittest
from phase999_full_mark_defect_inventory import analyze
from phase991_source_triangulation import TIMES
from test_phase996_btc_feb_gap_resolution import fixture


class InventoryTests(unittest.TestCase):
    def test_known_24_hour_gap(self):
        monthly, _ = fixture()
        out = analyze(monthly, TIMES)
        self.assertEqual(out["rows"], 648)
        self.assertEqual(out["missing_hours"], 24)
        self.assertEqual(out["missing_utc"][0], "2023-02-24T00:00:00+00:00")
        self.assertEqual(out["missing_utc"][-1], "2023-02-24T23:00:00+00:00")

    def test_full_month_no_gaps(self):
        _, daily = fixture()
        rows = [r for d in range(1,29) for r in daily[d]]
        out = analyze(rows, TIMES)
        self.assertEqual(out["missing_hours"], 0)
        self.assertEqual(out["duplicate_count"], 0)
        self.assertEqual(out["malformed_count"], 0)

    def test_duplicate_and_geometry_detected(self):
        _, daily = fixture()
        rows = [r for d in range(1,29) for r in daily[d]]
        rows[0][2] = "80"
        rows[1] = rows[0][:]
        out = analyze(rows, TIMES)
        self.assertEqual(out["duplicate_count"], 1)
        self.assertEqual(out["missing_hours"], 1)
        self.assertGreater(out["malformed_count"], 0)


if __name__ == "__main__":
    unittest.main()
