#!/usr/bin/env python3
"""V98 AJ1256/1257 preregistered growth and executable viability tests."""
import unittest
import numpy as np
from phase1256_aj_wealth_allocator import AJWealthAllocator
from phase1257_aj_open_viability_governor import (
    aj_governor,future_safe,FEES)

class TestAJAllocator(unittest.TestCase):
    def test_no_lookahead_warmup(self):
        a=AJWealthAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        self.assertEqual(a.decide(s,'TREND')['growth_scale'],0.)

    def test_no_artificial_growth_scale_ceiling(self):
        a=AJWealthAllocator()
        a.previous[0,0]=1.
        for _ in range(168):
            a.observe(np.array([.01,0.,0.,0.]),np.zeros(4),np.zeros(4))
        s=np.zeros((4,4));s[0,0]=1.
        out=a.decide(s,'TREND')
        self.assertGreater(out['growth_scale'],4.)
        self.assertGreater(out['signed_target'][0],1.)

    def test_negative_edge_is_flat(self):
        a=AJWealthAllocator()
        a.previous[0,0]=1.
        for _ in range(168):
            a.observe(np.array([-.01,0.,0.,0.]),np.zeros(4),np.zeros(4))
        s=np.zeros((4,4));s[0,0]=1.
        self.assertEqual(a.decide(s,'TREND')['growth_scale'],0.)

    def test_regime_priors(self):
        a=AJWealthAllocator()
        s=np.zeros((4,4))
        self.assertGreater(a.decide(s,'CRISIS')['weights'][3],
                           a.decide(s,'TREND')['weights'][3])

    def test_cost_and_native_funding(self):
        a=AJWealthAllocator()
        a.previous[0,0]=1.
        a.pending_cost[0]=.0015
        paper=a.observe(np.array([.01,0,0,0]),
                        np.array([.001,0,0,0]),
                        np.array([1,0,0,0]))
        self.assertAlmostEqual(paper[0],.0075)

    def test_invalid(self):
        a=AJWealthAllocator()
        with self.assertRaises(ValueError):
            a.decide(np.zeros((3,4)),'TREND')

class TestAJGovernor(unittest.TestCase):
    def kwargs(self):
        return dict(cash_previous=10000.,old_units=np.zeros(4),
                    prior_close=np.full(4,100.),opening=np.full(4,100.),
                    signed_target=np.array([100.,-100.,50.,-50.]),
                    prior_down=np.full(4,.45),prior_up=np.full(4,.8),
                    funding_bound=np.full(4,.0005),
                    prior_quote=np.full(4,1e8),
                    min_quote=np.full(4,1e8))

    def test_funded_open_governed(self):
        k=self.kwargs()
        out=aj_governor(**k)
        self.assertTrue(out['future_safe'])
        self.assertTrue(out['real_open_solvent'])
        self.assertFalse(out['hidden_borrow'])
        self.assertTrue(np.isfinite(out['units']).all())
        self.assertGreater(np.abs(out['units']).sum(),0.)

    def test_severe_cost_cannot_increase_feasible_gross(self):
        k=self.kwargs()
        base=aj_governor(**k,fee_mode='base')['units']
        severe=aj_governor(**k,fee_mode='supersevere')['units']
        self.assertLessEqual(np.abs(severe).sum(),
                             np.abs(base).sum()+1e-7)

    def test_real_gap_bankruptcy(self):
        k=self.kwargs()
        k['old_units']=np.array([-100.,0,0,0])
        k['opening']=np.array([250.,100,100,100])
        with self.assertRaisesRegex(ValueError,'GAP_BANKRUPTCY'):
            aj_governor(**k)

    def test_actual_open_controlled_reduction(self):
        k=self.kwargs()
        k['old_units']=np.array([-75.,0,0,0])
        k['signed_target']=np.zeros(4)
        k['prior_quote']=np.full(4,1e6)
        k['min_quote']=np.full(4,1e7)
        out=aj_governor(**k)
        self.assertTrue(out['controlled_reduction'])
        self.assertLess(abs(out['units'][0]),75.)

    def test_unreachable_exit_rejected(self):
        k=self.kwargs()
        k['old_units']=np.array([-75.,0,0,0])
        k['signed_target']=np.zeros(4)
        k['prior_quote']=np.full(4,100.)
        k['min_quote']=np.full(4,1e7)
        with self.assertRaisesRegex(ValueError,'NO_REACHABLE'):
            aj_governor(**k)

    def test_extreme_risk_false(self):
        self.assertFalse(future_safe(100.,np.array([10.,0,0,0]),
            np.full(4,100.),np.full(4,.45),np.full(4,.8),
            np.full(4,.0005),.01,100.,100.))

    def test_invalid_fee(self):
        k=self.kwargs()
        with self.assertRaises(ValueError):
            aj_governor(**k,fee_mode='unknown')

if __name__=='__main__':
    unittest.main()
