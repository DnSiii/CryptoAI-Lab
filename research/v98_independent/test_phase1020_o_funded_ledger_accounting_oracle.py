#!/usr/bin/env python3
"""V98 Phase1020: independent synthetic wealth conservation oracle. No historical PnL."""
from __future__ import annotations
import unittest
import numpy as np
from phase1007_o_funded_ledger_hourly import simulate_o_with_hourly
from phase876_k_funded_ledger import FEE_TIERS, ORDERS, CAPITAL_MODES

N = 96

def fixture():
    w = np.zeros((N, 4), dtype=float)
    o = np.full((N, 4), 100., dtype=float)
    h = np.full((N, 4), 100.2, dtype=float)
    l = np.full((N, 4), 99.8, dtype=float)
    c = o.copy()
    q = np.full((N, 4), 1.e9, dtype=float)
    fr = np.zeros((N, 4), dtype=float)
    mk = np.full((N, 4), np.nan, dtype=float)
    ev = np.zeros((N, 4), dtype=bool)
    yy = np.full(N, 2023, dtype=int)
    return [w, o, h, l, c, q, fr, mk, ev, yy]

def execute(a, *, fee=.0007, order="carried_before_fill", mode="immediate"):
    return simulate_o_with_hourly(*a[:9], fee, order=order, mode=mode,
                                  years=a[9], require_full_sample=False)

def conserve(r):
    assert r["survived"], r
    residual = (r["terminal_usd"] + r["fees_usd"] +
                r["funding_debit_usd"] - r["initial_usd"])
    return residual

class OWealthConservationOracle(unittest.TestCase):
    def test_flat_price_turnover_has_no_free_money_at_all_cost_tiers(self):
        a = fixture()
        a[0][::2, 0] = .30
        a[0][::2, 1] = .15
        a[0][1::2, 2] = .35
        a[0][1::2, 3] = .10
        terminals = []
        for fee in FEE_TIERS.values():
            for order in ORDERS:
                r = execute(a, fee=fee, order=order)
                self.assertTrue(r["survived"], r.get("reason"))
                self.assertAlmostEqual(conserve(r), 0., delta=1.e-5)
                self.assertEqual(r["funding_debit_usd"], 0.)
                self.assertGreater(r["fees_usd"], 0.)
                self.assertLess(r["terminal_usd"], r["initial_usd"])
                terminals.append((fee, order, r["terminal_usd"]))
        for order in ORDERS:
            vals = [x[2] for x in terminals if x[1] == order]
            self.assertGreater(vals[0], vals[1])
            self.assertGreater(vals[1], vals[2])

    def test_funding_settlement_order_is_real_and_reconciles(self):
        a = fixture()
        a[0][0, 0] = .20
        a[6][1, 0] = .01
        a[7][1, 0] = 100.
        a[8][1, 0] = True
        carried = execute(a, order="carried_before_fill")
        new = execute(a, order="new_after_fill")
        for r in (carried, new):
            self.assertTrue(r["survived"], r.get("reason"))
            self.assertAlmostEqual(conserve(r), 0., delta=1.e-5)
        self.assertAlmostEqual(carried["funding_debit_usd"], 0., delta=1.e-8)
        self.assertGreater(new["funding_debit_usd"], 1000.)
        self.assertGreater(carried["terminal_usd"], new["terminal_usd"])

    def test_tminus_one_volume_participation_and_flat_wealth(self):
        a = fixture()
        a[0][:, 0] = .40
        a[5][:] = 1000.  # 5% per prior-hour asset volume = 50 USD/hour
        immediate = execute(a, mode="immediate")
        capacity = execute(a, mode="capacity_1m")
        for r in (immediate, capacity):
            self.assertTrue(r["survived"], r.get("reason"))
            self.assertAlmostEqual(conserve(r), 0., delta=1.e-5)
        self.assertGreater(immediate["fees_usd"], capacity["fees_usd"])
        self.assertGreater(capacity["partial_asset_hours"], immediate["partial_asset_hours"])
        self.assertLessEqual(capacity["turnover_usd"], 50. * (N - 1) + 1.e-6)

    def test_cash_only_funding_event_does_not_create_debit(self):
        a = fixture()
        a[6][1, 2] = -.05
        a[7][1, 2] = 100.
        a[8][1, 2] = True
        for order in ORDERS:
            r = execute(a, order=order)
            self.assertTrue(r["survived"], r.get("reason"))
            self.assertAlmostEqual(conserve(r), 0., delta=1.e-8)
            self.assertEqual(r["funding_debit_usd"], 0.)
            self.assertEqual(r["filled_orders"], 0)

if __name__ == "__main__":
    unittest.main()
