#!/usr/bin/env python3
"""W synthetic signed OCO/atomic/funding oracle, no official PnL."""
import unittest
import numpy as np
from phase1112_w_atomic_ledger import execute_hour
P=np.ones(4)*100
D=np.ones(4)*.1;H=np.ones(4)*.1;Q=np.ones(4)*1e9
Z=np.zeros(4)
def run(o=None,h=None,l=None,c=None,u=None,w=None,cash=10000.,**kw):
    return execute_hour(P,np.asarray(o if o is not None else P,float),
        np.asarray(h if h is not None else P,float),
        np.asarray(l if l is not None else P,float),
        np.asarray(c if c is not None else P,float),
        np.asarray(u if u is not None else Z,float),
        np.asarray(w if w is not None else Z,float),
        cash,D,H,Q,.002,.002,**kw)

class TestWLedger(unittest.TestCase):
    def test_flat_no_trade(self):
        x=run();self.assertTrue(x['ok']);self.assertEqual(x['fees'],0.)
    def test_entry_cost_and_long_stop(self):
        x=run(w=[.2,0,0,0],h=[102,100,100,100],
              l=[90,100,100,100],c=[95,100,100,100])
        self.assertTrue(x['ok']);self.assertEqual(x['units'][0],0.)
        self.assertTrue(any(e['action']=='STOP_FIRST' for e in x['events']))
        self.assertLess(x['equity'],10000.)
    def test_both_touched_stop_first(self):
        x=run(w=[.2,0,0,0],h=[110,100,100,100],
              l=[90,100,100,100],c=[100,100,100,100])
        self.assertTrue(x['ok']);self.assertEqual(x['units'][0],0.)
        self.assertFalse(any(e['action']=='PARTIAL_LIMIT' for e in x['events']))
    def test_limit_reduces_one_third(self):
        x=run(w=[.2,0,0,0],h=[110,100,100,100],
              l=[99,100,100,100],c=[105,100,100,100])
        self.assertTrue(x['ok'])
        self.assertAlmostEqual(x['units'][0],.2*10000/100*2/3)
    def test_signed_funding(self):
        kw={'funding_rate':np.array([.01,.01,0,0]),
            'funding_mark':P,'funding_event':np.array([True,True,False,False])}
        x=run(w=[.2,-.2,0,0],**kw)
        self.assertTrue(x['ok'])
        self.assertAlmostEqual(x['signed_funding_cash_delta'],0.,places=8)
        x=run(w=[.2,0,0,0],**kw)
        self.assertTrue(x['ok']);self.assertLess(x['signed_funding_cash_delta'],0.)
    def test_reversal_flat_first(self):
        x=run(u=[20,0,0,0],w=[-.2,0,0,0],cash=8000.)
        self.assertTrue(x['ok']);self.assertEqual(x['units'][0],0.)
        self.assertTrue(any(e['action']=='ATOMIC_FLAT_REVERSAL' for e in x['events']))
    def test_unexpected_range_rejected(self):
        x=run(h=[120,100,100,100])
        self.assertFalse(x['ok'])
        self.assertEqual(x['reason'],'W_UNANTICIPATED_GAP_OR_RANGE')
    def test_mandatory_capacity_rejected(self):
        x=execute_hour(P,P,P,P,P,Z,np.array([.2,0,0,0]),
                       10000.,D,H,np.zeros(4),.002,.002)
        self.assertFalse(x['ok'])
        self.assertEqual(x['reason'],'W_OPEN_MANDATORY_CAPACITY')
    def test_no_lookahead_for_opening(self):
        a=run(w=[.2,0,0,0],c=[100,100,100,100])
        b=run(w=[.2,0,0,0],c=[102,100,100,100],
              h=[102,100,100,100])
        self.assertTrue(a['ok'] and b['ok'])
        self.assertEqual(a['events'][0],b['events'][0])
if __name__=='__main__':unittest.main()
