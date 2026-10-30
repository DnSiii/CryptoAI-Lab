import unittest
import numpy as np
from test_phase1214_af_dual_ewma_core import sample
from phase1215_af_synchronized_acceleration import (
    af_opportunity_source,BASELINE,LOOKBACK,HOLD)


def shocked(two=True):
    f=[x.copy() for x in sample(900)]
    c=f[3].to_numpy(copy=True)
    c[600:,0]*=1.05
    if two:c[600:,1]*=1.04
    o=np.vstack((c[0],c[:-1]))
    hi=np.maximum(o,c)*1.0003
    lo=np.minimum(o,c)*.9997
    for k,a in ((0,o),(1,hi),(2,lo),(3,c)):
        f[k].iloc[:]=a
    return f


class AFAccelerationOpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=shocked()
        cls.out=af_opportunity_source(*cls.f)

    def test_strict_342h_baseline(self):
        self.assertTrue(np.all(self.out[:BASELINE+LOOKBACK]==0))

    def test_two_asset_coacceleration_activates(self):
        self.assertGreater(self.out[600,0],0)
        self.assertGreater(self.out[600,1],0)
        self.assertAlmostEqual(self.out[600].sum(),.20,places=12)

    def test_single_asset_shock_not_confirmed(self):
        out=af_opportunity_source(*shocked(two=False))
        self.assertTrue(np.all(out[600:610]==0))

    def test_fixed_12h_persistence_and_expiry(self):
        self.assertTrue(np.all(self.out[606:617].sum(axis=1)>0))
        self.assertEqual(self.out[617].sum(),0)

    def test_future_shock_cannot_change_previous_decisions(self):
        plain=af_opportunity_source(*sample(900))
        np.testing.assert_array_equal(self.out[:600],plain[:600])

    def test_current_quote_cannot_change_current_trigger(self):
        f=[x.copy() for x in self.f]
        f[4].iloc[600,0]=0
        out=af_opportunity_source(*f)
        np.testing.assert_array_equal(self.out[:601],out[:601])
        self.assertFalse(np.array_equal(self.out[612:617],out[612:617]))

    def test_no_short_or_gross_excess(self):
        self.assertTrue(np.all(self.out>=0))
        self.assertLessEqual(self.out.sum(axis=1).max(),.20+1e-10)

    def test_deterministic_reproduction(self):
        np.testing.assert_array_equal(self.out,af_opportunity_source(*self.f))


if __name__=='__main__':unittest.main()
