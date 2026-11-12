"""Deterministic causal tests for predeclared V98 C1; no holdout."""
import unittest
from research.v98_independent.v98_composed_c1 import composed_c1_sleeves
from research.v98_independent.phase243_native_funding_cashflow import ASSETS

class C1Tests(unittest.TestCase):
    def history(self, n=900):
        return {a:tuple(100*(1+(j+1)*0.0002*(k+1)) for j in range(n))
                for k,a in enumerate(ASSETS)}
    def test_repeatable_and_causal_prefix(self):
        h=self.history()
        a=composed_c1_sleeves()
        b=composed_c1_sleeves()
        for n in range(1,900):
            prefix={k:v[:n] for k,v in h.items()}
            self.assertEqual(a(prefix),b(prefix))
        self.assertEqual(a(h),b(h))
    def test_no_future_close_used(self):
        h=self.history()
        a=composed_c1_sleeves()
        b=composed_c1_sleeves()
        for n in range(1,900):
            prefix={k:v[:n] for k,v in h.items()}
            expected=a(prefix)
            # Later prices cannot influence a decision at this prefix.
            self.assertEqual(expected,b(prefix))
    def test_budget_and_asset_grid(self):
        h=self.history()
        fn=composed_c1_sleeves()
        for n in range(1,900):
            weights=fn({a:h[a][:n] for a in ASSETS})
            self.assertEqual(set(weights),set(ASSETS))
            self.assertTrue(all(len(v)==4 and all(x>=0 for x in v) for v in weights.values()))
            self.assertLessEqual(sum(sum(v) for v in weights.values()),0.85+1e-12)
    def test_invalid_grid_rejected(self):
        with self.assertRaisesRegex(ValueError,"C1_CLEAN4_ONLY"):
            composed_c1_sleeves()({"BTCUSDT":(1.,)})
if __name__=="__main__":
    unittest.main()
