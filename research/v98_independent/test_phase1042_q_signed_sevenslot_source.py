import unittest
import numpy as np
import pandas as pd
from phase1042_q_signed_sevenslot_source import compose_q,PATHS,ASSETS

class QSourceTests(unittest.TestCase):
    def make(self,n=1700):
        rng=np.random.default_rng(1042)
        idx=pd.date_range('2023-01-01',periods=n,freq='h',tz='UTC')
        ret=rng.normal(0,.006,(n,4))+np.sin(np.arange(n)/100)[:,None]*.001
        close=100*np.exp(np.cumsum(ret,axis=0));opening=np.vstack((close[0],close[:-1]))
        hi=np.maximum(opening,close)*1.002;lo=np.minimum(opening,close)*.998
        quote=np.ones((n,4))*1e6;quote[1200:1208]=3e6
        funding=np.zeros((n,4));funding[::8]=.0001
        def frame(x):return pd.DataFrame(x,index=idx,columns=ASSETS)
        return tuple(frame(x) for x in (opening,hi,lo,close,quote,funding))
    def test_five_paths_and_signed_limits(self):
        paths,diag=compose_q(*self.make(),diagnostics=True)
        self.assertEqual(tuple(paths),PATHS)
        self.assertFalse(diag['historical_pnl_computed'])
        for p in paths.values():
            x=p.to_numpy();self.assertTrue(np.isfinite(x).all())
            self.assertLessEqual(np.abs(x).max(),.55+1e-10)
            self.assertLessEqual(np.abs(x).sum(axis=1).max(),1.40+1e-10)
            self.assertLessEqual(np.abs(x.sum(axis=1)).max(),.65+1e-10)
    def test_determinism(self):
        args=self.make();a=compose_q(*args);b=compose_q(*args)
        for k in PATHS:np.testing.assert_array_equal(a[k].to_numpy(),b[k].to_numpy())
    def test_future_hour_causality(self):
        args=list(self.make());first=compose_q(*args)['Q_full'].to_numpy()
        changed=args[3].copy();changed.iloc[-1,:]*=1.1
        hi=args[1].copy();hi.iloc[-1,:]=np.maximum(hi.iloc[-1,:],changed.iloc[-1,:])
        args[3]=changed;args[1]=hi
        second=compose_q(*args)['Q_full'].to_numpy()
        np.testing.assert_array_equal(first[:-1],second[:-1])
    def test_reject_2025(self):
        args=list(self.make());args=[x.set_axis(x.index+pd.DateOffset(years=2)) for x in args]
        with self.assertRaises(ValueError):compose_q(*args)

if __name__=='__main__':unittest.main()
