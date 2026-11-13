"""Deterministic causal tests for preregistered V98 C3 sleeves."""
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c3 import composed_c3_sleeves, LOOKBACK, STEP

class TestC3(unittest.TestCase):
    def test_no_early_allocation_and_cash_bound(self):
        fn = composed_c3_sleeves()
        history = {a: tuple(100. + i * 0.01 for i in range(LOOKBACK)) for a in ASSETS}
        self.assertTrue(all(sum(v) == 0 for v in fn(history).values()))
        history = {a: tuple(100. + i * 0.01 for i in range(LOOKBACK + STEP + 1)) for a in ASSETS}
        result = fn(history)
        self.assertEqual(set(result), set(ASSETS))
        self.assertLessEqual(sum(sum(v) for v in result.values()), .75 + 1e-12)
        self.assertTrue(all(len(v) == 4 and all(x >= 0 for x in v) for v in result.values()))

    def test_prefix_invariance(self):
        n = LOOKBACK + STEP * 2 + 1
        hist = {a: tuple(100. + j * .01 * (k + 1) for j in range(n)) for k, a in enumerate(ASSETS)}
        fn1 = composed_c3_sleeves()
        fn2 = composed_c3_sleeves()
        prefix = {a: hist[a][:LOOKBACK + STEP + 1] for a in ASSETS}
        result = fn1(prefix)
        self.assertEqual(result, fn2(prefix))
        self.assertEqual(result, fn2({a: hist[a][:LOOKBACK + STEP + 2] for a in ASSETS}))

    def test_reject_misalignment(self):
        fn = composed_c3_sleeves()
        hist = {a: (100.,) * 1345 for a in ASSETS}
        hist[ASSETS[0]] = (100.,) * 1344
        with self.assertRaisesRegex(ValueError, "C3_MISALIGNED"):
            fn(hist)

if __name__ == "__main__":
    unittest.main()
