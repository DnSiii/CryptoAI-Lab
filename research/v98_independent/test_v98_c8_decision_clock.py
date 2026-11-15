"""Regression test: C8 daily sleeve decisions use the completed t-1 close."""
import unittest
from .v98_composed_c8 import composed_c8_sleeves
from .phase243_native_funding_cashflow import ASSETS

class C8DecisionClockTest(unittest.TestCase):
    def test_first_decision_only_after_complete_daily_bar(self):
        sleeve = composed_c8_sleeves()
        prices = {a: tuple(100.0 * (1.0002 ** i) for i in range(2184)) for a in ASSETS}
        def snapshot(n):
            return sleeve({a: prices[a][:n] for a in ASSETS})
        self.assertTrue(all(sum(v) == 0 for v in snapshot(2161).values()))
        self.assertTrue(all(sum(v) == 0 for v in snapshot(2183).values()))
        self.assertTrue(any(sum(v) > 0 for v in snapshot(2184).values()))
        self.assertEqual(snapshot(2184), snapshot(2184))

if __name__ == "__main__":
    unittest.main()
