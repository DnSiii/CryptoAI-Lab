#!/usr/bin/env python3
"""V98 AI1250 preregistered actual-open controlled viability tests."""
import unittest,hashlib
import numpy as np
from phase1250_ai_controlled_governor import (
    FEES,ORDERS,ai_controlled_governor,future_safe)
from phase1246_ai_two_stage_margin import settle_hour

class TestControlledViability(unittest.TestCase):
    def args(self):
        return dict(cash_previous=10000.,old_units=np.zeros(4),
            prior_close=np.full(4,100.),opening=np.full(4,100.),
            signed_target=np.array([3.,-3.,0.,0.]),
            prior_down=np.full(4,.45),prior_up=np.full(4,.8),
            funding_bound=np.full(4,.0005),
            prior_quote=np.full(4,1e9),min_quote=np.full(4,1e9))
    def test_nonzero_signed_target(self):
        r=ai_controlled_governor(**self.args())
        self.assertGreater(r['fraction'],0.)
        self.assertLess(r['fraction'],1.)
        self.assertLess(r['units'][1],0.)
        self.assertTrue(r['future_safe'])
    def test_next_hour_actual_fees(self):
        kw=self.args();r=ai_controlled_governor(**kw)
        kw['old_units']=r['units']
        kw['cash_previous']=10000.-.001*np.sum(np.abs(r['units']*100))
        next_r=ai_controlled_governor(**kw)
        self.assertTrue(next_r['real_open_solvent'])
        self.assertTrue(next_r['future_safe'])
    def test_reachable_real_reduction(self):
        kw=self.args()
        kw['old_units']=np.array([140.,0,0,0])
        kw['signed_target']=np.zeros(4)
        r=ai_controlled_governor(**kw)
        self.assertTrue(r['controlled_reduction'])
        self.assertLess(abs(r['units'][0]),140.)
    def test_insufficient_depth_rejects(self):
        kw=self.args()
        kw['old_units']=np.array([140.,0,0,0])
        kw['signed_target']=np.zeros(4)
        kw['prior_quote']=np.full(4,1000.)
        kw['min_quote']=np.full(4,1000.)
        with self.assertRaisesRegex(ValueError,'NO_REACHABLE'):
            ai_controlled_governor(**kw)
    def test_actual_gap_bankruptcy(self):
        kw=self.args()
        kw['old_units']=np.array([140.,0,0,0])
        kw['opening']=np.array([10.,100,100,100])
        with self.assertRaisesRegex(ValueError,'REAL_GAP_BANKRUPTCY'):
            ai_controlled_governor(**kw)
    def test_real_open_insolvency(self):
        kw=self.args()
        kw['cash_previous']=1000.
        kw['old_units']=np.array([100.,0,0,0])
        with self.assertRaisesRegex(ValueError,'REAL_OPEN_INSOLVENCY'):
            ai_controlled_governor(**kw)
    def test_six_modes(self):
        kw=self.args()
        for fee in FEES:
            for order in ORDERS:
                self.assertTrue(ai_controlled_governor(**kw,
                    fee_mode=fee,funding_order=order)['future_safe'])
    def test_quote_capacity(self):
        kw=self.args()
        kw['prior_quote']=np.full(4,1000.)
        kw['min_quote']=np.full(4,1000.)
        r=ai_controlled_governor(**kw)
        self.assertTrue(np.all(np.abs(r['units'])*100<=3./(2.2*1.8)+1e-8))
    def test_actual_signed_settlement(self):
        kw=self.args();r=ai_controlled_governor(**kw)
        p=np.full(4,100.);z=np.zeros(4)
        out=settle_hour(10000.,z,p,p,p*1.01,p*.99,p,
            r['units'],z,z,p*.99,p*1.01)
        self.assertTrue(out['cash_settled'])
        self.assertFalse(out['hidden_borrow'])
        self.assertAlmostEqual(out['cash'],10000.-out['fees']-out['slippage'])
    def test_no_realized_bar(self):
        self.assertNotIn('high',ai_controlled_governor.__code__.co_varnames)
        self.assertNotIn('low',ai_controlled_governor.__code__.co_varnames)
    def test_deterministic(self):
        kw=self.args()
        a=ai_controlled_governor(**kw);b=ai_controlled_governor(**kw)
        self.assertEqual(hashlib.sha256(a['units'].astype('<f8').tobytes()).hexdigest(),
            hashlib.sha256(b['units'].astype('<f8').tobytes()).hexdigest())
    def test_invalid(self):
        kw=self.args();kw['prior_down']=np.full(4,1.1)
        with self.assertRaises(ValueError):ai_controlled_governor(**kw)

if __name__=='__main__':unittest.main()
