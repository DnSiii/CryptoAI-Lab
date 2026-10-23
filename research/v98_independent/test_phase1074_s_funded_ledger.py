#!/usr/bin/env python3
"""S signed hourly ledger synthetic-only, no historical sources or benchmarks."""
import unittest
import numpy as np
from phase1074_s_funded_ledger import simulate,prior_shocks,fold

def sample(n=1800):
    o=np.full((n,4),100.);h=o*1.001;l=o*.999;c=o.copy()
    q=np.full((n,4),1e7);r=np.zeros((n,4));ev=np.zeros((n,4),bool)
    marks=np.full((n,4,2),np.nan);w=np.zeros((n,4));y=np.r_[np.full(744,2022),np.full(n-744,2023)]
    dn,up=prior_shocks(o,h,l)
    return [w,o,h,l,c,q,r,marks,ev,dn,up],y

class SFundedLedger(unittest.TestCase):
    def test_no_trade_survival(self):
        a,y=sample();result=simulate(*a,.0007,order='carried_before_fill',mode='immediate',years=y,require_full_sample=False)
        self.assertTrue(result['survived'],result);self.assertEqual(result['fees_usd'],0.)
        self.assertEqual(result['funding_debit_usd'],0.);self.assertEqual(result['total_log_wealth'],0.)
    def test_signed_funding_and_costs(self):
        a,y=sample();a[0][735:]=[.12,-.08,0.,0.]
        a[6][760,0]=.001;a[6][760,1]=-.001;a[8][760,:2]=True
        a[7][760,:2]=[99.9,100.1]
        result=simulate(*a,.0012,order='new_after_fill',mode='immediate',years=y,require_full_sample=False)
        self.assertTrue(result['survived'],result);self.assertGreater(result['fees_usd'],0.)
        self.assertGreater(result['funding_debit_usd'],0.)
    def test_wrong_signed_shape_rejected(self):
        a,y=sample();a[7]=np.full((1800,4),np.nan)
        with self.assertRaisesRegex(ValueError,'SOURCE_GEOMETRY'):simulate(*a,.0007,order='new_after_fill',mode='immediate',years=y,require_full_sample=False)
    def test_future_rejected(self):
        a,y=sample();y[1700]=2025
        with self.assertRaisesRegex(ValueError,'TRAINING_CELL'):simulate(*a,.0007,order='new_after_fill',mode='immediate',years=y,require_full_sample=False)
    def test_prior_shocks_causal(self):
        a,_=sample();down,up=prior_shocks(a[1],a[2],a[3]);h=a[2].copy();h[1000:]*=1.2
        other=prior_shocks(a[1],h,a[3]);np.testing.assert_array_equal(up[:1000],other[1][:1000])
        self.assertTrue(np.isfinite(down[24:]).all())
    def test_fold_metrics(self):
        x=fold(np.array([100.,110.,105.,115.]),100.)
        self.assertTrue(x['complete']);self.assertGreater(x['log_wealth'],0)
        self.assertGreater(x['positive_days'],0);self.assertLess(x['max_drawdown'],0)
if __name__=='__main__':unittest.main()
