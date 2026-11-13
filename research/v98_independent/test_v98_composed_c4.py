"""C4 deterministic causal sleeve smoke tests; not economic validation."""
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c4 import composed_c4_sleeves, LONG

class TestC4(unittest.TestCase):
    def test_clean4_gate(self):
        with self.assertRaisesRegex(ValueError, "C4_CLEAN4_ONLY"):
            composed_c4_sleeves()({"BTCUSDT":[1.]})
    def test_no_lookahead_prefix(self):
        a={k:[100.*(1.0003**i) for i in range(LONG+49)] for k in ASSETS}
        f=composed_c4_sleeves()
        x=f({k:v[:LONG+1] for k,v in a.items()})
        self.assertTrue(all(len(v)==4 for v in x.values()))
        y=f({k:v[:LONG+2] for k,v in a.items()})
        self.assertEqual(x,y)
        self.assertLessEqual(sum(sum(z) for z in x.values()),0.75+1e-10)
        self.assertTrue(all(z>=0 for v in x.values() for z in v))
    def test_invalid_close(self):
        a={k:[100.]* (LONG+1) for k in ASSETS}
        a[ASSETS[0]][-1]=float('nan')
        with self.assertRaisesRegex(ValueError,"C4_INVALID_CLOSE"):
            composed_c4_sleeves()(a)
if __name__=="__main__":
    unittest.main()
