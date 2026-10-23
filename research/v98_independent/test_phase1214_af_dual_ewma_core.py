import unittest
import numpy as np
import pandas as pd
from phase1214_af_dual_ewma_core import (
    ASSETS,START,LIQUIDITY_WINDOW,af_growth_source,capped_growth,source_digest)


def sample(n=900):
    idx=pd.date_range(START,periods=n,freq='h')
    t=np.arange(n,dtype=float)
    trends=np.array([.001,.0012,.0009,-.0005])
    close=100*np.exp(t[:,None]*trends[None,:])
    opening=np.vstack((close[0],close[:-1]))
    high=np.maximum(opening,close)*1.0003
    low=np.minimum(opening,close)*.9997
    quote=np.full_like(close,1e9)
    rate=np.zeros_like(close)
    event=np.zeros_like(close)
    event[::8]=1
    rate[::8]=.0001
    return [pd.DataFrame(a,index=idx,columns=ASSETS)
            for a in (opening,high,low,close,quote,rate,event)]


class AFLongOnlyCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample()
        cls.out=af_growth_source(*cls.frames)

    def test_strict_336h_liquidity_warmup(self):
        self.assertEqual(self.out.shape,(900,4))
        self.assertTrue(np.all(self.out[:LIQUIDITY_WINDOW]==0))

    def test_positive_growth_deployed_not_cash_only(self):
        w=self.out[500]
        self.assertTrue(np.all(w[:3]>0))
        self.assertEqual(w[3],0)
        self.assertAlmostEqual(w.sum(),.75,places=10)

    def test_no_short_or_hidden_leverage(self):
        self.assertTrue(np.all(self.out>=0))
        self.assertLessEqual(self.out.max(),.30+1e-10)
        self.assertLessEqual(self.out.sum(axis=1).max(),.75+1e-10)

    def test_capped_growth_redistributes_to_profitable_assets(self):
        w=capped_growth(np.array([10.,1.,1.,1.]))
        self.assertAlmostEqual(w[0],.30,places=10)
        np.testing.assert_allclose(w[1:],np.full(3,.15),atol=1e-10)

    def test_current_close_cannot_change_previous_decisions(self):
        f=[x.copy() for x in self.frames]
        f[3].iloc[500,0]*=1.05
        f[1].iloc[500,0]=max(f[1].iloc[500,0],f[3].iloc[500,0])
        new=af_growth_source(*f)
        np.testing.assert_array_equal(self.out[:500],new[:500])
        self.assertFalse(np.array_equal(self.out[500:],new[500:]))

    def test_current_quote_cannot_change_current_decision(self):
        f=[x.copy() for x in self.frames]
        f[4].iloc[500,0]=0
        new=af_growth_source(*f)
        np.testing.assert_array_equal(self.out[:501],new[:501])
        self.assertNotEqual(self.out[501,0],new[501,0])

    def test_deterministic_source_digest(self):
        a=source_digest(self.frames[0].index,self.out)
        b=source_digest(self.frames[0].index,af_growth_source(*self.frames))
        self.assertEqual(a,b)
        self.assertEqual(len(a),64)

    def test_reject_xrp_and_future_holdout(self):
        f=sample()
        f[0].columns=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT']
        with self.assertRaisesRegex(ValueError,'CLEAN4_COLUMNS'):
            af_growth_source(*f)
        f=sample()
        idx=pd.date_range('2024-12-31T00:00:00Z',periods=900,freq='h')
        f=[pd.DataFrame(x.to_numpy(),index=idx,columns=ASSETS) for x in f]
        with self.assertRaisesRegex(ValueError,'TRAINING_CHRONOLOGY'):
            af_growth_source(*f)


if __name__=='__main__':unittest.main()
