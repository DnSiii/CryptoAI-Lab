#!/usr/bin/env python3
"""V98 AI1246 preregistered two-stage collateral and signed ledger unit tests."""
import unittest,hashlib
import numpy as np
from phase1246_ai_two_stage_margin import (
    four,signed_funding,two_stage_audit,ai_governor,settle_hour,
    FEES,ORDERS,MAINTENANCE)

class TestAIInvariant(unittest.TestCase):
    def args(self):
        return dict(cash_previous=10000.,old_units=np.zeros(4),
            prior_close=np.full(4,100.),opening=np.full(4,100.),
            signed_target=np.array([3.,-3.,0.,0.]),
            prior_down=np.full(4,.45),prior_up=np.full(4,.8),
            funding_bound=np.full(4,.0005),
            prior_quote=np.full(4,1e9),min_quote=np.full(4,1e9))
    def test_zero_inventory_viable(self):
        ok,reason=two_stage_audit(10000.,np.zeros(4),np.full(4,100.),
            np.full(4,.45),np.full(4,.8),np.full(4,.0005),.001,10000.)
        self.assertTrue(ok,reason)
    def test_second_stage_not_same_as_one_step(self):
        n=np.array([133.,0,0,0])
        ok,reason=two_stage_audit(10000.,n,np.full(4,100.),
            np.full(4,.45),np.full(4,.8),np.zeros(4),.001,10000.)
        self.assertFalse(ok)
        self.assertEqual(reason,'SECOND_STAGE_VIABILITY')
    def test_signed_funding_both_sides(self):
        p=np.full(4,100.)
        rate=np.array([.01,.01,0,0])
        event=np.array([1.,1.,0,0])
        n=np.array([1.,-1.,0,0])
        self.assertAlmostEqual(signed_funding(n,rate,event,p,p),0.)
        self.assertAlmostEqual(signed_funding(n,rate,event,p*.99,p*1.01),-.02)
    def test_max_feasible_not_free_leverage(self):
        kw=self.args()
        r=ai_governor(**kw)
        self.assertGreater(r['fraction'],0.)
        self.assertLess(r['fraction'],1.)
        self.assertLess(r['units'][1],0.)
        ok,reason=two_stage_audit(10000.,r['units'],np.full(4,100.),
            np.full(4,.45),np.full(4,.8),np.full(4,.0005),.001,10000.)
        self.assertTrue(ok,reason)
    def test_next_hour_ordinary_carry(self):
        kw=self.args()
        r=ai_governor(**kw)
        old=r['units']
        kw['old_units']=old
        kw['signed_target']=np.array([3.,-3.,0.,0.])
        kw['cash_previous']=10000.-.001*np.sum(np.abs(old*100))
        self.assertTrue(ai_governor(**kw)['two_stage_viable'])
    def test_carried_fail_closed(self):
        kw=self.args();kw['old_units']=np.array([130.,0,0,0])
        with self.assertRaisesRegex(ValueError,'CARRIED'):
            ai_governor(**kw)
    def test_quote_capacity(self):
        kw=self.args()
        kw['prior_quote']=np.full(4,1000.)
        kw['min_quote']=np.full(4,1000.)
        r=ai_governor(**kw)
        self.assertTrue(np.all(np.abs(r['units'])*100<=3./(2.2*1.8)+1e-8))
    def test_both_fee_and_funding_modes(self):
        kw=self.args()
        for fee in FEES:
            for order in ORDERS:
                r=ai_governor(**kw,fee_mode=fee,funding_order=order)
                self.assertTrue(np.isfinite(r['units']).all())
    def test_actual_variation_margin(self):
        kw=self.args()
        r=ai_governor(**kw)
        p=np.full(4,100.)
        z=np.zeros(4)
        out=settle_hour(10000.,z,p,p,p*1.01,p*.99,p,
            r['units'],z,z,p*.99,p*1.01)
        self.assertTrue(out['cash_settled'])
        self.assertFalse(out['hidden_borrow'])
        self.assertLess(out['cash'],10000.)
        self.assertAlmostEqual(out['cash'],10000.-out['fees']-out['slippage'])
    def test_pretrade_no_realized_high_low(self):
        self.assertNotIn('high',ai_governor.__code__.co_varnames)
        self.assertNotIn('low',ai_governor.__code__.co_varnames)
    def test_deterministic_digest(self):
        kw=self.args()
        a=ai_governor(**kw)
        b=ai_governor(**kw)
        self.assertEqual(hashlib.sha256(a['units'].astype('<f8').tobytes()).hexdigest(),
            hashlib.sha256(b['units'].astype('<f8').tobytes()).hexdigest())
    def test_invalid(self):
        kw=self.args();kw['prior_down']=np.full(4,1.1)
        with self.assertRaises(ValueError):ai_governor(**kw)

if __name__=='__main__':unittest.main()
