import unittest
import numpy as np
import pandas as pd
from phase1205_ae_breakout_source import (
    ASSETS,START,CHANNEL,ae_breakout_source,source_digest,validate_ae_source)


def sample(n=900):
    idx=pd.date_range(START,periods=n,freq='h')
    t=np.arange(n,dtype=float)
    rates=np.array([.0015,.0018,.0013,-.0015])
    close=100*np.exp(t[:,None]*rates[None,:])
    opening=np.vstack([close[0],close[:-1]])
    high=np.maximum(opening,close)*1.0003
    low=np.minimum(opening,close)*.9997
    quote=np.full_like(close,1e9)
    funding=np.zeros_like(close)
    event=np.zeros_like(close)
    event[::8]=1
    funding[::8]=.0001
    return [pd.DataFrame(a,index=idx,columns=ASSETS)
            for a in (opening,high,low,close,quote,funding,event)]


class AEIndependentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample()
        cls.out=ae_breakout_source(*cls.frames)

    def test_warmup_and_shapes(self):
        g,o,v,r=self.out
        for x in (g,o,v):
            self.assertEqual(x.shape,(900,4))
            self.assertTrue(np.isfinite(x).all())
            self.assertTrue(np.all(x[:CHANNEL]==0))
        self.assertEqual(r.shape,(900,3))
        np.testing.assert_array_equal(r.sum(axis=1),np.ones(900))

    def test_growth_breakouts_both_sides(self):
        g=self.out[0]
        self.assertTrue(np.all(g[400,0:3]>0))
        self.assertLess(g[400,3],0)
        self.assertAlmostEqual(np.abs(g[400]).sum(),.65,places=10)

    def test_opportunity_three_breakouts_and_rv_zero_net(self):
        opp,rv=self.out[1],self.out[2]
        self.assertTrue(np.any(opp[240:400,0:3]>0))
        self.assertTrue(np.all(rv[400,0:3]>0))
        self.assertLess(rv[400,3],0)
        np.testing.assert_allclose(rv.sum(axis=1),0,atol=1e-12)
        self.assertLessEqual(np.abs(opp).sum(axis=1).max(),.12+1e-10)

    def test_strict_t_minus_one_channel(self):
        altered=[x.copy() for x in self.frames]
        altered[1].iloc[500,0]*=100
        new=ae_breakout_source(*altered)
        for a,b in zip(self.out,new):
            np.testing.assert_array_equal(a[:501],b[:501])
        self.assertTrue(any(not np.array_equal(a[530:],b[530:])
                            for a,b in zip(self.out,new)))

    def test_funding_change_cannot_create_breakout(self):
        altered=[x.copy() for x in self.frames]
        altered[5].iloc[504,0]=.05
        new=ae_breakout_source(*altered)
        for a,b in zip(self.out,new):
            np.testing.assert_array_equal(a,b)

    def test_deterministic_hash(self):
        a=source_digest(self.frames[0].index,self.out)
        b=source_digest(self.frames[0].index,ae_breakout_source(*self.frames))
        self.assertEqual(a,b)
        self.assertEqual(len(a),64)

    def test_reject_missing_hour_and_unmasked_funding(self):
        f=sample()
        f[0]=f[0].drop(f[0].index[400])
        with self.assertRaisesRegex(ValueError,'TRAINING_CHRONOLOGY'):
            ae_breakout_source(*f)
        f=sample()
        f[5].iloc[401,0]=.02
        with self.assertRaisesRegex(ValueError,'NATIVE_FUNDING_MASK'):
            ae_breakout_source(*f)

    def test_reject_future_year_and_xrp(self):
        f=sample()
        f[0].columns=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT']
        with self.assertRaisesRegex(ValueError,'CLEAN4_COLUMNS'):
            ae_breakout_source(*f)
        f=sample()
        idx=pd.date_range('2024-12-31T00:00:00Z',periods=900,freq='h')
        f=[pd.DataFrame(x.to_numpy(),index=idx,columns=ASSETS) for x in f]
        with self.assertRaisesRegex(ValueError,'TRAINING_CHRONOLOGY'):
            ae_breakout_source(*f)


if __name__=='__main__':
    unittest.main()
