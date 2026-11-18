"""Deterministic no-market-data invariants for C13. Not an economic gate."""
import math
import unittest
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_composed_c13 import (
    WARMUP, REBALANCE, composed_c13_sleeves, c13_router, c13_allocator,
)

class C13Invariants(unittest.TestCase):
    def make_history(self, length, slope):
        return {a: [100.0*math.exp(slope*i) for i in range(length)]
                for a in ASSETS}

    def test_clean4_fail_closed(self):
        h = self.make_history(WARMUP+1, 0.0001)
        del h[next(iter(ASSETS))]
        with self.assertRaisesRegex(ValueError, "C13_CLEAN4_ONLY"):
            composed_c13_sleeves()(h)

    def test_invalid_prices_fail_closed(self):
        h = self.make_history(WARMUP+1, 0.0001)
        h[next(iter(ASSETS))][-1] = float("nan")
        with self.assertRaisesRegex(ValueError, "C13_INVALID_CLOSE"):
            composed_c13_sleeves()(h)

    def test_flat_market_zero(self):
        h = self.make_history(WARMUP+1, 0)
        s = composed_c13_sleeves()(h)
        self.assertTrue(all(all(v == 0 for v in s[a]) for a in ASSETS))

    def test_trend_gross_and_asset_caps(self):
        h = self.make_history(WARMUP+1, 0.0002)
        s = composed_c13_sleeves()(h)
        r = {a: c13_router(h[a]) for a in ASSETS}
        w = c13_allocator(s, r, 1.0)
        self.assertLessEqual(sum(w.values()), .76+1e-12)
        self.assertTrue(all(0 <= v <= .38+1e-12 for v in w.values()))

    def test_governor_monotonic(self):
        h = self.make_history(WARMUP+1, 0.0002)
        s = composed_c13_sleeves()(h)
        r = {a: c13_router(h[a]) for a in ASSETS}
        hi = c13_allocator(s, r, 1.0)
        lo = c13_allocator(s, r, .25)
        self.assertTrue(all(lo[a] <= hi[a]+1e-12 for a in ASSETS))

    def test_rebalance_determinism(self):
        h = self.make_history(WARMUP+REBALANCE+1, 0.0002)
        engine = composed_c13_sleeves()
        a = engine({k:v[:WARMUP+1] for k,v in h.items()})
        b = engine({k:v[:WARMUP+2] for k,v in h.items()})
        self.assertEqual(a,b)

if __name__ == "__main__":
    unittest.main()
