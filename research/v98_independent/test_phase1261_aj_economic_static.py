#!/usr/bin/env python3
"""V98 AJ1261 static economic chronology/metric definitions; no historical data."""
import itertools
import unittest
from phase1260_aj_authenticated_source_digest import HOURS,PATHS,CAPITAL
from phase1261_aj_chronological_90cell import (
    WARMUP,YEAR_2024,metrics_hourly)
from phase1257_aj_open_viability_governor import FEES,ORDERS

class TestAJEconomicStatic(unittest.TestCase):
    def test_90_unique_preregistered_cells(self):
        grid=list(itertools.product(PATHS,CAPITAL,FEES,ORDERS))
        self.assertEqual(len(grid),90)
        self.assertEqual(len(set(grid)),90)

    def test_dec2022_only_warmup(self):
        self.assertEqual(WARMUP,744)
        self.assertEqual(YEAR_2024,9504)
        self.assertEqual(HOURS,18288)
        self.assertEqual(YEAR_2024-WARMUP,8760)
        self.assertEqual(HOURS-YEAR_2024,8784)

    def test_hourly_profit_factor_payoff(self):
        m=metrics_hourly([2.,-1.,4.,-2.],[.02,-.01,.04,-.02],1,2)
        self.assertAlmostEqual(m['hourly_net_profit_factor'],2.)
        self.assertAlmostEqual(m['hourly_net_payoff'],2.)
        self.assertAlmostEqual(m['hourly_net_win_rate'],.5)
        self.assertEqual(m['positive_utc_days'],1)

    def test_no_trades_are_explicit(self):
        m=metrics_hourly([0.,0.],[0.,0.],0,1)
        self.assertIsNone(m['hourly_net_profit_factor'])
        self.assertIsNone(m['hourly_net_payoff'])
        self.assertEqual(m['hourly_net_win_rate'],0.)

    def test_tail_is_negative(self):
        m=metrics_hourly([1.,-5.,1.,1.],[.01,-.05,.01,.01],1,1)
        self.assertLess(m['hourly_cvar_1pct'],0.)
        self.assertLessEqual(m['hourly_cvar_1pct'],m['hourly_var_1pct'])

if __name__=='__main__':
    unittest.main()
