#!/usr/bin/env python3
"""Y five-path source, causal folds and Clean-4 synthetic tests only."""
import unittest
import numpy as np
import pandas as pd
from phase1125_y_sevenslot_source import compose_y,validate,ASSETS,PATHS

def sample(n=1900,seed=1125):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(0,.005,(n,4))
    close=100*np.exp(np.cumsum(r,axis=0))
    op=np.vstack((close[0],close[:-1]))
    high=np.maximum(op,close)*(1+rng.uniform(.0001,.008,(n,4)))
    low=np.minimum(op,close)*(1-rng.uniform(.0001,.008,(n,4)))
    q=rng.uniform(1e8,1e10,(n,4))
    funding=rng.uniform(-.0001,.0001,(n,4))
    return tuple(pd.DataFrame(x,index=idx,columns=ASSETS)
                 for x in (op,high,low,close,q,funding))

class TestYSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=sample()
        cls.p,cls.d=compose_y(*cls.f,diagnostics=True)
    def test_five_paths(self):
        self.assertEqual(tuple(self.p),PATHS)
        self.assertEqual(self.d['target_execution'],'t+1_open_only')
    def test_caps_and_quantization(self):
        for k,f in self.p.items():
            a=f.to_numpy()
            self.assertTrue(np.isfinite(a).all(),k)
            self.assertLessEqual(np.abs(a).max(),.45+1e-8)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),1.35+1e-8)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),.75+1e-8)
            np.testing.assert_allclose(a*1e6,np.round(a*1e6),atol=1e-8,rtol=0)
    def test_no_future_leak(self):
        future=1750;changed=[f.copy() for f in self.f]
        for j in (0,1,2,3):changed[j].iloc[future:]*=2.
        changed[4].iloc[future:]*=10.
        p=compose_y(*changed)
        for k in PATHS:
            np.testing.assert_array_equal(self.p[k].iloc[:future].to_numpy(),
                                          p[k].iloc[:future].to_numpy())
    def test_no_2025_or_2026(self):
        for year in (2025,2026):
            idx=pd.date_range(f'{year}-01-01',periods=len(self.f[0]),freq='h',tz='UTC')
            with self.assertRaises(ValueError):
                validate(*[x.set_axis(idx) for x in self.f])
    def test_xrp_quarantine(self):
        fs=list(self.f)
        fs[0]=fs[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaises(ValueError):validate(*fs)
    def test_four_sleeves_active(self):
        for k,v in self.d['sleeve_active_hours'].items():
            self.assertGreater(v,0,k)
        self.assertFalse(np.array_equal(self.p['Y_core_only'].to_numpy(),
                                        self.p['Y_full'].to_numpy()))
    def test_deterministic(self):
        p=compose_y(*self.f)
        for k in PATHS:
            np.testing.assert_array_equal(self.p[k].to_numpy(),p[k].to_numpy())
    def test_no_economic_claims(self):
        for k in ('historical_pnl_computed','validation_2025_read',
                  'external_benchmarks_used','holdout_accessed'):
            self.assertFalse(self.d[k])
if __name__=='__main__':unittest.main()
