"""V98 U causal target synthetic tests. No historical PnL or 2025+."""
import unittest
import numpy as np
import pandas as pd
from phase1092_u_sevenslot_source import ASSETS,PATHS,compose_u,governor,fixed_event_hold,hysteresis

def synthetic(n=2100,seed=98):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    ret=rng.normal(.00005,.002,(n,4))
    price=100*np.exp(np.cumsum(ret,axis=0))
    op=pd.DataFrame(price,index=idx,columns=ASSETS)
    cl=pd.DataFrame(price*(1+rng.normal(0,.0002,(n,4))),index=idx,columns=ASSETS)
    hi=pd.DataFrame(np.maximum(op,cl)*1.002,index=idx,columns=ASSETS)
    lo=pd.DataFrame(np.minimum(op,cl)*.998,index=idx,columns=ASSETS)
    q=pd.DataFrame(rng.uniform(1e6,3e6,(n,4)),index=idx,columns=ASSETS)
    funding=pd.DataFrame(rng.normal(.00001,.0001,(n,4)),index=idx,columns=ASSETS)
    return op,hi,lo,cl,q,funding

class UTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=synthetic()
        cls.paths,cls.diag=compose_u(*cls.frames,diagnostics=True)
    def test_five_paths_and_provenance(self):
        self.assertEqual(set(self.paths),set(PATHS))
        self.assertFalse(self.diag['historical_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
        self.assertTrue(self.diag['contingent_order_validation_required'])
    def test_serialized_caps(self):
        for frame in self.paths.values():
            x=frame.to_numpy()
            self.assertTrue(np.isfinite(x).all())
            self.assertLessEqual(np.abs(x).max(),.45+1e-10)
            self.assertLessEqual(np.abs(x).sum(axis=1).max(),1.35+1e-10)
            self.assertLessEqual(np.abs(x.sum(axis=1)).max(),.75+1e-10)
    def test_eight_hour_rebalance(self):
        for frame in self.paths.values():
            change=frame.diff().abs().sum(axis=1)>0
            self.assertTrue((np.flatnonzero(change)%8==0).all())
    def test_no_future_leak(self):
        f=[x.copy() for x in self.frames];changed=[x.copy() for x in f]
        for x in changed:x.iloc[-200:]*=1.01
        a=compose_u(*f);b=compose_u(*changed)
        for name in PATHS:
            np.testing.assert_array_equal(a[name].iloc[:-200],b[name].iloc[:-200])
    def test_deterministic(self):
        again=compose_u(*self.frames)
        for name in PATHS:
            np.testing.assert_array_equal(self.paths[name],again[name])
    def test_2025_rejected(self):
        f=[x.copy() for x in self.frames]
        for x in f:x.index=x.index+pd.DateOffset(years=3)
        with self.assertRaisesRegex(ValueError,'CHRONOLOGICAL'):compose_u(*f)
    def test_nonfinite_rejected(self):
        f=[x.copy() for x in self.frames];f[0].iloc[4,0]=np.nan
        with self.assertRaisesRegex(ValueError,'NONFINITE'):compose_u(*f)
    def test_negative_quote_rejected(self):
        f=[x.copy() for x in self.frames];f[4].iloc[4,0]=-1
        with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):compose_u(*f)
    def test_governor_nonfinite_fails(self):
        with self.assertRaisesRegex(ValueError,'NONFINITE'):governor([[float('nan')]*4])
    def test_event_cooldown(self):
        x=fixed_event_hold(np.ones((30,4)),np.ones((30,4),bool),24,72)
        self.assertTrue((x[:24]==1).all())
        self.assertTrue((x[24:]==0).all())
    def test_hysteresis(self):
        a=hysteresis([1,0,0,0,1,1,2,2,2],hours=3)
        self.assertEqual(a.tolist(),[1,0,0,0,1,1,1,2,2])

if __name__=='__main__':unittest.main()
