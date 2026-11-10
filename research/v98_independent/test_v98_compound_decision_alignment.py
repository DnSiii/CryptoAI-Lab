"""V98-only regression: every replay order must be generated at exactly t-1."""
import unittest

from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_compound_scenario_replay import replay

START = 1669852800000


class DecisionAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.bars = {a: [(100., 101., 99., 100.)] for a in ASSETS}
        self.funding = {a: {} for a in ASSETS}
        self.weights = {a: 0. for a in ASSETS}

    def run_decision(self, decision_time):
        return replay(
            [{"hour_open_ms": START, "decision_time_ms": decision_time,
              "weights": self.weights}],
            self.bars, self.funding, first_hour_ms=START,
            initial_equity_usd=10000., fee_bps=4., slippage_bps=2.,
            multipliers=(1., 2., 4.))

    def test_exact_previous_hour_is_accepted(self):
        result = self.run_decision(START-HOUR_MS)
        self.assertEqual(set(result), {"1.0", "2.0", "4.0"})
        self.assertEqual(result["1.0"][0]["ending_equity_usd"], 10000.)

    def test_stale_decision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "NONCAUSAL_OR_MISSING_DECISION"):
            self.run_decision(START-2*HOUR_MS)

    def test_same_hour_decision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "NONCAUSAL_OR_MISSING_DECISION"):
            self.run_decision(START)


if __name__ == "__main__":
    unittest.main()
