"""V98 funding coverage gate tests, isolated from system PnL."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v98_native_funding_inventory_coverage_gate import audit, START, HOUR, ASSETS

class CoverageTests(unittest.TestCase):
    def panel(self):
        return [{"asset": a, "hour_open_ms": START + i*HOUR}
                for a in ASSETS for i in range(2)]
    def funding(self):
        return {a: {START: 0.0001} for a in ASSETS}
    def test_complete_panel(self):
        r = audit(self.panel(), self.funding(), START, START+2*HOUR)
        self.assertEqual(r["position_hours"], 8)
        self.assertEqual(r["native_events"], 4)
    def test_missing_zero_position_fails(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_POSITION_PANEL"):
            audit(self.panel()[:-1], self.funding(), START, START+2*HOUR)
    def test_duplicate_fails(self):
        p=self.panel()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_POSITION_HOUR"):
            audit(p+[p[0]], self.funding(), START, START+2*HOUR)
    def test_future_data_fails(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRAINING_WINDOW"):
            audit(self.panel(), self.funding(), START, 1767225600000+HOUR)
    def test_missing_asset_fails(self):
        f=self.funding()
        del f["BTCUSDT"]
        with self.assertRaisesRegex(ValueError, "MISSING_FUNDING_ASSET"):
            audit(self.panel(), f, START, START+2*HOUR)
if __name__ == "__main__":
    unittest.main()
