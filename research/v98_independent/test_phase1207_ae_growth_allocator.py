import unittest
import numpy as np
from phase1207_ae_growth_allocator import (
    AEAllocator,PRIOR,HISTORY,VIRTUAL_FEE,valid_sleeves)


def sleeves():
    return np.array([[.30,.20,.15,0.],
                     [0.,.12,0.,0.],
                     [.10,-.10,0.,0.],
                     [-.06,-.06,-.06,-.06]],dtype=float)


def step(a,ret=None,rate=None,event=None,s=None,regime=None):
    return a.step(np.zeros(4) if ret is None else ret,
                  np.zeros(4) if rate is None else rate,
                  np.zeros(4) if event is None else event,
                  sleeves() if s is None else s,
                  np.array([0.,1.,0.]) if regime is None else regime)


class AEGrowthAllocatorTests(unittest.TestCase):
    def test_prior_budget_before_full_history(self):
        a=AEAllocator()
        desired,budget=step(a)
        np.testing.assert_allclose(budget,PRIOR,atol=1e-14)
        self.assertEqual(desired.shape,(4,))
        self.assertAlmostEqual(budget.sum(),1.)

    def test_positive_net_growth_changes_budget_after_336(self):
        a=AEAllocator()
        for _ in range(HISTORY+5):
            desired,budget=step(a,ret=np.array([.003,-.002,.001,0.]))
        self.assertGreater(budget[0],PRIOR[0])
        self.assertLess(budget[1],PRIOR[1])
        self.assertLessEqual(np.abs(desired).sum(),.65+1e-9)

    def test_previous_holdings_only_and_funding_sign(self):
        a=AEAllocator()
        step(a)
        step(a,rate=np.array([.01,0,0,0]),event=np.array([1,0,0,0]))
        expected=-.30*.01 - VIRTUAL_FEE*.65
        self.assertAlmostEqual(a.last_realized[0],expected,places=12)

    def test_future_sleeve_cannot_change_current_realized(self):
        a,b=AEAllocator(),AEAllocator()
        step(a)
        step(b)
        s=sleeves()
        changed=s.copy()
        changed[0]=0
        step(a,ret=np.array([.001,0,0,0]),s=s)
        step(b,ret=np.array([.001,0,0,0]),s=changed)
        np.testing.assert_array_equal(a.last_realized,b.last_realized)
        self.assertFalse(np.array_equal(a.prev,b.prev))

    def test_three_regimes_have_distinct_causal_budgets(self):
        budgets=[]
        for regime in (np.array([1.,0.,0.]),np.array([0.,1.,0.]),
                       np.array([0.,0.,1.])):
            a=AEAllocator()
            budgets.append(step(a,regime=regime)[1])
        self.assertTrue(all(abs(b.sum()-1)<1e-12 for b in budgets))
        self.assertLess(budgets[0][0],budgets[2][0])
        self.assertGreater(budgets[0][3],budgets[2][3])

    def test_fixed_window_and_determinism(self):
        a,b=AEAllocator(),AEAllocator()
        for _ in range(400):
            x=step(a,ret=np.array([.001,-.001,.0005,0.]))
            y=step(b,ret=np.array([.001,-.001,.0005,0.]))
            np.testing.assert_array_equal(x[0],y[0])
            np.testing.assert_array_equal(x[1],y[1])
        self.assertEqual(a.diagnostic()['window_hours'],HISTORY)

    def test_reject_unbalanced_rv_and_overbudget(self):
        s=sleeves()
        s[2]=[.10,0,0,0]
        with self.assertRaisesRegex(ValueError,'SLEEVE_BUDGET'):
            step(AEAllocator(),s=s)
        s=sleeves()
        s[0]=[.70,0,0,0]
        with self.assertRaisesRegex(ValueError,'SLEEVE_BUDGET'):
            step(AEAllocator(),s=s)

    def test_reject_invalid_event_and_regime(self):
        with self.assertRaisesRegex(ValueError,'COMPLETED_INPUT'):
            step(AEAllocator(),rate=np.array([.01,0,0,0]))
        with self.assertRaisesRegex(ValueError,'COMPLETED_INPUT'):
            step(AEAllocator(),regime=np.array([.5,.5,0.]))

    def test_no_historical_claims(self):
        d=AEAllocator().diagnostic()
        self.assertFalse(d['historical_system_pnl_computed'])
        self.assertFalse(d['validation_2025_read'])
        self.assertFalse(d['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
