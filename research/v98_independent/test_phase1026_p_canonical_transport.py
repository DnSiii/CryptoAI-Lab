#!/usr/bin/env python3
"""Independent P canonical transport source-only numerical invariants."""
import sys,types,unittest
import numpy as np
import pandas as pd
try:import phase866_k_sevenslot_source
except ImportError:
    stub=types.ModuleType('phase866_k_sevenslot_source')
    stub.ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
    stub.START=pd.Timestamp('2022-12-01T00:00:00Z')
    stub.END=pd.Timestamp('2024-12-31T23:00:00Z')
    stub.PINS={}
    sys.modules[stub.__name__]=stub
from phase1026_p_canonical_transport import canonical_scalar,canonical_array

class PCanonicalTests(unittest.TestCase):
    def test_zero_and_exact_monotone(self):
        self.assertEqual(canonical_scalar(0),0.)
        for v in (1e-9,.00001357469,.14,.7,1.75):
            self.assertLessEqual(canonical_scalar(v),v)
            self.assertGreaterEqual(canonical_scalar(v),0)
    def test_invalid_rejected(self):
        for v in (-.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):canonical_scalar(v)
    def test_seeded_matrix_monotone(self):
        rng=np.random.default_rng(1026)
        x=rng.uniform(0,.7,(3000,4))
        y=canonical_array(x)
        self.assertTrue((y<=x+1e-15).all())
        self.assertTrue((y>=0).all())
        np.testing.assert_array_equal(y,canonical_array(x))
    def test_shape(self):
        with self.assertRaises(ValueError):canonical_array(np.ones((3,5)))

if __name__=='__main__':unittest.main()
