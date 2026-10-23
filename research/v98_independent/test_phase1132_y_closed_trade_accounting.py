#!/usr/bin/env python3
"""Y FIFO closed trade, signed funding and 200-hour NAV reconciliation tests."""
import unittest
import numpy as np
from phase1132_y_closed_trade_accounting import TradeBook
from phase1126_y_hourly_ledger import execute_hour
T='2023-01-01T00:00:00Z'

def event(asset,units,price,fee=0.):
    return {'asset':asset,'action':'TEST','delta_units':units,'fill_price':price,
            'fee_usd':fee,'notional':abs(units)*price}

class TestYTradeBook(unittest.TestCase):
    def test_long_win_with_fees(self):
        b=TradeBook(10000)
        b.apply_hour([event(0,10,100,2)],[0]*4,T,funding_order='new_after_fill')
        b.apply_hour([event(0,-10,110,2)],[0]*4,'2023-01-01T01:00Z',funding_order='new_after_fill')
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],96.)
        self.assertAlmostEqual(b.total_pnl(np.ones(4)*100),96.)
    def test_short_win_and_partial(self):
        b=TradeBook(10000)
        b.fill(0,-10,100,2,T)
        b.fill(0,5,90,1,'2023-01-01T01:00Z')
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],48.)
        self.assertAlmostEqual(b.units()[0],-5.)
        self.assertAlmostEqual(b.total_pnl(np.ones(4)*90),97.)
    def test_reversal_closed_and_new_short(self):
        b=TradeBook(10000);b.fill(0,10,100,0,T)
        b.fill(0,-15,110,3,'2023-01-01T01:00Z')
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],98.)
        self.assertAlmostEqual(b.units()[0],-5.)
        self.assertAlmostEqual(b.total_pnl(np.ones(4)*110),97.)
    def test_funding_order_allocates_to_correct_inventory(self):
        a=TradeBook(10000);b=TradeBook(10000)
        for book in (a,b):book.fill(0,10,100,0,T)
        ev=[event(0,-20,100)]
        a.apply_hour(ev,[-1,0,0,0],'2023-01-01T01:00Z',funding_order='carried_before_fill')
        b.apply_hour(ev,[1,0,0,0],'2023-01-01T01:00Z',funding_order='new_after_fill')
        self.assertAlmostEqual(a.closed[0]['pnl_usd'],-1.)
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],0.)
        self.assertAlmostEqual(b.total_pnl(np.ones(4)*100),1.)
    def test_stop_after_funding_debit_attributed(self):
        b=TradeBook(10000);b.fill(0,10,100,0,T)
        b.apply_hour([event(0,-10,90,0)],[-1,0,0,0],
            '2023-01-01T01:00Z',funding_order='new_after_fill')
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],-101.)
    def test_200hour_signed_ledger_nav_identity_two_orders(self):
        for order in ('carried_before_fill','new_after_fill'):
            rng=np.random.default_rng(1132);b=TradeBook(10000)
            p=np.ones(4)*100;u=np.zeros(4);cash=10000.
            for t in range(1,201):
                o=p.copy();c=o*np.exp(rng.normal(0,.001,4))
                h=np.maximum(o,c)*1.001;l=np.minimum(o,c)*.999
                w=np.array([.1,-.05,0,0]) if (t//12)%2==0 else np.array([-.06,.1,0,0])
                r=execute_hour(p,o,h,l,c,u,w,cash,np.ones(4)*.05,
                    np.ones(4)*.05,np.ones(4)*.0002,np.ones(4)*1e9,
                    .002,.002,rebalance=((t-1)%12==0),
                    funding_rate=np.array([.0001,-.0001,0,0]),funding_mark=c,
                    funding_event=np.ones(4,bool) if t%8==0 else np.zeros(4,bool),
                    funding_order=order)
                self.assertTrue(r['ok'],(order,t,r.get('reason')))
                b.apply_hour(r['events'],r['funding_by_asset'],
                    f'2023-01-{1+(t//24):02d}T{t%24:02d}:00Z',funding_order=order)
                np.testing.assert_allclose(b.units(),r['units'],atol=1e-8,rtol=0)
                self.assertAlmostEqual(b.initial+b.total_pnl(c),r['equity'],places=6)
                p=c;u=r['units'];cash=r['cash']
    def test_invalid_order_fails_closed(self):
        b=TradeBook(10000)
        with self.assertRaises(ValueError):b.apply_hour([],np.zeros(4),T,funding_order='unknown')
if __name__=='__main__':unittest.main()
