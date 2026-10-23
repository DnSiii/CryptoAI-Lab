#!/usr/bin/env python3
"""V98 AI1248 preregistered forward-reachable governor fail-closed tests."""
import unittest,hashlib
import numpy as np
from phase1248_ai_reachable_governor import (
    NEXT,FEES,ORDERS,severe_safe,forward_reachable,ai_reachable_governor)

class TestAIReachable(unittest.TestCase):
    def args(self):
        return dict(cash_previous=10000.,old_units=np.zeros(4),
            prior_close=np.full(4,100.),opening=np.full(4,100.),
            signed_target=np.array([3.,-3.,0.,0.]),
            prior_down=np.full(4,.45),prior_up=np.full(4,.8),
            funding_bound=np.full(4,.0005),
            prior_quote=np.full(4,1e9),min_quote=np.full(4,1e9))
    def test_zero_safe(self):
        z=np.zeros(4);p=np.full(4,100.)
        self.assertTrue(forward_reachable(10000.,z,p,np.full(4,.45),
            np.full(4,.8),np.full(4,.0005),.001,10000.)[0])
    def test_17_next_states(self):
        self.assertEqual(len(NEXT),17)
        self.assertEqual(len(set(map(tuple,NEXT))),17)
    def test_signed_target_viable(self):
        r=ai_reachable_governor(**self.args())
        self.assertGreater(r['fraction'],0.)
        self.assertLess(r['fraction'],1.)
        self.assertLess(r['units'][1],0.)
        kw=self.args()
        self.assertTrue(forward_reachable(10000.,r['units'],kw['opening'],
            kw['prior_down'],kw['prior_up'],kw['funding_bound'],.001,10000.)[0])
    def test_next_hour_after_fees(self):
        kw=self.args();r=ai_reachable_governor(**kw)
        kw['old_units']=r['units']
        kw['cash_previous']=10000.-.001*np.sum(np.abs(r['units']*100))
        self.assertTrue(ai_reachable_governor(**kw)['forward_reachable'])
    def test_all_ordinary_next_states(self):
        kw=self.args();r=ai_reachable_governor(**kw)
        n=r['units'];p=kw['opening']
        cash=10000.-.001*np.sum(np.abs(n*p))
        for shock in NEXT:
            pp=p*(1+shock)
            cash_next=cash+n@(pp-p)-np.sum(np.abs(n*pp)*kw['funding_bound'])
            self.assertTrue(severe_safe(cash_next,n,pp,
                kw['prior_down'],kw['prior_up'],kw['funding_bound'],
                .001,10000.)[0])
    def test_carried_rejected(self):
        kw=self.args();kw['old_units']=np.array([130.,0,0,0])
        with self.assertRaisesRegex(ValueError,'CARRIED'):
            ai_reachable_governor(**kw)
    def test_quote_cap(self):
        kw=self.args()
        kw['prior_quote']=np.full(4,1000.)
        kw['min_quote']=np.full(4,1000.)
        r=ai_reachable_governor(**kw)
        self.assertTrue(np.all(np.abs(r['units'])*100<=3./(2.2*1.8)+1e-8))
    def test_six_modes(self):
        kw=self.args()
        for fee in FEES:
            for order in ORDERS:
                self.assertTrue(ai_reachable_governor(**kw,
                    fee_mode=fee,funding_order=order)['forward_reachable'])
    def test_no_realized_bar_in_pretrade(self):
        self.assertNotIn('high',ai_reachable_governor.__code__.co_varnames)
        self.assertNotIn('low',ai_reachable_governor.__code__.co_varnames)
    def test_exact_determinism(self):
        kw=self.args()
        x=ai_reachable_governor(**kw);y=ai_reachable_governor(**kw)
        self.assertEqual(hashlib.sha256(x['units'].astype('<f8').tobytes()).hexdigest(),
            hashlib.sha256(y['units'].astype('<f8').tobytes()).hexdigest())
    def test_bad_input(self):
        kw=self.args();kw['prior_down']=np.full(4,1.2)
        with self.assertRaises(ValueError):ai_reachable_governor(**kw)

if __name__=='__main__':unittest.main()
