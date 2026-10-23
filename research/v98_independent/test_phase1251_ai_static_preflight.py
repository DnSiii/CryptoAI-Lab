#!/usr/bin/env python3
"""V98 AI1251 PRE-RESULT complete-system static wiring and causal tests."""
import unittest
import numpy as np
from phase1251_ai_complete_180cell import (
    fixture,prior_risk,PATHS,CAPITAL,FEES,ORDERS,HOURS,WARMUP)
from phase1247_ai_four_signed_sources import source_bundle

class TestAIStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benign=fixture(False)
        cls.crisis=fixture(True)
        cls.b=source_bundle(cls.benign[3],cls.benign[1],cls.benign[2],
            cls.benign[5],cls.benign[6])
        cls.s=source_bundle(cls.crisis[3],cls.crisis[1],cls.crisis[2],
            cls.crisis[5],cls.crisis[6])
    def test_180_cells(self):
        self.assertEqual(2*len(PATHS)*len(CAPITAL)*len(FEES)*len(ORDERS),180)
        self.assertEqual(HOURS-WARMUP,180)
    def test_exact_crisis_shocks(self):
        b=self.benign[3];c=self.crisis[3]
        np.testing.assert_allclose(c[809]/b[809],np.ones(4))
        np.testing.assert_allclose(c[810]/b[810],np.full(4,.55))
        np.testing.assert_allclose(c[850]/b[850],np.full(4,.99))
        self.assertAlmostEqual(c[870,3]/b[870,3],.396)
    def test_sources_active(self):
        for a in self.s[:4]:
            self.assertEqual(a.shape,(HOURS,4))
            self.assertTrue(np.isfinite(a).all())
        self.assertGreater(np.count_nonzero(self.s[1][WARMUP:]),0)
        self.assertGreater(np.count_nonzero(self.s[2][WARMUP:]),0)
        self.assertGreater(np.count_nonzero(self.s[3][WARMUP:]),0)
    def test_prior_only_risk(self):
        d,u,f,qmin=prior_risk(self.crisis)
        self.assertTrue(np.all(d[WARMUP:]>=.45))
        self.assertTrue(np.all(u[WARMUP:]>=.80))
        self.assertTrue(np.all(f[WARMUP:]>=.0005))
        self.assertTrue(np.all(qmin[WARMUP:]>0))
    def test_future_perturbation(self):
        o,h,l,c,q,r,e,ml,mh=self.benign
        j=760
        c2=c.copy();h2=h.copy();l2=l.copy()
        c2[j+1:]*=1.6;h2[j+1:]*=1.6;l2[j+1:]*=1.6
        b=source_bundle(c2,h2,l2,r,e)
        for i in range(4):
            np.testing.assert_array_equal(self.b[i][:j+1],b[i][:j+1])
        np.testing.assert_array_equal(self.b[4]['state'][:j+1],b[4]['state'][:j+1])

if __name__=='__main__':unittest.main()
