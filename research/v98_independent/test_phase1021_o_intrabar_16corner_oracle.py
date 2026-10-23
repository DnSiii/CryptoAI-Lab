#!/usr/bin/env python3
"""V98 Phase1021: 16-corner independent long-only O intrabar oracle; synthetic only."""
from __future__ import annotations
import unittest
import numpy as np
from phase876_k_funded_ledger import _intrabar

def direct_all_sixteen(cash, units, low, high):
    """Independent scalar accounting; does not call production _risk/_within."""
    for bits in range(16):
        gross_values = [float(units[j] * (high[j] if (bits >> j) & 1 else low[j]))
                        for j in range(4)]
        gross = sum(gross_values)
        equity = float(cash + gross)
        if not np.isfinite(equity) or equity <= 0:
            return False
        if gross / equity > 1.75 + 1.e-9:
            return False
        if max(gross_values) / equity > .70 + 1.e-9:
            return False
    return True

class OIntrabarCornerOracle(unittest.TestCase):
    def test_3000_seeded_long_only_cash_and_leverage_states(self):
        rng = np.random.default_rng(1021)
        mismatches = []
        survivors = 0
        rejections = 0
        negative_cash = 0
        for i in range(3000):
            opening = rng.uniform(30., 500., 4)
            gross = rng.uniform(.05, 1.75)
            weights = np.minimum(rng.dirichlet(np.ones(4)) * gross, .70)
            units = weights / opening
            cash = float(1. - weights.sum())
            if cash < 0:
                negative_cash += 1
            if i < 150:
                low = opening * rng.uniform(.999, 1., 4)
                high = opening * rng.uniform(1., 1.001, 4)
            else:
                low = opening * rng.uniform(.25, 1., 4)
                high = opening * rng.uniform(1., 2.5, 4)
            shortcut = bool(_intrabar(cash, units, low, high))
            oracle = direct_all_sixteen(cash, units, low, high)
            survivors += int(oracle)
            rejections += int(not oracle)
            if shortcut != oracle:
                mismatches.append((i, shortcut, oracle, cash, weights.tolist()))
        self.assertGreater(survivors, 0)
        self.assertGreater(rejections, 0)
        self.assertGreater(negative_cash, 0)
        self.assertEqual(mismatches, [])

if __name__ == "__main__":
    unittest.main()
