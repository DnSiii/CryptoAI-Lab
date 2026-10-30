#!/usr/bin/env python3
"""Y Phase1135 source-free synthetic contract tests; NEVER historical PnL."""
import unittest
import numpy as np
import pandas as pd
from phase1135_y_funded_training_simulator import (
    simulate_y,prior_bounds,adverse_signed_mark,FEE_TIERS,ORDERS,CAPITAL_MODES)

def fixture(n=748):
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    shape=(n,4)
    o=np.full(shape,100.);c=o.copy()
    h=np.full(shape,101.);l=np.full(shape,99.)
    q=np.full(shape,1e9)
    r=np.zeros(shape);mark=np.full((n,4,2),np.nan)
    ev=np.zeros(shape,dtype=bool)
    w=np.zeros(shape)
    return w,o,h,l,c,q,r,mark,ev,idx.year

class TestY1135(unittest.TestCase):
    def test_zero_position_self_financing(self):
        w,o,h,l,c,q,r,m,e,years=fixture()
        z=simulate_y(w,o,h,l,c,q,r,m,e,fee=.0007,
                     order=ORDERS[0],mode='immediate',years=years,strict=False)
        self.assertTrue(z['survived'],z['first_failure'])
        self.assertEqual(z['hourly_nav_observations'],4)
        self.assertEqual(z['terminal_usd'],CAPITAL_MODES['immediate'])
        self.assertEqual(z['filled_orders'],0)
        self.assertEqual(z['funding_debit_usd'],0.)
    def test_sign_specific_vendor_mark(self):
        units=np.array([1.,-1.,1.,-1.])
        rate=np.array([.01,.01,-.01,-.01])
        marks=np.array([[90.,110.]]*4)
        result=adverse_signed_mark(units,rate,marks,
            np.ones(4,dtype=bool),np.full(4,100.))
        np.testing.assert_array_equal(result,[110.,90.,90.,110.])
    def test_non_event_uses_close(self):
        units=np.array([1.,-1.,1.,-1.])
        rate=np.zeros(4);marks=np.full((4,2),np.nan)
        result=adverse_signed_mark(units,rate,marks,
            np.zeros(4,dtype=bool),np.full(4,101.))
        np.testing.assert_array_equal(result,[101.]*4)
    def test_signed_funding_reconciles_with_live_inventory(self):
        for order in ORDERS:
            w,o,h,l,c,q,r,m,e,years=fixture()
            w[744,0]=.10
            l[745:,0]=99.5
            r[746,0]=.01
            e[746,0]=True
            m[746,0]=[90.,110.]
            result=simulate_y(w,o,h,l,c,q,r,m,e,fee=.0007,
                order=order,mode='immediate',years=years,strict=False)
            self.assertTrue(result['survived'],(order,result['first_failure']))
            self.assertGreater(result['funding_debit_usd'],10.)
            self.assertGreater(result['active_hours'],0)
            self.assertGreater(result['filled_orders'],0)
    def test_2025_and_2026_are_forbidden(self):
        a=list(fixture())
        a[-1]=np.full(len(a[-1]),2025)
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_CELL'):
            simulate_y(*a[:-1],fee=.0007,order=ORDERS[0],
                mode='immediate',years=a[-1],strict=False)
    def test_bad_mark_order_rejected(self):
        a=list(fixture());a[8][744,0]=True
        a[7][744,0]=[110.,90.];a[6][744,0]=.001
        with self.assertRaisesRegex(ValueError,'INVALID_AUTHENTICATED_INPUT'):
            simulate_y(*a[:-1],fee=.0007,order=ORDERS[0],
                mode='immediate',years=a[-1],strict=False)
    def test_current_candle_not_in_prior_bound(self):
        _,o,h,l,c,q,r,m,e,years=fixture()
        d1,u1,f1=prior_bounds(c,h,l,r)
        h[747,0]=99999.;l[747,0]=1.
        d2,u2,f2=prior_bounds(c,h,l,r)
        np.testing.assert_array_equal(d1[746],d2[746])
        np.testing.assert_array_equal(u1[746],u2[746])
        np.testing.assert_array_equal(f1[746],f2[746])
    def test_unregistered_fee_and_order(self):
        a=fixture()
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_CELL'):
            simulate_y(*a[:-1],fee=.0008,order=ORDERS[0],
                mode='immediate',years=a[-1],strict=False)
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_CELL'):
            simulate_y(*a[:-1],fee=.0007,order='best_funding',
                mode='immediate',years=a[-1],strict=False)
    def test_partial_calendar_cannot_be_authenticated(self):
        a=fixture()
        with self.assertRaisesRegex(ValueError,'FUTURE_OR_INCOMPLETE_TRAINING'):
            simulate_y(*a[:-1],fee=.0007,order=ORDERS[0],
                mode='immediate',years=a[-1],strict=True)
    def test_precommitted_dimensions(self):
        self.assertEqual(len(FEE_TIERS)*len(ORDERS)*len(CAPITAL_MODES)*5,90)
        self.assertEqual(set(FEE_TIERS.values()),{.0007,.0012,.002})
if __name__=='__main__':unittest.main()
