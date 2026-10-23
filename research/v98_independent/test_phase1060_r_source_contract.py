#!/usr/bin/env python3
"""V98 R source-only canonical invariants; no historical economics."""
import unittest
import numpy as np
import pandas as pd
from phase1060_r_source_auth import canonicalize
from phase1059_r_sevenslot_source import governor,ASSETS,GROSS,ASSET_CAP,NET_CAP

class RContractTest(unittest.TestCase):
    def test_roundtrip(self):
        rng=np.random.default_rng(12)
        for state in (0,1,2):
            x=governor(rng.normal(0,.4,(200,4)),np.full(200,state))
            frame=pd.DataFrame(x,columns=ASSETS)
            self.assertEqual(canonicalize(frame),canonicalize(frame.copy()))
            self.assertLessEqual(np.abs(x).sum(axis=1).max(),GROSS[state]+1e-10)
    def test_adversarial(self):
        rng=np.random.default_rng(222)
        n=25000;x=rng.normal(0,.8,(n,4));states=rng.integers(0,3,n)
        y=governor(x,states)
        self.assertTrue(np.isfinite(y).all())
        self.assertTrue((np.abs(y).sum(axis=1)<=GROSS[states]+1e-10).all())
        self.assertLessEqual(np.abs(y).max(),ASSET_CAP+1e-10)
        self.assertLessEqual(np.abs(y.sum(axis=1)).max(),NET_CAP+1e-10)
    def test_unsafe_rounded_net_rejected(self):
        x=np.array([[.23333334,.23333334,.23333334,0.]])
        with self.assertRaisesRegex(ValueError,'CAP_BREACH'):
            canonicalize(pd.DataFrame(x,columns=ASSETS))
    def test_reject_precision(self):
        x=np.array([[.123456789,0,0,0.]])
        with self.assertRaisesRegex(ValueError,'PRECISION'):
            canonicalize(pd.DataFrame(x,columns=ASSETS))
    def test_reject_nan(self):
        with self.assertRaises(ValueError):canonicalize(pd.DataFrame([[float('nan'),0,0,0]],columns=ASSETS))

if __name__=='__main__':unittest.main()
