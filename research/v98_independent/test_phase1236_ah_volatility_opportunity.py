#!/usr/bin/env python3
"""AH1236 signed opportunity breakout, hold, causality and geometry tests."""
import unittest
import numpy as np
from phase1236_ah_volatility_opportunity import ah_opportunity_source


class TestAHOpportunity(unittest.TestCase):
    @staticmethod
    def fixture(n=400):
        t=np.arange(n,dtype=float)
        c=100*np.exp(t[:,None]*np.array([.0001,.0001,.0001,.0001]))
        c[250:,0]=c[249,0]*1.30
        c[300:,1]=c[299,1]*.65
        opening=np.vstack((c[0],c[:-1]))
        h=np.maximum(opening,c)*1.0001
        l=np.minimum(opening,c)*.9999
        return c,h,l

    def test_long_short_activation(self):
        c,h,l=self.fixture()
        a=ah_opportunity_source(c,h,l)
        self.assertEqual(a.shape,(400,4))
        self.assertTrue(np.all(a[:120]==0))
        self.assertGreater(a[250,0],0)
        self.assertLess(a[300,1],0)
        self.assertTrue(np.all(np.abs(a).sum(axis=1)<=1+1e-12))

    def test_exact_twelve_hour_expiry(self):
        c,h,l=self.fixture()
        a=ah_opportunity_source(c,h,l)
        self.assertGreater(a[250,0],0)
        self.assertGreater(a[261,0],0)
        self.assertEqual(a[262,0],0)
        self.assertLess(a[311,1],0)
        self.assertEqual(a[312,1],0)

    def test_future_perturbation_invariance(self):
        c,h,l=self.fixture()
        a=ah_opportunity_source(c,h,l)
        c2=c.copy();h2=h.copy();l2=l.copy()
        c2[350:]*=np.array([.5,2.,3.,.2])
        h2[350:]=np.maximum(h2[350:],c2[350:])
        l2[350:]=np.minimum(l2[350:],c2[350:])
        b=ah_opportunity_source(c2,h2,l2)
        self.assertTrue(np.array_equal(a[:350],b[:350]))

    def test_no_current_high_used_as_signal(self):
        c,h,l=self.fixture()
        a=ah_opportunity_source(c,h,l)
        h2=h.copy();h2[250]*=1.5
        b=ah_opportunity_source(c,h2,l)
        self.assertTrue(np.array_equal(a[:251],b[:251]))

    def test_bad_geometry_rejected(self):
        c,h,l=self.fixture()
        l[250,0]=c[250,0]*1.01
        with self.assertRaisesRegex(ValueError,'SOURCE_GEOMETRY'):
            ah_opportunity_source(c,h,l)


if __name__=='__main__':
    unittest.main()
