import unittest
import numpy as np
from phase1146_z_inventory_ledger import execute_hour,risk_corners,signed_mark

def args(**kw):
    a=dict(prior=np.full(4,100.),opening=np.full(4,100.),
        high=np.full(4,101.),low=np.full(4,99.),closing=np.full(4,100.),
        carried_units=np.zeros(4),desired_weights=np.array([.1,-.1,0.,0.]),
        cash=10000.,prior_down=np.full(4,.15),prior_up=np.full(4,.15),
        prior_funding_bound=np.full(4,.001),prior_quote=np.full(4,1e8),
        fee=.0007,order='new_after_fill',funding_rate=np.zeros(4),
        funding_mark_bounds=np.full((4,2),np.nan),
        funding_event=np.zeros(4,bool),rebalance=True)
    a.update(kw)
    return a

class TestLedger(unittest.TestCase):
    def test_signed_long_short_and_self_financing(self):
        x=execute_hour(**args())
        self.assertTrue(x['ok'],x.get('reason'))
        self.assertEqual(len(x['events']),2)
        self.assertAlmostEqual(x['equity'],x['cash']+sum(x['units']*100),places=8)
        self.assertGreater(x['fees'],0)
        self.assertLess(x['equity'],10000.)
    def test_zero_quote_fail_closed(self):
        x=execute_hour(**args(prior_quote=np.zeros(4)))
        self.assertEqual(x['reason'],'Z1146_OPEN_CAPACITY')
    def test_native_signed_mark_adversity(self):
        marks=np.array([[99,101],[99,101],[np.nan,np.nan],[np.nan,np.nan]])
        m=signed_mark(np.array([1,-1,0,0]),np.array([.01,.01,0,0]),
                      marks,np.array([True,True,False,False]),np.full(4,100.))
        self.assertEqual(m.tolist()[:2],[101,99])
        x=execute_hour(**args(carried_units=np.array([1.,-1.,0.,0.]),
            desired_weights=np.array([.01,-.01,0.,0.]),
            funding_rate=np.array([.01,.01,0,0]),funding_mark_bounds=marks,
            funding_event=np.array([True,True,False,False]),
            rebalance=False,order='carried_before_fill'))
        self.assertTrue(x['ok'],x.get('reason'))
        self.assertAlmostEqual(x['funding_cash_delta'],-.02,places=8)
    def test_gap_stops_before_new_entries(self):
        x=execute_hour(**args(carried_units=np.array([1.,0,0,0]),
            opening=np.array([80.,100,100,100]),
            low=np.array([79.,99,99,99]),high=np.array([100.,101,101,101]),
            closing=np.array([85.,100,100,100]),
            desired_weights=np.array([.3,.2,0,0]),prior_down=np.full(4,.1)))
        self.assertTrue(x['ok'],x.get('reason'))
        self.assertTrue(x['basket_stop'])
        self.assertTrue(np.allclose(x['units'],0))
        self.assertEqual(x['events'][0]['action'],'GAP_REDUCE_ONLY')
    def test_stop_capacity_fails_not_fabricated(self):
        x=execute_hour(**args(carried_units=np.array([1.,0,0,0]),
            desired_weights=np.array([.01,0,0,0]),
            low=np.array([84.,99,99,99]),high=np.full(4,101.),
            closing=np.array([90.,100,100,100]),
            prior_quote=np.array([1.,1e8,1e8,1e8]),rebalance=False))
        self.assertIn(x['reason'],('Z1146_OPEN_CAPACITY','Z1146_STOP_CAPACITY'))
    def test_81_corner_asset_and_equity_violation(self):
        p=np.array([[50.,100,100,100],[100,100,100,100],[150,100,100,100]])
        self.assertFalse(risk_corners(0.,np.array([1.,0,0,0]),p,100.)['ok'])
    def test_prior_weights_unaffected_by_current_candle(self):
        a=args()
        b=args(high=np.full(4,130.),low=np.full(4,70.))
        x=execute_hour(**a);y=execute_hour(**b)
        self.assertEqual(x['planned_units'],y['planned_units'])
    def test_both_funding_orders_supported(self):
        for order in ('new_after_fill','carried_before_fill'):
            x=execute_hour(**args(order=order))
            self.assertTrue(x['ok'])

if __name__=='__main__':unittest.main()
