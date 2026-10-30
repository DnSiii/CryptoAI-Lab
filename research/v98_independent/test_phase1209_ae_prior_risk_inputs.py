import unittest
import numpy as np
from test_phase1205_ae_breakout_source import sample
from phase1209_ae_prior_risk_inputs import ae_prior_risk


class AEPriorRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample(1000)
        cls.risk=ae_prior_risk(*cls.frames)

    def test_five_finite_clean4_risk_arrays(self):
        self.assertEqual(len(self.risk),5)
        for a in self.risk.values():
            self.assertEqual(a.shape,(1000,4))
            self.assertTrue(np.isfinite(a[720:]).all())

    def test_strict_prior_quote(self):
        np.testing.assert_array_equal(self.risk['prior_quote'][720:],
                                      self.frames[4].to_numpy()[719:-1])

    def test_strict_downside_and_upside_floors(self):
        self.assertTrue((self.risk['down'][720:]>=.35).all())
        self.assertTrue((self.risk['up'][720:]>=.45).all())
        self.assertTrue((self.risk['funding_bound'][720:]>=.006).all())

    def test_current_low_shock_only_impacts_future(self):
        f=[x.copy() for x in self.frames]
        f[2].iloc[800,0]*=.1
        r=ae_prior_risk(*f)
        for k in self.risk:
            np.testing.assert_array_equal(self.risk[k][:801],r[k][:801])
        self.assertGreater(r['down'][801,0],self.risk['down'][801,0])

    def test_current_high_shock_only_impacts_future(self):
        f=[x.copy() for x in self.frames]
        f[1].iloc[800,0]*=10
        r=ae_prior_risk(*f)
        for k in self.risk:
            np.testing.assert_array_equal(self.risk[k][:801],r[k][:801])
        self.assertGreater(r['up'][801,0],self.risk['up'][801,0])

    def test_current_quote_liquidity_only_impacts_future(self):
        f=[x.copy() for x in self.frames]
        f[4].iloc[800,0]=0
        r=ae_prior_risk(*f)
        for k in self.risk:
            np.testing.assert_array_equal(self.risk[k][:801],r[k][:801])
        self.assertEqual(r['prior_quote'][801,0],0)
        self.assertEqual(r['min_quote'][801,0],0)

    def test_native_funding_event_only_impacts_future(self):
        f=[x.copy() for x in self.frames]
        f[5].iloc[800,0]=.10
        r=ae_prior_risk(*f)
        for k in self.risk:
            np.testing.assert_array_equal(self.risk[k][:801],r[k][:801])
        self.assertGreater(r['funding_bound'][801,0],
                           self.risk['funding_bound'][801,0])

    def test_short_history_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'MINIMUM_720_WARMUP'):
            ae_prior_risk(*sample(700))


if __name__=='__main__':unittest.main()
