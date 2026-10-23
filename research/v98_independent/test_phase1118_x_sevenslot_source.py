#!/usr/bin/env python3
"""X source chronology and 5-path risk tests, synthetic only."""
import unittest
import numpy as np
import pandas as pd
from phase1118_x_sevenslot_source import compose_x,validate,ASSETS,PATHS

def sample(n=1900,seed=1118):
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

class TestXSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=sample()
        cls.p,cls.d=compose_x(*cls.f,diagnostics=True)
    def test_five_paths(self):
        self.assertEqual(tuple(self.p),PATHS)
        self.assertEqual(self.d['target_execution'],'t+1_open_only')
    def test_no_future_leak(self):
        changed=[f.copy() for f in self.f]
        for j in (0,1,2,3):changed[j].iloc[1750:]*=2.
        changed[4].iloc[1750:]*=10.
        p=compose_x(*changed)
        for k in PATHS:
            np.testing.assert_array_equal(self.p[k].iloc[:1750].to_numpy(),
                                          p[k].iloc[:1750].to_numpy())
    def test_caps_and_quantization(self):
        for k,f in self.p.items():
            a=f.to_numpy()
            self.assertTrue(np.isfinite(a).all(),k)
            self.assertLessEqual(np.abs(a).max(),.45+1e-8)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),1.35+1e-8)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),.75+1e-8)
            np.testing.assert_allclose(a*1e6,np.round(a*1e6),atol=1e-8,rtol=0)
    def test_2025_2026_blocked(self):
        for year in (2025,2026):
            idx=pd.date_range(f'{year}-01-01',periods=len(self.f[0]),freq='h',tz='UTC')
            with self.assertRaises(ValueError):
                validate(*[x.set_axis(idx) for x in self.f])
    def test_xrp_blocked(self):
        frames=list(self.f)
        frames[0]=frames[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaises(ValueError):validate(*frames)
    def test_distinct_sleeves_active(self):
        for name,v in self.d['active_hours'].items():
            self.assertGreater(v,0,name)
        self.assertFalse(np.array_equal(self.p['X_core_only'].to_numpy(),
                                        self.p['X_full'].to_numpy()))
    def test_reproducible(self):
        p=compose_x(*self.f)
        for k in PATHS:
            np.testing.assert_array_equal(self.p[k].to_numpy(),p[k].to_numpy())
    def test_not_economic(self):
        for k in ('historical_pnl_computed','validation_2025_read',
                  'holdout_accessed','external_benchmarks_used'):
            self.assertFalse(self.d[k])
if __name__=='__main__':unittest.main()
