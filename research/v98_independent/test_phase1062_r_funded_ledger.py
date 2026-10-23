#!/usr/bin/env python3
"""V98 R funded ledger synthetic contracts; no official history."""
import unittest
import numpy as np
import pandas as pd
from phase1062_r_funded_ledger import simulate,fold,FEE_TIERS,ORDERS,CAPITAL_MODES


def fixture(n=1700):
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    yy=idx.year.to_numpy();o=np.ones((n,4))*100;c=o.copy();h=o*1.001;l=o*.999
    q=np.ones((n,4))*1e9;rate=np.zeros((n,4));ev=np.zeros((n,4),bool)
    mark=np.full((n,4,2),np.nan);dn=np.full((n,4),.05);up=np.full((n,4),.05)
    w=np.zeros((n,4));w[1440:,0]=.15
    return w,o,h,l,c,q,rate,mark,ev,dn,up,yy

class RLedgerTest(unittest.TestCase):
    def test_grid(self):self.assertEqual(5*len(FEE_TIERS)*len(ORDERS)*len(CAPITAL_MODES),90)
    def test_cash(self):
        f=list(fixture());f[0][:]=0
        r=simulate(*f[:11],.0007,order='carried_before_fill',mode='immediate',years=f[11],require_full_sample=False)
        self.assertTrue(r['survived'],r);self.assertEqual(r['fees_usd'],0.)
    def test_fee_conservation(self):
        f=fixture()
        r=simulate(*f[:11],.0007,order='carried_before_fill',mode='immediate',years=f[11],require_full_sample=False)
        self.assertTrue(r['survived'],r);self.assertGreater(r['fees_usd'],0.)
        self.assertAlmostEqual(r['terminal_usd'],r['initial_usd']-r['fees_usd'],places=5)
    def test_source_preflight_separated(self):
        f=list(fixture());f[0][1500,0]=.9
        with self.assertRaisesRegex(ValueError,'R_PREFLIGHT_TARGET_CAP'):
            simulate(*f[:11],.0007,order='carried_before_fill',mode='immediate',years=f[11],require_full_sample=False)
    def test_signed_funding(self):
        f=list(fixture());f[7][1501,0]=[99.,101.];f[8][1501,0]=True;f[6][1501,0]=.001
        r=simulate(*f[:11],.0007,order='new_after_fill',mode='immediate',years=f[11],require_full_sample=False)
        self.assertTrue(r['survived'],r);self.assertGreater(r['funding_debit_usd'],0.)
    def test_fold_metrics(self):
        r=fold([100,110,100,120],100)
        self.assertTrue(r['complete']);self.assertEqual(r['positive_days'],2)

if __name__=='__main__':unittest.main()
