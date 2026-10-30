"""V98 Independent T pre-economic synthetic tests. No historical trading PnL."""
import unittest
import numpy as np
import pandas as pd
from phase1081_t_sevenslot_source import ASSETS,PATHS,compose_t,governor,normalize,persistence,event_latch

def synthetic(n=2100,seed=22):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    shocks=rng.normal(.00008,.002,(n,4));price=100*np.exp(np.cumsum(shocks,axis=0))
    op=pd.DataFrame(price,index=idx,columns=ASSETS)
    cl=op*(1+rng.normal(0,.0004,(n,4)))
    hi=np.maximum(op,cl)*1.002;lo=np.minimum(op,cl)*.998
    quote=pd.DataFrame(rng.uniform(1e6,3e6,(n,4)),index=idx,columns=ASSETS)
    funding=pd.DataFrame(rng.normal(.00003,.0001,(n,4)),index=idx,columns=ASSETS)
    return op,hi,lo,cl,quote,funding

class TSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=synthetic();cls.paths,cls.diag=compose_t(*cls.frames,diagnostics=True)
    def test_paths(self):
        self.assertEqual(set(self.paths),set(PATHS))
        self.assertFalse(self.diag['historical_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
    def test_caps(self):
        for p in self.paths.values():
            a=p.to_numpy();self.assertTrue(np.isfinite(a).all())
            self.assertLessEqual(np.abs(a).max(),.45+1e-10)
            self.assertLessEqual(np.abs(a).sum(axis=1).max(),1.35+1e-10)
            self.assertLessEqual(np.abs(a.sum(axis=1)).max(),.75+1e-10)
    def test_daily_latch(self):
        for p in self.paths.values():
            changed=(p.diff().abs().sum(axis=1)>0)
            self.assertTrue((p.index[changed].hour==0).all())
    def test_no_future_leak(self):
        a=list(self.frames);b=[x.copy() for x in a]
        for x in b:x.iloc[-200:]*=1.01
        pa=compose_t(*a);pb=compose_t(*b)
        for name in PATHS:
            np.testing.assert_array_equal(pa[name].iloc[:-200].to_numpy(),pb[name].iloc[:-200].to_numpy())
    def test_determinism(self):
        again=compose_t(*self.frames)
        for name in PATHS:
            np.testing.assert_array_equal(self.paths[name].to_numpy(),again[name].to_numpy())
    def test_reject_future(self):
        frames=list(synthetic(n=2100));frames=[x.copy() for x in frames]
        for x in frames:x.index=x.index+pd.DateOffset(years=4)
        with self.assertRaisesRegex(ValueError,'CHRONOLOGICAL'):compose_t(*frames)
    def test_bad_data(self):
        frames=list(self.frames);frames[0]=frames[0].copy();frames[0].iloc[2,0]=np.nan
        with self.assertRaisesRegex(ValueError,'NONFINITE'):compose_t(*frames)
    def test_event_cooldown(self):
        raw=np.ones((20,4));events=np.ones((20,4),bool)
        out=event_latch(raw,events,hold=3,cooldown=8)
        self.assertTrue(np.all(out[0:3]==1));self.assertTrue(np.all(out[3:8]==0))
        self.assertTrue(np.all(out[8:11]==1))
    def test_persistence(self):
        x=np.ones((10,4),bool);out=persistence(x,confirm=3)
        self.assertFalse(out[:2].any());self.assertTrue(out[2:].all())
    def test_zero_governor(self):
        self.assertTrue(np.array_equal(governor(np.zeros((4,4))),np.zeros((4,4))))
    def test_normalize_zero(self):
        self.assertTrue(np.array_equal(normalize(np.zeros((4,4))),np.zeros((4,4))))

if __name__=='__main__':unittest.main()
