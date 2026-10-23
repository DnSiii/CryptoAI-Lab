import unittest
import numpy as np
from test_phase1214_af_dual_ewma_core import sample
from phase1218_af_breadth_router import af_router_source,WARMUP


def quiet():
    f=[x.copy() for x in sample(900)]
    f[5].iloc[:]=0
    return f


def crash():
    f=quiet()
    c=f[3].to_numpy(copy=True)
    c[600:]*=.55
    o=np.vstack((c[0],c[:-1]))
    hi=np.maximum(o,c)*1.0003
    lo=np.minimum(o,c)*.9997
    for k,a in ((0,o),(1,hi),(2,lo),(3,c)):
        f[k].iloc[:]=a
    return f


class AFBreadthRouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=quiet()
        cls.out=af_router_source(*cls.f)

    def test_warmup_transition_and_one_hot(self):
        self.assertTrue(np.all(self.out[:WARMUP,1]==1))
        np.testing.assert_array_equal(self.out.sum(axis=1),np.ones(900))

    def test_six_completed_on_hours_required(self):
        self.assertEqual(self.out[340,1],1)
        self.assertEqual(self.out[341,2],1)

    def test_sharp_market_crash_immediately_risk_off(self):
        r=af_router_source(*crash())
        self.assertEqual(r[600,0],1)
        self.assertEqual(r[601,0],1)
        np.testing.assert_array_equal(self.out[:600],r[:600])

    def test_crash_recovery_waits_for_vol_window_and_streak(self):
        r=af_router_source(*crash())
        self.assertEqual(r[670,0],1)
        self.assertEqual(r[677,2],1)

    def test_signed_funding_stress_at_completed_event(self):
        f=quiet()
        f[5].iloc[600,0]=.02
        r=af_router_source(*f)
        np.testing.assert_array_equal(self.out[:600],r[:600])
        self.assertEqual(r[600,0],1)

    def test_current_quote_cannot_change_current_router(self):
        f=quiet()
        f[4].iloc[600,0]=0
        r=af_router_source(*f)
        np.testing.assert_array_equal(self.out[:601],r[:601])
        self.assertEqual(r[601,0],1)

    def test_deterministic_reproduction(self):
        np.testing.assert_array_equal(self.out,af_router_source(*self.f))


if __name__=='__main__':unittest.main()
