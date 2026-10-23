import unittest
import numpy as np
from test_phase1189_ad_online_core_router import sample
from phase1192_ad_covariance_neutral_rv import relative_value_intents,projected_trade


def fixture(n=1100):
    f=sample(n)
    f[3].iloc[800,0]*=1.20
    f[1].iloc[800,0]=max(f[1].iloc[800,0],f[3].iloc[800,0])*1.01
    return f


class RelativeValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=fixture()
        cls.out,cls.diag=relative_value_intents(*cls.f,diagnostics=True)

    def test_projected_trade_neutrality(self):
        cov=np.array([[2.,.5,.2,.1],[.5,1.8,.3,.2],[.2,.3,1.5,.4],[.1,.2,.4,1.3]])
        w=projected_trade(np.array([.2,-.1,.3,-.2]),cov)
        self.assertAlmostEqual(float(w.sum()),0,places=8)
        self.assertAlmostEqual(float((cov[:,0]/cov[0,0])@w),0,places=8)
        self.assertAlmostEqual(float(np.abs(w).sum()),1,places=8)

    def test_non_psd_rejected(self):
        with self.assertRaisesRegex(ValueError,'PSD'):
            projected_trade(np.ones(4),-np.eye(4))

    def test_shock_produces_neutral_intent(self):
        self.assertGreater(float(np.abs(self.out[800]).sum()),.99)
        self.assertAlmostEqual(float(self.out[800].sum()),0,places=7)

    def test_eight_hour_expiry(self):
        np.testing.assert_array_equal(self.out[800:808],np.repeat(self.out[800:801],8,axis=0))
        self.assertTrue(np.all(self.out[808:824]==0))

    def test_warmup(self):
        self.assertTrue((self.out[:336]==0).all())

    def test_prefix_causality(self):
        f=[x.copy() for x in self.f]
        f[3].iloc[900,2]*=1.4
        f[1].iloc[900,2]=max(f[1].iloc[900,2],f[3].iloc[900,2])*1.01
        out=relative_value_intents(*f)
        np.testing.assert_array_equal(self.out[:900],out[:900])

    def test_future_extension(self):
        out=relative_value_intents(*fixture(1300))
        np.testing.assert_array_equal(self.out,out[:1100])

    def test_no_pnl_or_future(self):
        self.assertFalse(self.diag['historical_system_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])
        self.assertFalse(self.diag['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
