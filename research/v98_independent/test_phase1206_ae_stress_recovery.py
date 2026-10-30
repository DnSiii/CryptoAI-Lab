import unittest
import numpy as np
from phase1206_ae_stress_recovery import (
    AEStressMachine,RECOVERY_HOURS,HEDGE_GROSS)


class AEStressRecoveryTests(unittest.TestCase):
    def test_no_hedge_before_observed_stress(self):
        m=AEStressMachine()
        np.testing.assert_array_equal(m.step(100,0),np.zeros(4))
        np.testing.assert_array_equal(m.step(99,-.01),np.zeros(4))

    def test_actual_nav_drawdown_activates_next_open_target(self):
        m=AEStressMachine()
        m.step(100,0)
        h=m.step(87,-.001)
        np.testing.assert_array_equal(h,np.full(4,-.06))
        self.assertAlmostEqual(np.abs(h).sum(),HEDGE_GROSS)
        self.assertTrue(m.diagnostic()['active'])

    def test_market_crash_triggers_even_without_nav_drawdown(self):
        m=AEStressMachine()
        m.step(100,0)
        np.testing.assert_array_equal(m.step(100,-.031),np.full(4,-.06))

    def test_recovery_requires_exactly_48_completed_hours(self):
        m=AEStressMachine()
        m.step(100,0)
        m.step(86,-.01)
        for _ in range(RECOVERY_HOURS-1):
            np.testing.assert_array_equal(m.step(99,.001),np.full(4,-.06))
        np.testing.assert_array_equal(m.step(99,.001),np.zeros(4))
        self.assertFalse(m.diagnostic()['active'])

    def test_negative_recovery_hour_resets_counter(self):
        m=AEStressMachine()
        m.step(100,0)
        m.step(86,0)
        for _ in range(30):m.step(99,.001)
        self.assertEqual(m.diagnostic()['recovery_hours'],30)
        m.step(99,-.001)
        self.assertEqual(m.diagnostic()['recovery_hours'],0)
        for _ in range(47):m.step(99,.001)
        self.assertTrue(m.diagnostic()['active'])
        m.step(99,.001)
        self.assertFalse(m.diagnostic()['active'])

    def test_new_shock_resets_recovery(self):
        m=AEStressMachine()
        m.step(100,0)
        m.step(85,-.001)
        for _ in range(30):m.step(99,.001)
        m.step(99,-.04)
        self.assertEqual(m.diagnostic()['recovery_hours'],0)
        self.assertTrue(m.diagnostic()['active'])

    def test_sequential_future_invariance(self):
        a,b=AEStressMachine(),AEStressMachine()
        history=[(100,0),(97,-.005),(84,-.005)]+[(96,.001)]*20
        for nav,ret in history:
            np.testing.assert_array_equal(a.step(nav,ret),b.step(nav,ret))
        a.step(99,-.04)
        b.step(99,.002)
        self.assertNotEqual(a.diagnostic()['recovery_hours'],
                            b.diagnostic()['recovery_hours'])

    def test_fail_closed_invalid_inputs(self):
        for nav,ret in ((0,0),(-1,0),(float('nan'),0),
                        (100,float('inf')),(100,float('nan'))):
            with self.assertRaisesRegex(ValueError,'NONFINITE_OR_INSOLVENT'):
                AEStressMachine().step(nav,ret)

    def test_source_only_diagnostic(self):
        d=AEStressMachine().diagnostic()
        self.assertFalse(d['historical_system_pnl_computed'])
        self.assertFalse(d['validation_2025_read'])
        self.assertFalse(d['external_benchmarks_used'])


if __name__=='__main__':unittest.main()
