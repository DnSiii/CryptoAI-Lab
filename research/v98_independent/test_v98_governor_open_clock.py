"""Guard against same-open equity lookahead in V98 governor decisions."""
import unittest
from unittest.mock import patch
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_next_open_execution import replay_next_open
from .v98_c8_daily_risk_execution import replay_c8_daily_risk

class GovernorOpenClockTest(unittest.TestCase):
    def test_governor_receives_prior_mark_not_current_open(self):
        n = 4
        bars = {a: [(100., 0., 0., 100.) for _ in range(n)] for a in ASSETS}
        # An opening gap at i=2 must not influence the governor argument
        # used for a fill at that same opening.
        bars[ASSETS[0]][2] = (150., 0., 0., 150.)
        funding = {a: {} for a in ASSETS}
        def sleeve(_):
            return {"growth": [0.1]*len(ASSETS)}
        for executor in (replay_next_open, replay_c8_daily_risk):
            observed = []
            def governor(equity, peak):
                observed.append((equity, peak))
                return 1.
            with patch.object(__import__(executor.__module__, fromlist=["governor_multiplier"]),
                              "governor_multiplier", side_effect=governor):
                executor(bars, funding, sleeve)
            self.assertEqual(len(observed), n)
            # No position at i=1 prior to decision; i=2 prior mark is
            # the i=1 fill equity, not the gapped i=2 open equity.
            self.assertLess(observed[2][0], 10000.)
            self.assertAlmostEqual(observed[2][0], observed[1][0] * (1-0.4*0.0006))
if __name__ == "__main__":
    unittest.main()
