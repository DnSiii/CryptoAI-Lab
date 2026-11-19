"""C18 causal/shape deterministic regression tests (synthetic data only)."""
import math
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c18 import c18_model, WARMUP, REBALANCE

class C18Causality(unittest.TestCase):
    def _history(self, length, perturb=False):
        d={}
        for j,a in enumerate(ASSETS):
            d[a]=[100*math.exp((0.00005+j*0.00001)*i) for i in range(length)]
            if perturb:
                d[a][-1]*=1.01
        return d

    def test_warmup_returns_zero(self):
        compute,_=c18_model()
        out=compute(self._history(WARMUP))
        self.assertTrue(all(sum(v)==0 for v in out.values()))

    def test_determinism_at_first_decision(self):
        n=WARMUP+1
        a,_=c18_model()
        b,_=c18_model()
        self.assertEqual(a(self._history(n)),b(self._history(n)))

    def test_non_rebalance_close_does_not_recompute(self):
        n=WARMUP+1
        compute,_=c18_model()
        first=compute(self._history(n))
        self.assertEqual(first,compute(self._history(n+1,perturb=True)))

    def test_malformed_price_rejected_at_decision(self):
        compute,_=c18_model()
        h=self._history(WARMUP+1)
        h[ASSETS[0]][-1]=float('nan')
        with self.assertRaisesRegex(ValueError,"C18_INVALID_CLOSE"):
            compute(h)

if __name__=="__main__":
    unittest.main()
