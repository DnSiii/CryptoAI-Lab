#!/usr/bin/env python3
"""AH1235 signed growth core causality, funding and deterministic tests."""
import unittest
import numpy as np
from phase1235_ah_signed_growth_core import ah_growth_source


class TestAHGrowth(unittest.TestCase):
    @staticmethod
    def fixture(n=400):
        t=np.arange(n,dtype=float)
        drift=np.array([.0008,-.0005,.0004,-.0001])
        c=100*np.exp(t[:,None]*drift+
            .004*np.sin(t[:,None]/np.array([11.,13.,17.,19.])))
        r=np.zeros_like(c);e=np.zeros_like(c)
        e[::8]=1.
        r[::8]=np.array([.0001,-.0001,.00015,-.00015])
        return c,r,e

    def test_signed_long_short_activity(self):
        c,r,e=self.fixture()
        a=ah_growth_source(c,r,e)
        self.assertEqual(a.shape,(400,4))
        self.assertTrue(np.all(a[:120]==0))
        self.assertGreater(int(np.count_nonzero(a>0)),0)
        self.assertGreater(int(np.count_nonzero(a<0)),0)
        self.assertTrue(np.all(np.abs(a).sum(axis=1)<=1+1e-12))

    def test_native_funding_sign_is_economic_input(self):
        c,r,e=self.fixture()
        a=ah_growth_source(c,r,e)
        r2=r.copy()
        r2[248,0]+=.30
        b=ah_growth_source(c,r2,e)
        self.assertFalse(np.array_equal(a[250],b[250]))
        self.assertTrue(np.array_equal(a[:248],b[:248]))

    def test_future_perturbation_no_leakage(self):
        c,r,e=self.fixture()
        a=ah_growth_source(c,r,e)
        c2=c.copy();r2=r.copy()
        c2[300:]*=np.array([2.,.2,3.,.4])
        r2[300:]*=100.
        b=ah_growth_source(c2,r2,e)
        self.assertTrue(np.array_equal(a[:300],b[:300]))

    def test_deterministic_repeat(self):
        c,r,e=self.fixture()
        self.assertTrue(np.array_equal(ah_growth_source(c,r,e),
                                       ah_growth_source(c,r,e)))

    def test_invalid_source_rejected(self):
        c,r,e=self.fixture()
        c[200,0]=-1
        with self.assertRaisesRegex(ValueError,'SOURCE_GEOMETRY'):
            ah_growth_source(c,r,e)


if __name__=='__main__':
    unittest.main()
