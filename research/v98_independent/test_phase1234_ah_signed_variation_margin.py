#!/usr/bin/env python3
"""AH1234 signed USD-M variation margin, funding, capacity and 81-corner tests."""
import unittest
import numpy as np
from phase1234_ah_signed_variation_margin import (
    funding_delta,settle_hour,scenario_audit,MAINTENANCE_RATE)


class TestAHVariationMargin(unittest.TestCase):
    def setUp(self):
        self.p=np.array([100.,150.,50.,200.])
        self.q=np.full(4,1e12)
        self.z=np.zeros(4)
        self.d=np.full(4,.20)
        self.u=np.full(4,.20)
        self.f=np.full(4,.002)

    def hour(self,old=None,target=None,cash=10000.,p0=None,p=None,
             high=None,low=None,close=None,quote=None,
             rate=None,event=None,order='carried_before_fill'):
        if old is None:old=self.z
        if target is None:target=np.array([1.,-.5,.4,-.1])
        if p0 is None:p0=self.p
        if p is None:p=self.p
        if high is None:high=p*1.001
        if low is None:low=p*.999
        if close is None:close=p
        if quote is None:quote=self.q
        if rate is None:rate=self.z
        if event is None:event=self.z
        return settle_hour(cash,old,p0,p,high,low,close,target,
             quote,self.q,self.d,self.u,self.f,rate,event,
             p*.99,p*1.01,'base',order)

    def test_signed_long_short_and_no_spot_notional_debit(self):
        r=self.hour()
        self.assertTrue(np.any(r['units']<0))
        self.assertTrue(np.any(r['units']>0))
        self.assertTrue(r['cash_settled'])
        self.assertFalse(r['hidden_borrow'])
        self.assertAlmostEqual(r['cash'],10000.-r['fees']-r['slippage'],places=6)

    def test_overnight_and_intrabar_variation_cash(self):
        old=np.array([2.,-1.,0.,0.])
        p=np.array([110.,140.,50.,200.])
        c=np.array([110.22,139.72,50.,200.])
        r=self.hour(old=old,target=old,p=p,close=c)
        self.assertAlmostEqual(r['overnight_pnl'],30.,places=6)
        self.assertAlmostEqual(r['intrabar_pnl'],.72,places=6)
        self.assertAlmostEqual(r['cash'],10030.72,places=5)
        self.assertEqual(r['turnover'],0.)

    def test_funding_obligation_depends_on_position_sign(self):
        n=np.array([1.,-2.,0.,0.])
        rate=np.array([.001,.001,0.,0.])
        event=np.array([1.,1.,0.,0.])
        delta=funding_delta(n,rate,event,self.p*.99,self.p*1.01)
        self.assertAlmostEqual(delta,-.101+.297,places=6)

    def test_funding_order_timing_is_real(self):
        old=np.array([1.,0.,0.,0.])
        target=np.array([0.,-1.,0.,0.])
        r=np.array([.001,.001,0.,0.])
        e=np.array([1.,1.,0.,0.])
        a=self.hour(old=old,target=target,rate=r,event=e)
        b=self.hour(old=old,target=target,rate=r,event=e,
                    order='new_after_fill')
        self.assertNotEqual(a['funding'],b['funding'])

    def test_maintenance_margin_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'MAINTENANCE_MARGIN'):
            self.hour(target=np.array([1000.,0.,0.,0.]))

    def test_quote_capacity_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'ORDER_CAPACITY'):
            self.hour(quote=np.zeros(4))

    def test_short_squeeze_expost_audit(self):
        with self.assertRaisesRegex(ValueError,'REALIZED_'):
            self.hour(target=np.array([0.,-40.,0.,0.]),
                      high=self.p*np.array([1.,2.,1.,1.]))

    def test_causal_same_open_different_benign_extremes(self):
        a=self.hour(high=self.p*1.0001,low=self.p*.9999)
        b=self.hour(high=self.p*1.002,low=self.p*.998)
        self.assertTrue(np.array_equal(a['units'],b['units']))
        self.assertEqual(a['cash'],b['cash'])

    def test_randomized_signed_survival_and_cash_reconciliation(self):
        rng=np.random.default_rng(1234)
        passed=0
        for _ in range(250):
            target=rng.uniform(-3.,3.,4)
            p=self.p
            cash=10000.
            try:
                r=self.hour(target=target,cash=cash,
                            high=p*1.01,low=p*.99)
            except ValueError as exc:
                self.assertIn('REALIZED_',str(exc))
                continue
            self.assertTrue(np.isfinite(r['cash']))
            self.assertGreater(r['cash'],0)
            self.assertGreaterEqual(r['cash']+1e-7,r['maintenance_at_close'])
            self.assertAlmostEqual(r['cash']+r['fees']+r['slippage'],
                                   cash,places=5)
            passed+=1
        self.assertGreater(passed,100)


if __name__=='__main__':
    unittest.main()
