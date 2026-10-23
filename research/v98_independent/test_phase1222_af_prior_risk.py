import unittest
import numpy as np
from test_phase1214_af_dual_ewma_core import sample
from phase1222_af_prior_risk import af_prior_risk


class AFPriorRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=sample(1000)
        cls.r=af_prior_risk(*cls.f)

    def test_five_finite_strict_prior_arrays(self):
        self.assertEqual(len(self.r),5)
        for x in self.r.values():
            self.assertEqual(x.shape,(1000,4))
            self.assertTrue(np.isfinite(x[720:]).all())

    def test_previous_quote_exact(self):
        np.testing.assert_array_equal(self.r['prior_quote'][720:],
                                      self.f[4].to_numpy()[719:-1])

    def test_conservative_risk_floors(self):
        self.assertTrue((self.r['down'][720:]>=.40).all())
        self.assertTrue((self.r['up'][720:]>=.50).all())
        self.assertTrue((self.r['funding_bound'][720:]>=.007).all())

    def test_current_low_extreme_only_affects_future(self):
        f=[x.copy() for x in self.f]
        f[2].iloc[800,0]*=.1
        r=af_prior_risk(*f)
        for k in self.r:np.testing.assert_array_equal(self.r[k][:801],r[k][:801])
        self.assertGreater(r['down'][801,0],self.r['down'][801,0])

    def test_current_high_extreme_only_affects_future(self):
        f=[x.copy() for x in self.f]
        f[1].iloc[800,0]*=10
        r=af_prior_risk(*f)
        for k in self.r:np.testing.assert_array_equal(self.r[k][:801],r[k][:801])
        self.assertGreater(r['up'][801,0],self.r['up'][801,0])

    def test_current_quote_only_affects_future(self):
        f=[x.copy() for x in self.f]
        f[4].iloc[800,0]=0
        r=af_prior_risk(*f)
        for k in self.r:np.testing.assert_array_equal(self.r[k][:801],r[k][:801])
        self.assertEqual(r['prior_quote'][801,0],0)

    def test_native_funding_event_only_affects_future(self):
        f=[x.copy() for x in self.f]
        f[5].iloc[800,0]=.10
        r=af_prior_risk(*f)
        for k in self.r:np.testing.assert_array_equal(self.r[k][:801],r[k][:801])
        self.assertGreater(r['funding_bound'][801,0],self.r['funding_bound'][801,0])

    def test_short_history_rejected(self):
        with self.assertRaisesRegex(ValueError,'MINIMUM_720_WARMUP'):
            af_prior_risk(*sample(700))


if __name__=='__main__':unittest.main()
