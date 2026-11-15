"""Regression test: C8 daily sleeve decisions use the completed t-1 close."""
import unittest
from .v98_composed_c8 import composed_c8_sleeves
from .phase243_native_funding_cashflow import ASSETS

class C8DecisionClockTest(unittest.TestCase):
    def test_replay_fills_only_after_completed_daily_close(self):
        # End-to-end execution clock: an eligible signal at 2183 close
        # cannot fill before open 2184, including the intraday policy.
        from .v98_b0_next_open_execution import replay_next_open
        from .v98_c8_daily_risk_execution import replay_c8_daily_risk
        n = 2186
        bars = {a: [(100.0 * (1.0002 ** i), 0., 0.,
                     100.0 * (1.0002 ** (i + 1))) for i in range(n)]
                for a in ASSETS}
        funding = {a: {} for a in ASSETS}
        for executor in (replay_next_open, replay_c8_daily_risk):
            _, ledger = executor(bars, funding, composed_c8_sleeves())
            fills = [e["index"] for e in ledger if e["turnover"] > 1e-12]
            self.assertTrue(fills, executor.__name__)
            self.assertEqual(fills[0], 2184, executor.__name__)
            self.assertTrue(all(i >= 2184 for i in fills), executor.__name__)

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
