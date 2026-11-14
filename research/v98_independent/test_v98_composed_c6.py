"""C6 deterministic causal tests; not economic validation."""
import unittest
from .phase243_native_funding_cashflow import ASSETS
from .v98_composed_c6 import composed_c6_sleeves, LONG

class TestC6(unittest.TestCase):
    def test_clean4(self):
        with self.assertRaisesRegex(ValueError,"C6_CLEAN4_ONLY"):
            composed_c6_sleeves()({"BTCUSDT":[1.]})
    def test_prefix_and_budget(self):
        data={a:[100*(1.0002**i) for i in range(LONG+49)] for a in ASSETS}
        f=composed_c6_sleeves()
        first=f({a:v[:LONG+1] for a,v in data.items()})
        self.assertEqual(first,f({a:v[:LONG+2] for a,v in data.items()}))
        self.assertLessEqual(sum(sum(v) for v in first.values()),0.75+1e-10)
        self.assertTrue(all(x>=0 for v in first.values() for x in v))
    def test_invalid_close(self):
        data={a:[100.]*(LONG+1) for a in ASSETS}
        data[ASSETS[0]][-1]=float("nan")
        with self.assertRaisesRegex(ValueError,"C6_INVALID_CLOSE"):
            composed_c6_sleeves()(data)
if __name__=="__main__":
    unittest.main()
