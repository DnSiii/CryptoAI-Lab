#!/usr/bin/env python3
"""AC pre-economic signed funding, t+1 cash ledger, gap and capacity tests."""
import unittest
import numpy as np
from phase1177_ac_actual_open_executor import execute_hour, funding_cash, intrabar


def case(**kwargs):
    p = np.full(4, 100.)
    base = dict(prior=p, opening=p, high=p * 1.01, low=p * .99,
                closing=p, cash=10000., old_units=np.zeros(4),
                scores=np.array([4, 0, 0, 0]), cov24=np.eye(4)*.001,
                down=np.full(4, .2), up=np.full(4, .2),
                funding_bound=np.full(4, .0001), prior_quote=np.full(4, 1e8),
                min336_quote=np.full(4, 1e8), fee=.0007,
                funding_rate=np.zeros(4), mark_bounds=np.full((4, 2), np.nan),
                funding_event=np.zeros(4, bool))
    base.update(kwargs)
    return base


class ACExecutorTests(unittest.TestCase):
    def test_zero_flat(self):
        r = execute_hour(**case(scores=np.zeros(4)))
        self.assertTrue(r['ok'])
        self.assertEqual(r['equity'], 10000.)
        self.assertEqual(r['fees'], 0.)

    def test_actual_open_self_financing(self):
        r = execute_hour(**case())
        self.assertTrue(r['ok'])
        self.assertGreater(r['turnover'], 0)
        self.assertLess(r['equity'], 10000.)
        self.assertAlmostEqual(r['equity'], 10000.-r['fees']-.002*r['turnover']/1.002, places=6)

    def test_signed_short(self):
        r = execute_hour(**case(scores=np.array([-4, 0, 0, 0])))
        self.assertTrue(r['ok'])
        self.assertLess(r['units'][0], 0)

    def test_funding_long_debit_short_credit(self):
        b=np.array([[99.,101.]]*4)
        ev=np.array([True,False,False,False])
        rate=np.array([.01,0,0,0])
        self.assertAlmostEqual(funding_cash(np.array([1.,0,0,0]),rate,b,ev)[0],-1.01)
        self.assertAlmostEqual(funding_cash(np.array([-1.,0,0,0]),rate,b,ev)[0],.99)

    def test_funding_ordering(self):
        k=case(funding_rate=np.array([.01,0,0,0]),
               mark_bounds=np.array([[99.,101.],[np.nan,np.nan],[np.nan,np.nan],[np.nan,np.nan]]),
               funding_event=np.array([True,False,False,False]))
        before=execute_hour(**k,order='carried_before_fill')
        after=execute_hour(**k,order='new_after_fill')
        self.assertTrue(before['ok'] and after['ok'])
        self.assertEqual(before['funding_cash_delta'],0.)
        self.assertLess(after['funding_cash_delta'],0.)

    def test_gap_no_phantom_exit(self):
        old=np.array([80.,0,0,0])
        k=case(cash=2000.,old_units=old,
               opening=np.array([50.,100,100,100]),
               low=np.array([49.,99,99,99]),
               high=np.array([100.,101,101,101]),
               closing=np.array([50.,100,100,100]))
        r=execute_hour(**k)
        self.assertFalse(r['ok'])
        self.assertEqual(r['reason'],'AC1177_GAP_UNEXECUTABLE')

    def test_no_quote_no_free_exit(self):
        k=case(cash=2000.,old_units=np.array([80.,0,0,0]),
               prior_quote=np.zeros(4))
        r=execute_hour(**k)
        self.assertFalse(r['ok'])

    def test_intrabar_concentration(self):
        reason=intrabar(1000.,np.array([50.,0,0,0]),
                        np.full(4,90.),np.full(4,100.),np.full(4,110.),6000.,0.)
        self.assertIsNotNone(reason)

    def test_invalid_fee(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_OR_COST'):
            execute_hour(**case(fee=.0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
