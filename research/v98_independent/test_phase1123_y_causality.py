#!/usr/bin/env python3
"""Y t-1 planning independence from next opening; synthetic only."""
import unittest
import numpy as np
from phase1123_y_continuous_feedback import max_safe_retention
P=np.ones(4)*100
D=np.ones(4)*.04
F=np.ones(4)*.0002
Q=np.ones(4)*1e9

class TestYCausality(unittest.TestCase):
    def test_next_open_cannot_change_precommitted_retention(self):
        u=np.array([44.9068,0,0,0]);cash=10000.-4490.68
        plans=[max_safe_retention(P,P*m,u,cash,D,D,F,Q,.002,.002)
               for m in (1.,1.0001,.9999)]
        self.assertEqual(len({p['planned_retention'] for p in plans}),1)
        self.assertTrue(plans[0]['ok'])
        self.assertTrue(plans[1]['ok'])
        self.assertFalse(plans[2]['ok'])
        self.assertEqual(plans[2]['reason'],'Y_UNEXPECTED_OPENING_RISK')
if __name__=='__main__':unittest.main()
