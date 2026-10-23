#!/usr/bin/env python3
"""V98 Phase1007 O exact-LP hourly execution synthetic-only tests."""
from __future__ import annotations
import unittest
import numpy as np
from phase1002_lp_opening_repair import repair_open_lp
from phase1007_o_funded_ledger_hourly import simulate_o_with_hourly


def synthetic(n=96):
    target = np.zeros((n,4))
    target[:,0] = .35
    target[:,1] = .30
    o = np.ones((n,4))*100
    h = o*1.01
    l = o*.99
    c = o.copy()
    q = np.ones((n,4))*1e8
    rate = np.zeros((n,4))
    mark = np.full((n,4), np.nan)
    event = np.zeros((n,4), dtype=bool)
    years = np.full(n,2023)
    return target,o,h,l,c,q,rate,mark,event,years


def run(arr,fee=.0007,order="carried_before_fill",mode="immediate"):
    w,o,h,l,c,q,rate,mark,event,years = arr
    return simulate_o_with_hourly(w,o,h,l,c,q,rate,mark,event,fee,order=order,mode=mode,years=years,require_full_sample=False)


class OLedgerTests(unittest.TestCase):
    def test_cash_only_survives(self):
        a = list(synthetic())
        a[0] = np.zeros_like(a[0])
        r = run(a)
        self.assertTrue(r["survived"])
        self.assertEqual(r["filled_orders"],0)
        self.assertEqual(r["opening_repair_events"],0)

    def test_target_causality_last_close_unexecuted(self):
        a = list(synthetic())
        first = run(a)
        self.assertTrue(first["survived"])
        a[0] = a[0].copy()
        a[0][-1,:] = [.7,.7,.1,.1]
        second = run(a)
        self.assertEqual(first, second)

    def test_lp_opening_repair_is_sell_only(self):
        cash,units,sold,ok = repair_open_lp(-.2,np.array([.9,.4,0.,0.]),np.ones(4),np.ones(4)*100, .0007)
        self.assertTrue(ok)
        self.assertGreater(sold.sum(),0)
        self.assertTrue((units <= np.array([.9,.4,0.,0.])+1e-12).all())
        eq = cash + units.sum()
        self.assertLessEqual(units.max()/eq,.70+1e-8)

    def test_realized_intrabar_violation_is_rejected(self):
        a = list(synthetic())
        a[0] = a[0].copy()
        a[0][:,:] = 0
        a[0][:,0] = .65
        a[2] = a[2].copy()
        a[2][3,0] = 250
        r = run(a)
        self.assertFalse(r["survived"])
        self.assertEqual(r["reason"],"INTRABAR_SURVIVAL_BREACH")
        self.assertEqual(r["breach_index"],3)

    def test_forbid_2025_and_invalid_funding(self):
        a = list(synthetic())
        a[-1] = a[-1].copy()
        a[-1][50] = 2025
        with self.assertRaises(ValueError):
            run(a)
        b = list(synthetic())
        b[7] = b[7].copy()
        b[7][3,0] = 1
        with self.assertRaises(ValueError):
            run(b)

    def test_fee_and_ordering_and_capital_modes(self):
        a = synthetic()
        results = [run(a,fee=f,order=order,mode=mode)
                   for f in (.0007,.0012,.0020)
                   for order in ("carried_before_fill","new_after_fill")
                   for mode in ("immediate","capacity_1m","capacity_10m")]
        self.assertEqual(len(results),18)
        self.assertTrue(all(r["survived"] for r in results))
        self.assertTrue(all(r["fees_usd"] >= 0 for r in results))

    def test_reproducible_hourly_receipt(self):
        a = synthetic()
        self.assertEqual(run(a),run(a))


if __name__ == "__main__":
    unittest.main()
