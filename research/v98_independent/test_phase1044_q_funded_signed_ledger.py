import unittest
import numpy as np
from phase1044_q_funded_signed_ledger import simulate_q_hourly,FEE_TIERS

class QLedgerTests(unittest.TestCase):
    def fixture(self):
        n=1650;o=np.ones((n,4))*100;c=o.copy();h=o*1.001;l=o*.999;q=np.ones((n,4))*1e7
        fr=np.zeros((n,4));ev=np.zeros((n,4),bool);mk=np.full((n,4,2),np.nan)
        dn=np.ones((n,4))*.01;up=dn.copy();years=np.ones(n,int)*2023
        return o,h,l,c,q,fr,mk,ev,dn,up,years
    def test_flat_cash_conservation(self):
        o,h,l,c,q,fr,mk,ev,dn,up,years=self.fixture();w=np.zeros_like(o)
        r=simulate_q_hourly(w,o,h,l,c,q,fr,mk,ev,dn,up,FEE_TIERS['base'],order='carried_before_fill',mode='immediate',years=years,require_full_sample=False)
        self.assertTrue(r['survived'],r);self.assertAlmostEqual(r['terminal_usd'],10000)
        self.assertEqual(r['fees_usd'],0);self.assertEqual(r['funding_debit_usd'],0)
    def test_native_signed_funding(self):
        o,h,l,c,q,fr,mk,ev,dn,up,years=self.fixture();w=np.zeros_like(o)
        w[1440:,0]=.10;w[1440:,1]=-.10
        ev[1450,0]=True;ev[1450,1]=True;mk[1450,0]=[99,101];mk[1450,1]=[99,101];fr[1450,0]=.001;fr[1450,1]=.001
        r=simulate_q_hourly(w,o,h,l,c,q,fr,mk,ev,dn,up,FEE_TIERS['base'],order='new_after_fill',mode='immediate',years=years,require_full_sample=False)
        self.assertTrue(r['survived'],r);self.assertGreater(r['filled_orders'],0)
        self.assertGreater(r['funding_debit_usd'],0)  # long debit high mark, short credit low mark
    def test_bad_future_rejected(self):
        o,h,l,c,q,fr,mk,ev,dn,up,years=self.fixture();years[-1]=2025
        with self.assertRaises(ValueError):simulate_q_hourly(np.zeros_like(o),o,h,l,c,q,fr,mk,ev,dn,up,FEE_TIERS['base'],order='carried_before_fill',mode='immediate',years=years,require_full_sample=False)

if __name__=='__main__':unittest.main()
