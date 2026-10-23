#!/usr/bin/env python3
"""V98 AH1243 preregistered PRE-RESULT static integration audit, no PnL."""
import unittest
import numpy as np
from phase1243_ah_complete_180cell import (
    fixture,source_bundle,prior_bounds,PATHS,CAPITAL,FEE_MODES,ORDERS,
    WARMUP,HOURS)

class TestAHStaticPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=fixture(False)
        cls.slots=source_bundle(cls.frames)
        cls.risk=prior_bounds(cls.frames)

    def test_complete_cardinality(self):
        self.assertEqual(2*len(PATHS)*len(CAPITAL)*len(FEE_MODES)*len(ORDERS),180)
        self.assertEqual(HOURS-WARMUP,180)
    def test_synthetic_shocks_immutable(self):
        benign=fixture(False);crisis=fixture(True)
        b,c=benign[3],crisis[3]
        np.testing.assert_allclose(c[809]/b[809],np.ones(4))
        np.testing.assert_allclose(c[810]/b[810],np.full(4,.55))
        np.testing.assert_allclose(c[850]/b[850],np.full(4,.99))
        self.assertAlmostEqual(c[870,3]/b[870,3],.396)
    def test_all_sources_shape_and_activation(self):
        growth,op,rv,router=self.slots
        for s in (growth,op,rv):
            self.assertEqual(s.shape,(HOURS,4))
            self.assertTrue(np.isfinite(s).all())
        self.assertGreater(np.count_nonzero(op[WARMUP:]),0,
            'preregistered opportunity fixture must excite sleeve')
        self.assertGreater(np.count_nonzero(rv[WARMUP:]),0)
        self.assertEqual(len(router['state']),HOURS)
    def test_prior_only_bounds(self):
        d,u,f,qmin=self.risk
        self.assertTrue(np.all(d[WARMUP:]>=.45))
        self.assertTrue(np.all(u[WARMUP:]>=.8))
        self.assertTrue(np.all(f[WARMUP:]>=.0005))
        self.assertTrue(np.all(qmin[WARMUP:]>0))
    def test_future_perturbation_invariance(self):
        o,h,l,c,q,r,e,ml,mh=self.frames
        j=760
        c2=c.copy();h2=h.copy();l2=l.copy()
        c2[j+1:]*=2.;h2[j+1:]*=2.;l2[j+1:]*=2.
        b=source_bundle((o,h2,l2,c2,q,r,e,ml,mh))
        for k in range(3):
            np.testing.assert_allclose(self.slots[k][:j+1],b[k][:j+1],atol=0,rtol=0)
        np.testing.assert_array_equal(self.slots[3]['state'][:j+1],b[3]['state'][:j+1])

if __name__=='__main__':unittest.main()
