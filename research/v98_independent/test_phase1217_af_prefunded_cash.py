import unittest
from phase1217_af_prefunded_cash import (
    AFCashStress,NORMAL_CASH,STRESS_CASH,RECOVERY_HOURS)


class AFCashStressTests(unittest.TestCase):
    def test_normal_cash_keeps_growth_participation(self):
        m=AFCashStress()
        self.assertEqual(m.step(100,0),NORMAL_CASH)
        self.assertEqual(m.step(99,-.01),NORMAL_CASH)

    def test_actual_nav_drawdown_prefunds_cash(self):
        m=AFCashStress()
        m.step(100,0)
        self.assertEqual(m.step(84,-.01),STRESS_CASH)

    def test_market_shock_triggers_next_open_reserve(self):
        m=AFCashStress()
        m.step(100,0)
        self.assertEqual(m.step(100,-.051),STRESS_CASH)

    def test_recovery_requires_exactly_24_completed_hours(self):
        m=AFCashStress()
        m.step(100,0)
        m.step(84,-.01)
        for _ in range(RECOVERY_HOURS-1):
            self.assertEqual(m.step(95,.001),STRESS_CASH)
        self.assertEqual(m.step(95,.001),NORMAL_CASH)

    def test_negative_recovery_hour_resets_counter(self):
        m=AFCashStress()
        m.step(100,0)
        m.step(84,-.01)
        for _ in range(10):m.step(95,.001)
        self.assertEqual(m.diagnostic()['recovery_hours'],10)
        m.step(95,-.001)
        self.assertEqual(m.diagnostic()['recovery_hours'],0)
        for _ in range(23):self.assertEqual(m.step(95,.001),STRESS_CASH)
        self.assertEqual(m.step(95,.001),NORMAL_CASH)

    def test_future_shock_cannot_change_prior_targets(self):
        a,b=AFCashStress(),AFCashStress()
        for nav,ret in ((100,0),(99,-.01),(98,.001)):
            self.assertEqual(a.step(nav,ret),b.step(nav,ret))
        self.assertNotEqual(a.step(90,-.06),b.step(98,.001))

    def test_fail_closed_insolvency_and_nan(self):
        for nav,ret in ((0,0),(-1,0),(float('nan'),0),
                        (100,float('inf'))):
            with self.assertRaisesRegex(ValueError,'NONFINITE_OR_INSOLVENT'):
                AFCashStress().step(nav,ret)

    def test_source_only_diagnostic(self):
        d=AFCashStress().diagnostic()
        self.assertFalse(d['historical_system_pnl_computed'])
        self.assertFalse(d['validation_2025_read'])
        self.assertFalse(d['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
