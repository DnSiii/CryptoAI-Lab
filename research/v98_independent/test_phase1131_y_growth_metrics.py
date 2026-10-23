#!/usr/bin/env python3
"""Y growth metric chronological folds, no future and realized-trade tests."""
import unittest
import numpy as np
import pandas as pd
from phase1131_y_growth_metrics import summarize,_trade_metrics

class TestYGrowthMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx=pd.date_range('2022-12-31T23:00Z','2024-12-31T23:00Z',freq='h')
        cls.nav=10000*np.exp(np.arange(len(cls.idx))*.00001)
        cls.exp=np.zeros((len(cls.idx),4));cls.exp[:,0]=2000
    def test_chronological_folds_and_growth(self):
        x=summarize(self.idx,self.nav,self.exp)
        self.assertEqual(x['folds']['2023']['hourly_observations'],8760)
        self.assertEqual(x['folds']['2024']['hourly_observations'],8784)
        self.assertEqual(x['folds']['2023']['positive_days'],365)
        self.assertGreater(x['folds']['2024']['cagr'],0)
        self.assertEqual(x['folds']['2024']['concentration']['asset_hhi'],1.)
        self.assertIsNone(x['folds']['2023']['profit_factor'])
        self.assertEqual(set(x),{'folds'})
    def test_trade_pf_payoff_are_realized_only(self):
        x=_trade_metrics([10,-5,20,-10])
        self.assertAlmostEqual(x['profit_factor'],2.)
        self.assertAlmostEqual(x['payoff'],2.)
        self.assertAlmostEqual(x['win_rate'],.5)
    def test_folds_no_future_and_no_lookahead(self):
        with self.assertRaises(ValueError):
            summarize(self.idx+pd.Timedelta(days=366),self.nav,self.exp)
    def test_single_year_cherry_pick_rejected(self):
        mask=self.idx.year!=2024
        with self.assertRaises(ValueError):
            summarize(self.idx[mask],self.nav[mask],self.exp[mask])
    def test_gap_rejected(self):
        with self.assertRaises(ValueError):
            summarize(self.idx.delete(50),np.delete(self.nav,50),np.delete(self.exp,50,axis=0))
    def test_invalid_equity_rejected(self):
        nav=self.nav.copy();nav[500]=-1
        with self.assertRaises(ValueError):summarize(self.idx,nav,self.exp)
    def test_trade_timestamp_provenance(self):
        with self.assertRaises(ValueError):
            summarize(self.idx,self.nav,self.exp,[{'timestamp':'2025-01-01T00:00Z','pnl_usd':1.}])
if __name__=='__main__':unittest.main()
