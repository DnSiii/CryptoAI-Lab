import unittest
import numpy as np
from test_phase1189_ad_online_core_router import sample
from phase1193_ad_stateful_stress import stress_targets


def fixture(n=1000):
    f=sample(n)
    close=f[3].to_numpy(copy=True)
    close[800:]*=.85
    close[840:]*=1.15
    op=np.vstack([close[0],close[:-1]])
    hi=np.maximum(close,op)*1.003
    lo=np.minimum(close,op)*.997
    for k,a in ((0,op),(1,hi),(2,lo),(3,close)):
        f[k].iloc[:]=a
    nav=np.full(n,10000.)
    nav[800:]=8500.
    nav[808:]=7500.
    nav[840:]=9600.
    return f,nav


class StressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f,cls.nav=fixture()
        cls.out,cls.diag=stress_targets(*cls.f,cls.nav,diagnostics=True)

    def test_trigger_and_no_premature_signal(self):
        self.assertTrue((self.out[:800]==0).all())
        self.assertAlmostEqual(float(np.abs(self.out[800]).sum()),.15,places=9)

    def test_escalation_and_no_early_unwind(self):
        self.assertAlmostEqual(float(np.abs(self.out[808]).sum()),.30,places=9)
        self.assertTrue((self.out[808:824]<0).all())

    def test_recovery_unwinds_demand(self):
        self.assertTrue((self.out[840]==0).all())
        self.assertGreaterEqual(self.diag['recoveries'],1)

    def test_no_assumed_fill_or_pnl(self):
        self.assertFalse(self.diag['actual_exit_execution_proven'])
        self.assertFalse(self.diag['historical_system_pnl_computed'])
        self.assertFalse(self.diag['validation_2025_read'])

    def test_prefix_causality(self):
        nav=self.nav.copy()
        nav[900:]*=.7
        out=stress_targets(*self.f,nav)
        np.testing.assert_array_equal(self.out[:900],out[:900])

    def test_future_extension(self):
        f,nav=fixture(1200)
        out=stress_targets(*f,nav)
        np.testing.assert_array_equal(self.out,out[:1000])

    def test_invalid_nav_rejected(self):
        nav=self.nav.copy();nav[900]=0
        with self.assertRaisesRegex(ValueError,'NAV_INVALID'):
            stress_targets(*self.f,nav)


if __name__=='__main__':unittest.main()
