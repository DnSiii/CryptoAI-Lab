import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np,pandas as pd
from phase1170_ab_growth_metrics import metrics
class TestABMetrics(unittest.TestCase):
    def sample(self):
        idx=pd.date_range('2023-01-01',periods=240,freq='h',tz='UTC')
        v=10000*np.exp(np.linspace(0,.1,240)+.02*np.sin(np.arange(240)/20))
        return pd.Series(v,index=idx),np.full(240,1.),np.zeros(240),np.zeros((240,4)),np.ones(240,int)
    def test_metrics_and_reproducibility(self):
        a=self.sample();x=metrics(*a);y=metrics(*a)
        self.assertEqual(x,y);self.assertGreater(x['cagr'],0)
        self.assertEqual(sum(x['regime_hours'].values()),239)
        self.assertAlmostEqual(x['total_fees'],240.)
        self.assertLessEqual(x['max_drawdown'],0)
    def test_loss_tail_and_profit_factor(self):
        a=list(self.sample());a[0]=pd.Series(10000*np.exp(-np.linspace(0,.1,240)),index=a[0].index)
        x=metrics(*a);self.assertLess(x['cagr'],0)
        self.assertEqual(x['positive_days'],0)
        self.assertEqual(x['daily_profit_factor'],0.)
    def test_no_2025_or_invalid_nav(self):
        a=list(self.sample());a[0]=a[0].set_axis(pd.date_range('2025-01-01',periods=240,freq='h',tz='UTC'))
        with self.assertRaisesRegex(ValueError,'TRAINING_ONLY'):metrics(*a)
        b=list(self.sample());b[0].iloc[2]=0
        with self.assertRaisesRegex(ValueError,'INVALID_RECEIPT'):metrics(*b)
if __name__=='__main__':unittest.main()
