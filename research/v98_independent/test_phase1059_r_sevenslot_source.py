#!/usr/bin/env python3
"""V98 R source-only deterministic and adversarial integration tests."""
import unittest
import numpy as np
import pandas as pd
from phase1059_r_sevenslot_source import compose_r,ASSETS,PATHS,governor,GROSS,NET_CAP,ASSET_CAP


def synthetic(seed=23,n=1800):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    logret=rng.normal(.00006,.007,(n,4));close=100*np.exp(np.cumsum(logret,axis=0))
    op=close*np.exp(rng.normal(0,.001,(n,4)))
    high=np.maximum(op,close)*(1+rng.uniform(.001,.01,(n,4)))
    low=np.minimum(op,close)*(1-rng.uniform(.001,.01,(n,4)))
    quote=rng.uniform(1e5,2e6,(n,4))
    funding=np.zeros((n,4));funding[::8]=rng.normal(.00002,.0001,(len(funding[::8]),4))
    return [pd.DataFrame(a,index=idx,columns=ASSETS) for a in (op,high,low,close,quote,funding)]

class RSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.frames=synthetic();cls.paths,cls.diag=compose_r(*cls.frames,diagnostics=True)
    def test_five_paths(self):self.assertEqual(tuple(self.paths),PATHS)
    def test_no_economics(self):self.assertFalse(self.diag['historical_pnl_computed'])
    def test_determinism(self):
        other=compose_r(*self.frames)
        for k in PATHS:np.testing.assert_array_equal(self.paths[k].to_numpy(),other[k].to_numpy())
    def test_caps(self):
        for f in self.paths.values():
            a=f.to_numpy();self.assertTrue(np.isfinite(a).all());self.assertLessEqual(np.abs(a).max(),ASSET_CAP+1e-10)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),GROSS.max()+1e-10)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),NET_CAP+1e-10)
            self.assertTrue(np.allclose(a*1e8,np.round(a*1e8),atol=1e-7))
    def test_causality(self):
        frames=[x.copy() for x in self.frames];cut=1450
        for f in frames[:5]:f.iloc[cut:]*=1.04
        frames[5].iloc[cut:]+=0.0005
        other=compose_r(*frames)
        for k in PATHS:np.testing.assert_array_equal(self.paths[k].iloc[:cut].to_numpy(),other[k].iloc[:cut].to_numpy())
    def test_funding_causal(self):
        frames=[x.copy() for x in self.frames];cut=1500
        frames[5].iloc[cut:]+=np.array([.002,-.002,.001,-.001])
        other=compose_r(*frames)
        np.testing.assert_array_equal(self.paths['R_full'].iloc[:cut].to_numpy(),other['R_full'].iloc[:cut].to_numpy())
        self.assertFalse(np.array_equal(self.paths['R_full'].iloc[cut+1:].to_numpy(),other['R_full'].iloc[cut+1:].to_numpy()))
    def test_ablations_not_identical(self):
        for k in PATHS:
            if k!='R_full':self.assertFalse(np.array_equal(self.paths[k].to_numpy(),self.paths['R_full'].to_numpy()))
    def test_boundary_rounding(self):
        x=np.array([[.2166666666,.2166666666,.2166666666,0.]])
        y=governor(x,np.array([2]))
        self.assertLessEqual(abs(y.sum()),NET_CAP+1e-10)
        self.assertTrue(np.isfinite(y).all())
    def test_forbid_future(self):
        frames=[f.copy() for f in self.frames]
        frames=[f.set_axis(pd.date_range('2025-01-01',periods=len(f),freq='h',tz='UTC')) for f in frames]
        with self.assertRaises(ValueError):compose_r(*frames)
    def test_reject_nan(self):
        frames=[f.copy() for f in self.frames];frames[3].iloc[700,0]=np.nan
        with self.assertRaises(ValueError):compose_r(*frames)
    def test_reject_gaps(self):
        frames=[f.copy() for f in self.frames]
        frames=[f.drop(f.index[20]) for f in frames]
        with self.assertRaises(ValueError):compose_r(*frames)

if __name__=='__main__':unittest.main()
