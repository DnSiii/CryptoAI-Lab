"""Source-only causal pair sweep differential tests; no real options or ROI."""
from __future__ import annotations

import random
import unittest
from decimal import Decimal

from research.tools.v99_r106_i1_lifecycle_daily_tape import _has_causal_pair
from research.verification.independent_v99_r106_i1_lifecycle_daily_oracle import (
    _has_causal_pair_independent,
)


def quadratic_reference(records):
    for i, (a, v, strike) in enumerate(records):
        for b, w, other in records[i + 1:]:
            if strike != other and abs(a - b) <= 1_000_000 and abs(v - w) <= 1_000_000:
                return True
    return False


class HeldPairSweepTests(unittest.TestCase):
    def assert_same(self, records, expected=None):
        old = quadratic_reference(records)
        if expected is not None:
            self.assertEqual(old, expected)
        self.assertEqual(_has_causal_pair(records), old)
        self.assertEqual(_has_causal_pair_independent(records), old)

    def test_exact_two_clock_inclusive_boundary(self):
        self.assert_same([(1_000_000, 2_000_000, Decimal(10)),
                          (2_000_000, 3_000_000, Decimal(11))], True)
        self.assert_same([(1_000_000, 2_000_000, Decimal(10)),
                          (2_000_001, 3_000_000, Decimal(11))], False)
        self.assert_same([(1_000_000, 2_000_000, Decimal(10)),
                          (2_000_000, 3_000_001, Decimal(11))], False)

    def test_numeric_strike_aliases_never_pair(self):
        self.assert_same([(1, 1, Decimal('30000')),
                          (1, 1, Decimal('30000.0'))], False)
        self.assert_same([(1, 1, Decimal('30000')),
                          (1, 1, Decimal('30000.0')),
                          (1, 1, Decimal('30001'))], True)

    def test_independent_differential_randomized_small(self):
        randomizer = random.Random(20261031)
        for size in range(0, 46):
            for _ in range(30):
                records = [
                    (randomizer.randrange(0, 5_000_000),
                     randomizer.randrange(0, 5_000_000),
                     Decimal(randomizer.randrange(0, 7)))
                    for _ in range(size)
                ]
                self.assert_same(records)

    def test_6000_distinct_strikes_without_synchronized_venue_clock(self):
        # Same arrival window but every venue event is >1s apart.
        # Quadratic reference intentionally omitted at this scale.
        records = [(2_000_000, i * 2_000_001, Decimal(i + 1))
                   for i in range(6000)]
        self.assertFalse(_has_causal_pair(records))
        self.assertFalse(_has_causal_pair_independent(records))
        # Exact 1s venue skew is eligible, but only for different strikes.
        records[3001] = (2_000_000, 3000 * 2_000_001 + 1_000_000,
                         Decimal(3002))
        self.assertTrue(_has_causal_pair(records))
        self.assertTrue(_has_causal_pair_independent(records))

    def test_6000_same_numeric_strike_without_false_pair(self):
        records = [(i % 3, i % 5, Decimal('30000.0')) for i in range(6000)]
        self.assertFalse(_has_causal_pair(records))
        self.assertFalse(_has_causal_pair_independent(records))


if __name__ == "__main__":
    unittest.main()
