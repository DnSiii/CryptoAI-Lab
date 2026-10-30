#!/usr/bin/env python3
"""AH1238 actual NAV short factor hedge and causal hysteresis tests."""
import unittest
import numpy as np
from phase1238_ah_actual_nav_stress_hedge import AHStressHedge,HEDGE


class TestAHStress(unittest.TestCase):
    def warm(self):
        s=AHStressHedge()
        for _ in range(48):
            self.assertTrue(np.all(s.step(10000.,0)==0))
        return s

    def test_drawdown_and_downside_confirmation(self):
        s=self.warm()
        x=s.step(8000.,-.20)
        self.assertTrue(np.array_equal(x,HEDGE))
        self.assertEqual(s.active_hours,1)

    def test_market_crash_without_nav_loss_no_hedge(self):
        s=self.warm()
        self.assertTrue(np.all(s.step(10000.,-.20)==0))

    def test_nav_loss_without_market_hazard_no_hedge(self):
        s=self.warm()
        self.assertTrue(np.all(s.step(8000.,0)==0))

    def test_exact_24_hour_recovery_hysteresis(self):
        s=self.warm()
        self.assertTrue(np.array_equal(s.step(8000.,-.20),HEDGE))
        for _ in range(23):
            self.assertTrue(np.array_equal(s.step(10000.,0),HEDGE))
        self.assertTrue(np.all(s.step(10000.,0)==0))
        self.assertEqual(s.active_hours,24)

    def test_skew_confirmation_without_negative_sum(self):
        s=AHStressHedge()
        for _ in range(47):s.step(10000.,.002)
        # Last-24h market sum remains positive, but skew is negative.
        self.assertTrue(np.array_equal(s.step(8000.,-.04),HEDGE))

    def test_future_perturbation_no_leakage(self):
        a=AHStressHedge();b=AHStressHedge()
        for t in range(100):
            nav=8000. if t==60 else 10000.
            ret=-.2 if t==60 else 0.
            x=a.step(nav,ret)
            y=b.step(nav if t<70 else 20000.,
                     ret if t<70 else .5)
            if t<70:self.assertTrue(np.array_equal(x,y))

    def test_invalid_nav_rejected(self):
        s=AHStressHedge()
        with self.assertRaisesRegex(ValueError,'NAV_OR_RETURN'):
            s.step(-1.,0.)


if __name__=='__main__':
    unittest.main()
