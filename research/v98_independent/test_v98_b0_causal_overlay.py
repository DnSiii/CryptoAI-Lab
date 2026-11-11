import math
import unittest
from research.v98_independent.v98_b0_causal_overlay import (
    WINDOW, REFERENCE_WINDOWS, regime_multiplier, governor_multiplier, compose_weights)

class B0CausalOverlayTests(unittest.TestCase):
    def test_insufficient_history_fails_closed(self):
        self.assertEqual(regime_multiplier([100.0] * 100), 0.0)

    def test_high_relative_volatility_triggers(self):
        rates = [0.001 * (-1)**i for i in range(REFERENCE_WINDOWS * WINDOW)]
        rates += [0.01 * (-1)**i for i in range(WINDOW)]
        prices = [100.0]
        for r in rates:
            prices.append(prices[-1] * math.exp(r))
        self.assertEqual(regime_multiplier(prices), 0.5)

    def test_low_relative_volatility(self):
        prices = [100.0]
        for i in range((REFERENCE_WINDOWS+1)*WINDOW):
            prices.append(prices[-1]*math.exp(0.001*(-1)**i))
        self.assertEqual(regime_multiplier(prices), 1.0)

    def test_governor_boundaries(self):
        self.assertEqual(governor_multiplier(90,100),1.0)
        self.assertEqual(governor_multiplier(80,100),0.5)
        self.assertEqual(governor_multiplier(79,100),0.25)

    def test_budget(self):
        weights=compose_weights({"BTC":(0.4,0.15,0.15,0.1),"ETH":(0.4,0.15,0.15,0.1)},{"BTC":1,"ETH":1},1)
        self.assertLessEqual(sum(weights.values()),0.75+1e-12)
        self.assertTrue(all(x<=0.4 for x in weights.values()))

if __name__ == "__main__":
    unittest.main()
