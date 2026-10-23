import unittest
import numpy as np
import pandas as pd
from phase1150_z_growth_metrics import summarize,fold_stats

class TestMetrics(unittest.TestCase):
    def test_partial_positive_compounding(self):
        idx=pd.date_range('2022-12-31T23:00Z',periods=121,freq='h')
        nav=10000*np.exp(np.arange(121)*.0002)
        out=summarize(idx,nav,np.zeros((121,4)),[],np.ones(121,int),strict=False)
        self.assertGreater(out['folds']['2023']['cagr'],0)
        self.assertEqual(out['folds']['2023']['positive_days'],5)
        self.assertAlmostEqual(out['total_log_wealth'],np.log(nav[-1]/nav[0]))
    def test_loss_and_drawdown(self):
        idx=pd.date_range('2022-12-31T23:00Z',periods=49,freq='h')
        nav=10000*np.exp(-np.arange(49)*.001)
        out=summarize(idx,nav,np.zeros((49,4)),[],np.ones(49,int),strict=False)
        self.assertLess(out['folds']['2023']['cagr'],0)
        self.assertEqual(out['folds']['2023']['positive_days'],0)
        self.assertLess(out['all_hourly_max_drawdown'],0)
    def test_profit_factor_and_payoff(self):
        nav=np.full(49,10000.)
        trades=[{'pnl_usd':100.},{'pnl_usd':-50.},{'pnl_usd':50.}]
        x=fold_stats(None,nav,np.zeros((48,4)),trades,year=2023,strict=False)
        self.assertEqual(x['profit_factor'],3)
        self.assertEqual(x['payoff'],1.5)
        self.assertAlmostEqual(x['win_rate'],2/3)
    def test_2024_leap_fold(self):
        nav=np.full(8785,10000.)
        x=fold_stats(None,nav,np.zeros((8784,4)),[],year=2024,strict=True)
        self.assertEqual(x['days'],366)
    def test_no_future_or_bad_chronology(self):
        idx=pd.date_range('2025-01-01',periods=50,freq='h',tz='UTC')
        with self.assertRaisesRegex(ValueError,'TRAINING_FOLDS_ONLY'):
            summarize(idx,np.ones(50),np.zeros((50,4)),[],np.ones(50,int))

if __name__=='__main__':unittest.main()
