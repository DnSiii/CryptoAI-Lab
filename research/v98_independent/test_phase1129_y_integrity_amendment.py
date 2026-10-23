#!/usr/bin/env python3
"""Phase1129 Y pre-economic signed-beta, stop reserve and zero-event proof."""
import unittest
import numpy as np
from phase1125_y_sevenslot_source import beta_neutral_pair
from phase1128_y_funding_reserve_audit import audit
from test_phase1126_y_hourly_ledger import run

class TestYFormalAmendment(unittest.TestCase):
    def test_positive_signed_betas_cancel(self):
        w=beta_neutral_pair(1.2,.8)
        self.assertIsNotNone(w)
        self.assertAlmostEqual(w[0]*1.2+w[1]*.8,0.,places=12)
        self.assertLess(w[0],0.);self.assertGreater(w[1],0.)
    def test_negative_signed_betas_cancel(self):
        w=beta_neutral_pair(-2.,-.5)
        self.assertIsNotNone(w)
        self.assertAlmostEqual(w[0]*-2.+w[1]*-.5,0.,places=12)
    def test_opposite_or_zero_beta_skipped(self):
        for a,b in ((-2.,1.),(2.,-1.),(0.,1.),(1.,0.)):
            self.assertIsNone(beta_neutral_pair(a,b))
    def test_funding_reserve_floor_fails_closed(self):
        x=audit()
        self.assertTrue(x['correctly_rejected'])
        self.assertFalse(x['uncertified_exit'])
        self.assertLess(x['source_exit'],x['floor'])
        self.assertGreater(x['original_unreserved_exit'],x['floor'])
    def test_noop_is_not_an_execution(self):
        x=run()
        self.assertTrue(x['ok'])
        self.assertEqual(x['events'],[])
        self.assertEqual(x['turnover'],0.)
if __name__=='__main__':unittest.main()
