#!/usr/bin/env python3
"""Independent AC FIFO partial close, reversal, signed funding, PF and NAV tests."""
import unittest
import numpy as np
from phase1184_ac_fifo_tradebook import FIFOTradebook


class FIFOTests(unittest.TestCase):
    def test_buy_hold_reconciles(self):
        b=FIFOTradebook(1000)
        b.trade(0,1,100,.1)
        r=b.reconcile(899.9,np.array([1.,0,0,0]),np.array([110.,100,100,100]))
        self.assertAlmostEqual(r['observed_pnl'],9.9)
        self.assertEqual(r['closed_trades'],0)

    def test_partial_close_fifo(self):
        b=FIFOTradebook(1000)
        b.trade(0,2,100,.2)
        b.trade(0,-1,110,.1)
        self.assertEqual(len(b.closed),1)
        self.assertAlmostEqual(b.closed[0]['net_pnl'],9.8)
        self.assertAlmostEqual(b.positions()[0],1.)
        b.reconcile(909.7,np.array([1.,0,0,0]),np.array([110.,100,100,100]))

    def test_reversal_and_short_profit(self):
        b=FIFOTradebook(1000)
        b.trade(0,1,100,.1)
        b.trade(0,-2,110,.2)
        self.assertEqual(len(b.closed),1)
        self.assertAlmostEqual(b.positions()[0],-1.)
        b.trade(0,1,90,.1)
        self.assertEqual(len(b.closed),2)
        self.assertGreater(b.closed[1]['net_pnl'],0)
        self.assertAlmostEqual(b.positions()[0],0.)
        b.reconcile(1029.6,np.zeros(4),np.full(4,100.))

    def test_signed_funding_debit_and_credit(self):
        b=FIFOTradebook(1000)
        b.trade(0,1,100,0.)
        b.apply_funding(0,-1.)
        b.trade(0,-1,100,0.)
        self.assertAlmostEqual(b.closed[0]['net_pnl'],-1.)
        b.reconcile(999.,np.zeros(4),np.full(4,100.))

    def test_proportional_funding_partial_close(self):
        b=FIFOTradebook(1000)
        b.trade(0,2,100,0.)
        b.apply_funding(0,-2.)
        b.trade(0,-1,100,0.)
        self.assertAlmostEqual(b.closed[0]['funding_cash'],-1.)
        self.assertAlmostEqual(b.unrealized(np.full(4,100.)),-1.)

    def test_funding_without_inventory_rejected(self):
        b=FIFOTradebook(1000)
        with self.assertRaisesRegex(ValueError,'WITHOUT_INVENTORY'):
            b.apply_funding(0,-1.)

    def test_profitable_and_losing_pf(self):
        b=FIFOTradebook(1000)
        b.trade(0,1,100,0.)
        b.trade(0,-1,110,0.)
        b.trade(0,1,100,0.)
        b.trade(0,-1,95,0.)
        m=b.trade_metrics()
        self.assertAlmostEqual(m['profit_factor'],2.)
        self.assertAlmostEqual(m['payoff'],2.)
        self.assertAlmostEqual(m['win_rate'],.5)

    def test_bad_nav_rejected(self):
        b=FIFOTradebook(1000)
        b.trade(0,1,100,0.)
        with self.assertRaisesRegex(ValueError,'NAV_RECONCILIATION'):
            b.reconcile(901.,np.array([1.,0,0,0]),np.full(4,110.))

    def test_bad_position_rejected(self):
        b=FIFOTradebook(1000)
        with self.assertRaisesRegex(ValueError,'POSITION_RECONCILIATION'):
            b.reconcile(1000.,np.array([1.,0,0,0]),np.full(4,100.))

    def test_four_assets_independent(self):
        b=FIFOTradebook(10000)
        for j in range(4):b.trade(j,(-1.)**j,100,0.)
        np.testing.assert_array_equal(b.positions(),[1,-1,1,-1])
        b.reconcile(10000.,np.array([1.,-1.,1.,-1.]),np.full(4,100.))


if __name__=='__main__':
    unittest.main(verbosity=2)
