#!/usr/bin/env python3
"""V98 S source-only causal deterministic synthetic tests."""
import unittest
import numpy as np
import pandas as pd
from phase1069_s_sevenslot_source import compose_s,ASSETS,PATHS,governor,GROSS,ASSET_CAP,NET_CAP


def data(seed=91,n=1800):
    rng=np.random.default_rng(seed);idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    close=100*np.exp(np.cumsum(rng.normal(.0001,.006,(n,4)),axis=0))
    op=close*np.exp(rng.normal(0,.001,(n,4)))
    hi=np.maximum(op,close)*(1+rng.uniform(.001,.015,(n,4)))
    lo=np.minimum(op,close)*(1-rng.uniform(.001,.015,(n,4)))
    q=rng.uniform(1e5,1e7,(n,4));fund=np.zeros((n,4));fund[::8]=rng.normal(0,.0001,(len(fund[::8]),4))
    return [pd.DataFrame(x,index=idx,columns=ASSETS) for x in (op,hi,lo,close,q,fund)]

class SSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.frames=data();cls.paths,cls.diag=compose_s(*cls.frames,diagnostics=True)
    def test_paths(self):self.assertEqual(tuple(self.paths),PATHS)
    def test_no_pnl(self):self.assertFalse(self.diag['historical_pnl_computed'])
    def test_determinism(self):
        other=compose_s(*self.frames)
        for k in PATHS:np.testing.assert_array_equal(self.paths[k].to_numpy(),other[k].to_numpy())
    def test_caps(self):
        for x in self.paths.values():
            a=x.to_numpy();self.assertTrue(np.isfinite(a).all());self.assertLessEqual(np.abs(a).max(),ASSET_CAP+1e-10)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),GROSS.max()+1e-10)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),NET_CAP+1e-10)
            self.assertTrue(np.allclose(a*1e6,np.round(a*1e6),rtol=0,atol=1e-7))
    def test_causal_future(self):
        fs=[f.copy() for f in self.frames];cut=1450
        for f in fs[:5]:f.iloc[cut:]*=1.05
        fs[5].iloc[cut:]+=.0001
        other=compose_s(*fs)
        for k in PATHS:np.testing.assert_array_equal(self.paths[k].iloc[:cut].to_numpy(),other[k].iloc[:cut].to_numpy())
    def test_ablations(self):
        for k in PATHS:
            if k not in ('S_full','S_minus_opportunity'):self.assertFalse(np.array_equal(self.paths[k].to_numpy(),self.paths['S_full'].to_numpy()))
    def test_opportunity_activation(self):
        fs=[f.copy() for f in self.frames]
        for t in range(1180,1230):
            fs[0].iloc[t,:]=100.;fs[1].iloc[t,:]=100.05;fs[2].iloc[t,:]=99.95;fs[3].iloc[t,:]=100.
        for t in range(1230,1234):
            fs[0].iloc[t,:]=100.;fs[1].iloc[t,:]=111.;fs[2].iloc[t,:]=99.;fs[3].iloc[t,:]=110.
            fs[4].iloc[t,:]=1e9
        p,diag=compose_s(*fs,diagnostics=True)
        self.assertGreater(diag['active_hours']['opportunity'],0)
        self.assertFalse(np.array_equal(p['S_full'].to_numpy(),p['S_minus_opportunity'].to_numpy()))
    def test_adversarial_caps(self):
        rng=np.random.default_rng(33);n=25000;x=rng.normal(0,1,(n,4));s=rng.integers(0,3,n)
        y=governor(x,s)
        self.assertTrue(np.isfinite(y).all());self.assertTrue((np.abs(y).sum(axis=1)<=GROSS[s]+1e-10).all())
        self.assertLessEqual(np.abs(y).max(),ASSET_CAP+1e-10);self.assertLessEqual(np.abs(y.sum(axis=1)).max(),NET_CAP+1e-10)
    def test_reject_future(self):
        fs=[f.copy() for f in self.frames]
        fs=[f.set_axis(pd.date_range('2025-01-01',periods=len(f),freq='h',tz='UTC')) for f in fs]
        with self.assertRaises(ValueError):compose_s(*fs)
    def test_reject_nan(self):
        fs=[f.copy() for f in self.frames];fs[3].iloc[10,0]=np.nan
        with self.assertRaises(ValueError):compose_s(*fs)

if __name__=='__main__':unittest.main()
