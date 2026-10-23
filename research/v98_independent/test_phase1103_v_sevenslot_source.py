"""V composed seven-slot synthetic tests, no historical PnL."""
import unittest
import numpy as np
import pandas as pd
from phase1103_v_sevenslot_source import ASSETS,PATHS,compose_v

def frames(n=2200,seed=1103):
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    ret=rng.normal(.0001,.002,(n,4))
    price=100*np.exp(np.cumsum(ret,axis=0))
    op=pd.DataFrame(price,index=idx,columns=ASSETS)
    cl=pd.DataFrame(price*(1+rng.normal(0,.0002,(n,4))),index=idx,columns=ASSETS)
    hi=pd.DataFrame(np.maximum(op,cl)*1.002,index=idx,columns=ASSETS)
    lo=pd.DataFrame(np.minimum(op,cl)*.998,index=idx,columns=ASSETS)
    quote=pd.DataFrame(rng.uniform(1e6,3e6,(n,4)),index=idx,columns=ASSETS)
    funding=np.zeros((n,4));funding[::8]=rng.normal(.00001,.0001,(len(funding[::8]),4))
    fr=pd.DataFrame(funding,index=idx,columns=ASSETS)
    return op,hi,lo,cl,quote,fr

class VSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=frames()
        cls.paths,cls.diag=compose_v(*cls.frames,diagnostics=True)
    def test_five_paths_and_provenance(self):
        self.assertEqual(set(self.paths),set(PATHS))
        self.assertFalse(self.diag['historical_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
    def test_composition_distinct(self):
        full=self.paths['V_full'].to_numpy()
        self.assertTrue(all(np.any(full!=self.paths[k].to_numpy()) for k in PATHS if k!='V_full'))
    def test_twelve_hour_causal_decisions(self):
        for frame in self.paths.values():
            change=frame.diff().abs().sum(axis=1)>0
            self.assertTrue((np.flatnonzero(change)%12==0).all())
    def test_serialized_point_caps(self):
        for frame in self.paths.values():
            x=frame.to_numpy(float)
            self.assertTrue(np.isfinite(x).all())
            self.assertLessEqual(np.abs(x).max(),.45+1e-9)
            self.assertLessEqual(np.abs(x).sum(axis=1).max(),1.35+1e-9)
            self.assertLessEqual(np.abs(x.sum(axis=1)).max(),.75+1e-9)
    def test_no_future_leak(self):
        changed=[x.copy() for x in self.frames]
        for f in changed:f.iloc[-100:]*=1.01
        altered=compose_v(*changed)
        for k in PATHS:
            np.testing.assert_array_equal(self.paths[k].iloc[:-100],altered[k].iloc[:-100])
    def test_2025_firewall(self):
        changed=[x.copy() for x in self.frames]
        for f in changed:f.index=f.index+pd.DateOffset(years=3)
        with self.assertRaisesRegex(ValueError,'FUTURE'):compose_v(*changed)

if __name__=='__main__':unittest.main()
