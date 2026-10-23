#!/usr/bin/env python3
"""W seven-slot synthetic chronology and portfolio tests; no economic receipts."""
import unittest
import numpy as np
import pandas as pd
from phase1111_w_sevenslot_source import ASSETS,PATHS,compose_w,validate
from phase1110_w_256state_governor import ASSET_CAP,NET_CAP,GROSS_CAP

def sample(n=1900,seed=1111):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(0,.005,(n,4))
    close=100*np.exp(np.cumsum(r,axis=0))
    op=np.vstack((close[0],close[:-1]))
    high=np.maximum(op,close)*(1+rng.uniform(.0001,.008,(n,4)))
    low=np.minimum(op,close)*(1-rng.uniform(.0001,.008,(n,4)))
    q=rng.uniform(1e8,1e10,(n,4));funding=rng.uniform(-.0001,.0001,(n,4))
    return tuple(pd.DataFrame(x,index=idx,columns=ASSETS)
                 for x in (op,high,low,close,q,funding))

class TestWSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample()
        cls.paths,cls.diag=compose_w(*cls.frames,diagnostics=True)
    def test_five_paths(self):
        self.assertEqual(tuple(self.paths),PATHS)
        self.assertEqual(self.diag['target_execution'],'t+1_open_only')
    def test_caps_and_quantization(self):
        for name,frame in self.paths.items():
            a=frame.to_numpy()
            self.assertTrue(np.isfinite(a).all(),name)
            self.assertLessEqual(np.abs(a).max(),ASSET_CAP+1e-8)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),GROSS_CAP+1e-8)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),NET_CAP+1e-8)
            np.testing.assert_allclose(a*1e6,np.round(a*1e6),atol=1e-8,rtol=0)
    def test_no_2025_or_2026(self):
        for year in (2025,2026):
            idx=pd.date_range(f'{year}-01-01',periods=len(self.frames[0]),freq='h',tz='UTC')
            with self.assertRaises(ValueError):
                validate(*[x.set_axis(idx) for x in self.frames])
    def test_no_xrp_or_misaligned_time(self):
        frames=list(self.frames);frames[0]=frames[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaises(ValueError):validate(*frames)
        frames=list(self.frames);frames[0]=frames[0].shift(freq='h')
        with self.assertRaises(ValueError):validate(*frames)
    def test_no_future_leakage(self):
        future=1750
        changed=[x.copy() for x in self.frames]
        for j in (0,1,2,3):changed[j].iloc[future:]*=2.
        changed[4].iloc[future:]*=10.
        altered=compose_w(*changed)
        for path in PATHS:
            np.testing.assert_array_equal(self.paths[path].iloc[:future].to_numpy(),
                                          altered[path].iloc[:future].to_numpy())
    def test_deterministic(self):
        again=compose_w(*self.frames)
        for path in PATHS:
            np.testing.assert_array_equal(self.paths[path].to_numpy(),again[path].to_numpy())
    def test_not_economic(self):
        for key in ('historical_pnl_computed','validation_2025_read',
                    'external_benchmarks_used','holdout_accessed'):
            self.assertFalse(self.diag[key])
if __name__=='__main__':unittest.main()
