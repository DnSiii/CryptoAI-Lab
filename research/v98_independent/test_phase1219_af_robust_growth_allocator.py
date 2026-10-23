import unittest
import numpy as np
from phase1219_af_robust_growth_allocator import (
    AFGrowthAllocator,PRIOR,WINDOW,FEE)


def sleeves():
    return np.array([[.30,.25,.20,0.],
                     [0.,.20,0.,0.],
                     [.10,.05,0.,0.]])


def step(a,ret=None,rate=None,event=None,s=None,regime=None,reserve=.10):
    return a.step(np.zeros(4) if ret is None else ret,
                  np.zeros(4) if rate is None else rate,
                  np.zeros(4) if event is None else event,
                  sleeves() if s is None else s,
                  np.array([0.,1.,0.]) if regime is None else regime,
                  reserve)


class AFAllocatorTests(unittest.TestCase):
    def test_baseline_budget_before_336(self):
        a=AFGrowthAllocator()
        desired,budget=step(a)
        np.testing.assert_allclose(budget,PRIOR,atol=1e-14)
        self.assertTrue(np.all(desired>=0))

    def test_credible_growth_deploys_more_to_winning_sleeve(self):
        a=AFGrowthAllocator()
        for _ in range(WINDOW+4):
            desired,budget=step(a,ret=np.array([.003,-.002,.002,0.]))
        self.assertGreater(budget[0],PRIOR[0])
        self.assertLess(budget[1],PRIOR[1])

    def test_previous_holdings_native_funding_and_turnover(self):
        a=AFGrowthAllocator()
        step(a)
        step(a,rate=np.array([.01,0,0,0]),event=np.array([1,0,0,0]))
        self.assertAlmostEqual(a.last_realized[0],-.30*.01-FEE*.75,places=12)

    def test_new_intent_does_not_change_current_realized(self):
        a,b=AFGrowthAllocator(),AFGrowthAllocator()
        step(a)
        step(b)
        changed=sleeves()
        changed[0]=0
        step(a,ret=np.array([.001,0,0,0]))
        step(b,ret=np.array([.001,0,0,0]),s=changed)
        np.testing.assert_array_equal(a.last_realized,b.last_realized)

    def test_cash_reserve_enforced_without_shorting(self):
        a=AFGrowthAllocator()
        d,b=step(a,reserve=.55)
        self.assertLessEqual(d.sum(),.45+1e-12)
        self.assertTrue(np.all(d>=0))
        self.assertAlmostEqual(d.sum(),.45,places=10)

    def test_router_shifts_growth_deployment(self):
        off=step(AFGrowthAllocator(),regime=np.array([1.,0.,0.]))[1]
        on=step(AFGrowthAllocator(),regime=np.array([0.,0.,1.]))[1]
        self.assertLess(off[0],on[0])
        self.assertAlmostEqual(off.sum(),1.)
        self.assertAlmostEqual(on.sum(),1.)

    def test_fixed_window_and_reproducibility(self):
        a,b=AFGrowthAllocator(),AFGrowthAllocator()
        for _ in range(400):
            x=step(a,ret=np.array([.001,-.001,.0005,0.]))
            y=step(b,ret=np.array([.001,-.001,.0005,0.]))
            np.testing.assert_array_equal(x[0],y[0])
            np.testing.assert_array_equal(x[1],y[1])
        self.assertEqual(a.diagnostic()['window_hours'],WINDOW)

    def test_invalid_funding_mask_and_reserve_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'COMPLETED_INPUT'):
            step(AFGrowthAllocator(),rate=np.array([.01,0,0,0]))
        with self.assertRaisesRegex(ValueError,'COMPLETED_INPUT'):
            step(AFGrowthAllocator(),reserve=.33)

    def test_no_historical_claims(self):
        d=AFGrowthAllocator().diagnostic()
        self.assertFalse(d['historical_system_pnl_computed'])
        self.assertFalse(d['validation_2025_read'])
        self.assertFalse(d['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
