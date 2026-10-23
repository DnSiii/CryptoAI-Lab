#!/usr/bin/env python3
"""Independent AG1226 atomic feasibility, cost, no-leverage and reproducibility tests."""
import unittest
import numpy as np
from phase1226_ag_atomic_portfolio import (joint_plan, corner_audit,
    CORNERS, COSTS, ORDER_SHARE, EQUITY_FLOOR)


class TestAGJoint(unittest.TestCase):
    def setUp(self):
        self.p = np.array([100., 150., 50., 200.])
        self.d = np.array([.40, .35, .45, .30])
        self.u = np.array([.30, .30, .35, .30])
        self.f = np.full(4, .004)
        self.q = np.full(4, 1e12)
        self.mu = np.array([.04, .035, .025, .03])

    def solve(self, old=None, cash=10000., mode='base', q=None, mu=None):
        if old is None: old=np.zeros(4)
        return joint_plan(old,self.p,cash,self.mu if mu is None else mu,
                          self.d,self.u,self.f,self.q if q is None else q,
                          self.q,mode)

    def test_cash_and_open_equity_reconciliation(self):
        r=self.solve()
        old=np.zeros(4)
        fee,slip=COSTS['base']
        turn=float(np.sum(np.abs(r['units']*self.p-old*self.p)))
        self.assertAlmostEqual(r['cash']+r['units']@self.p+(fee+slip)*turn,
                               10000.,places=6)
        self.assertTrue(r['jointly_feasible'])
        self.assertTrue(np.all(r['units']>=0))
        self.assertGreater(r['units'].sum(),0.)

    def test_joint_atomic_rebalances_carried_concentration(self):
        # AF's rejected post-sell intermediate state is never constructed.
        old=np.array([85.,0.,0.,0.])
        r=self.solve(old,cash=1500.)
        self.assertLess(r['units'][0],old[0])
        self.assertAlmostEqual(r['cash']+r['units']@self.p+
            .001*np.abs((r['units']-old)*self.p).sum(),10000.,places=5)
        self.assertTrue(r['jointly_feasible'])

    def test_no_imaginary_exit_capacity(self):
        old=np.array([85.,0.,0.,0.])
        with self.assertRaisesRegex(ValueError,'NO_JOINT_FEASIBLE'):
            self.solve(old,cash=1500.,q=np.zeros(4))

    def test_fee_stress_all_modes(self):
        for fee in COSTS:
            r=self.solve(mode=fee)
            self.assertGreaterEqual(r['cash'],-1e-8)
            self.assertLessEqual(np.sum(r['posttrade_weights']),.91)
            self.assertTrue(np.all(r['posttrade_weights']<=.37))
            self.assertTrue(r['jointly_feasible'])

    def test_future_exit_reserve(self):
        qmin=np.array([3000.,4000.,5000.,6000.])
        r=joint_plan(np.zeros(4),self.p,10000.,self.mu,
                     self.d,self.u,self.f,self.q,qmin)
        self.assertTrue(np.all(r['units']*self.p*(1+self.u)*2.2 <=
                               ORDER_SHARE*qmin+1e-6))

    def test_actual_cash_reserve_is_binding(self):
        r=joint_plan(np.zeros(4),self.p,10000.,self.mu,
                     self.d,self.u,self.f,self.q,self.q,
                     cash_floor=.45)
        self.assertGreaterEqual(r['cash'],4500.-1e-5)
        self.assertLessEqual(np.sum(r['posttrade_weights']),.55+1e-5)

    def test_crisis_gap_joint_liquidation(self):
        old=np.array([18.,10.,25.,8.])
        p=self.p*np.array([.55,.55,.55,.55])
        r=joint_plan(old,p,1800.,self.mu,np.full(4,.55),
                     np.full(4,.85),self.f,self.q,self.q)
        self.assertTrue(r['jointly_feasible'])
        self.assertGreaterEqual(r['cash'],-1e-8)

    def test_reproducibility(self):
        a=self.solve()
        b=self.solve()
        self.assertTrue(np.array_equal(a['units'],b['units']))
        self.assertEqual(a['cash'],b['cash'])

    def test_adversarial_randomized_portfolios(self):
        rng=np.random.default_rng(1226)
        passes=0
        for _ in range(100):
            cash=float(rng.uniform(5000.,15000.))
            d=rng.uniform(.15,.55,4)
            u=rng.uniform(.10,.80,4)
            mu=rng.uniform(-.03,.06,4)
            r=joint_plan(np.zeros(4),self.p,cash,mu,d,u,self.f,self.q,self.q)
            self.assertTrue(r['jointly_feasible'])
            self.assertGreaterEqual(r['cash'],-1e-7)
            self.assertTrue(np.all(np.isfinite(r['units'])))
            passes+=1
        self.assertEqual(passes,100)

if __name__=='__main__':
    unittest.main()
