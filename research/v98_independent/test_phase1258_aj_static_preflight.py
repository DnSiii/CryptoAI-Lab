#!/usr/bin/env python3
"""V98 AJ1258 static pre-result causal and complete-system preflight."""
import itertools
import unittest
import numpy as np
from phase1255_aj_signed_sources import source_bundle
from phase1257_aj_open_viability_governor import FEES,ORDERS
from phase1258_aj_complete_180cell import (
    PATHS,CAPITAL,HOURS,WARMUP,fixture,prior_risk)

class TestAJPreflight(unittest.TestCase):
    def test_180_cell_cardinality(self):
        grid=list(itertools.product((False,True),PATHS,CAPITAL,FEES,ORDERS))
        self.assertEqual(len(grid),180)
        self.assertEqual(len(set(grid)),180)

    def test_causal_calendar(self):
        self.assertEqual(HOURS,900)
        self.assertEqual(WARMUP,720)
        self.assertEqual(HOURS-WARMUP,180)

    def test_crisis_open_gaps_are_real(self):
        o,h,l,c,q,r,e,ml,mh=fixture(True)
        for t in (810,850,870):
            np.testing.assert_array_equal(o[t],c[t])
        self.assertTrue(np.all(l<=np.minimum(o,c)))
        self.assertTrue(np.all(h>=np.maximum(o,c)))

    def test_prior_risk_does_not_see_future(self):
        a=fixture(False)
        b=list(fixture(False))
        b[1]=b[1].copy()
        b[1][850:]*=1.5
        x=prior_risk(a)
        y=prior_risk(b)
        for i in range(4):
            np.testing.assert_array_equal(x[i][:840],y[i][:840])

    def test_all_four_sources_active_somewhere(self):
        o,h,l,c,q,r,e,ml,mh=fixture(True)
        src=source_bundle(c,h,l,r,e)
        counts=[int(np.count_nonzero(np.abs(x[720:]).sum(axis=1)>1e-10))
                for x in src[:4]]
        print('AJ1258_SOURCE_ACTIVATION',counts)
        self.assertTrue(all(x>0 for x in counts))

    def test_future_source_invariance(self):
        a=fixture(True)
        b=[x.copy() for x in a]
        for k in (1,2,3):
            b[k][850:]*=1.3
        s1=source_bundle(a[3],a[1],a[2],a[5],a[6])
        s2=source_bundle(b[3],b[1],b[2],b[5],b[6])
        for k in range(4):
            np.testing.assert_array_equal(s1[k][:840],s2[k][:840])
        np.testing.assert_array_equal(s1[4]['state'][:840],
                                      s2[4]['state'][:840])

if __name__=='__main__':
    unittest.main()
