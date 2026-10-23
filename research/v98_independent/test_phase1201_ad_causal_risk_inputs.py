import unittest
import numpy as np
from test_phase1189_ad_online_core_router import sample
from phase1201_ad_causal_risk_inputs import causal_risk


class RiskInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample(1000)
        cls.r=causal_risk(*cls.frames)

    def test_five_arrays_finite_after_warmup(self):
        self.assertEqual(len(self.r),5)
        for x in self.r.values():
            self.assertEqual(x.shape,(1000,4))
            self.assertTrue(np.isfinite(x[720:]).all())

    def test_downside_and_upside_minimum(self):
        self.assertTrue((self.r['down'][720:]>=.25).all())
        self.assertTrue((self.r['up'][720:]>=.30).all())
        self.assertTrue((self.r['funding_bound'][720:]>=.005).all())

    def test_strict_previous_hour_quote(self):
        np.testing.assert_array_equal(self.r['prior_quote'][720:],
                                      self.frames[4].to_numpy()[719:-1])

    def test_current_extreme_cannot_change_current_risk(self):
        f=[x.copy() for x in self.frames]
        f[1].iloc[800,0]*=5
        r=causal_risk(*f)
        for k in self.r:
            np.testing.assert_array_equal(self.r[k][:801],r[k][:801])
        self.assertGreater(r['up'][801,0],self.r['up'][801,0])

    def test_funding_current_excluded(self):
        f=[x.copy() for x in self.frames]
        f[5].iloc[800,0]=.1
        r=causal_risk(*f)
        np.testing.assert_array_equal(self.r['funding_bound'][:801],r['funding_bound'][:801])
        self.assertGreater(r['funding_bound'][801,0],self.r['funding_bound'][801,0])

    def test_short_history_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'MINIMUM_WARMUP'):
            causal_risk(*sample(700))


if __name__=='__main__':unittest.main()
