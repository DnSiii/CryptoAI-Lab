"""Synthetic no-leak tests of U stop/limit shock source."""
import unittest
import numpy as np
import pandas as pd
from phase1098_u_precommitted_shocks import ASSETS,WINDOW,trailing_shocks

def frames(n=750):
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    cl=pd.DataFrame(100.,index=idx,columns=ASSETS)
    hi=cl*1.01;lo=cl*.99
    return hi,lo,cl

class UShockTests(unittest.TestCase):
    def test_warmup_and_fixed_distance(self):
        d,u=trailing_shocks(*frames())
        self.assertTrue(d.iloc[:WINDOW].isna().all().all())
        self.assertTrue(u.iloc[:WINDOW].isna().all().all())
        self.assertTrue(np.allclose(d.iloc[WINDOW:],.01))
        self.assertTrue(np.allclose(u.iloc[WINDOW:],.01))
    def test_no_future_leak(self):
        a=frames();b=[f.copy() for f in a]
        b[0].iloc[-100:]*=1.10;b[1].iloc[-100:]*=.90
        d0,u0=trailing_shocks(*a);d1,u1=trailing_shocks(*b)
        pd.testing.assert_frame_equal(d0.iloc[:-100],d1.iloc[:-100])
        pd.testing.assert_frame_equal(u0.iloc[:-100],u1.iloc[:-100])
    def test_future_year_rejected(self):
        f=frames()
        for x in f:x.index=x.index+pd.DateOffset(years=3)
        with self.assertRaisesRegex(ValueError,'FUTURE'):trailing_shocks(*f)
    def test_invalid_bar_rejected(self):
        f=list(frames());f[1].iloc[5,0]=200.
        with self.assertRaisesRegex(ValueError,'INVALID_BAR'):trailing_shocks(*f)

if __name__=='__main__':unittest.main()
