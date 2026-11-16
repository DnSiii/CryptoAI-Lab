"""V98 Independent causal cashflow regression; synthetic data only.

Funding at opening i belongs to exposure carried across that boundary,
not to the newly filled position. This test must never access holdout data.
"""
import unittest
from unittest.mock import patch

from .v98_b0_stream_integration import ASSETS
from .v98_b0_next_open_execution import replay_next_open
from .v98_c8_daily_risk_execution import replay_c8_daily_risk


class NativeFundingBoundaryTest(unittest.TestCase):
    def test_funding_charged_to_previous_position_before_fill(self):
        bars = {a: [(100., 100., 100., 100.) for _ in range(4)]
                for a in ASSETS}
        funding = {a: {} for a in ASSETS}
        first = ASSETS[0]
        funding[first][2] = 0.01
        calls = [0]

        def sleeve(_):
            calls[0] += 1
            # Open 1: establish a position. Open 2: exit it.
            allocation = 0.4 if calls[0] == 1 else 0.
            return {a: (allocation if a == first else 0., 0., 0., 0.)
                    for a in ASSETS}

        for executor in (replay_next_open, replay_c8_daily_risk):
            calls[0] = 0
            with patch.object(__import__(executor.__module__, fromlist=['regime_multiplier']),
                              'regime_multiplier', return_value=1.):
                summary, ledger = executor(bars, funding, sleeve,
                                           fee_rate=0., slippage_rate=0.)
            self.assertAlmostEqual(ledger[0]['weights_after_fill'][first], 0.4)
            self.assertAlmostEqual(ledger[1]['funding_by_asset'][first], -0.004)
            self.assertAlmostEqual(ledger[1]['funding_return'], -0.004)
            self.assertAlmostEqual(summary['final_equity'], 9960.)
            self.assertAlmostEqual(ledger[1]['weights_after_fill'][first], 0.)


if __name__ == '__main__':
    unittest.main()
