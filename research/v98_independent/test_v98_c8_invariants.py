"""Deterministic C8 transition and causal invariance tests (synthetic only)."""
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c8 import composed_c8_sleeves, LONG, MID, STEP

class C8Transitions(unittest.TestCase):
    def test_clean4_only(self):
        with self.assertRaisesRegex(ValueError, "C8_CLEAN4_ONLY"):
            composed_c8_sleeves()({"BTCUSDT":[100.]})

    def test_no_future_lookahead(self):
        # Any update before the next 24h decision boundary must preserve prior weights.
        n=LONG+STEP+2
        bars={a:[100.*(1.0001**i) for i in range(n)] for a in ASSETS}
        fn=composed_c8_sleeves()
        before=fn({a:v[:n-1] for a,v in bars.items()})
        after=fn(bars)
        self.assertEqual(before,after)

    def test_no_stress_recovery_without_prior_stress(self):
        n=LONG+STEP+1
        bars={a:[100.*(1.0002**i) for i in range(n)] for a in ASSETS}
        output=composed_c8_sleeves()(bars)
        self.assertTrue(all(x[3]==0. for x in output.values()))

if __name__=="__main__":
    unittest.main()
