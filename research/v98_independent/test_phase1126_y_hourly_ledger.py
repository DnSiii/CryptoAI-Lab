#!/usr/bin/env python3
"""Y synthetic hourly accounting, funding, stop-first and causality tests."""
import unittest
import numpy as np
from phase1126_y_hourly_ledger import execute_hour
P=np.ones(4)*100;Z=np.zeros(4);D=np.ones(4)*.05
Q=np.ones(4)*1e9;F=np.ones(4)*.0002

def run(*,u=Z,w=Z,cash=10000.,o=P,h=None,l=None,c=P,rebalance=False,
        rate=Z,event=None,quote=Q):
    o=np.asarray(o,float);c=np.asarray(c,float)
    if h is None:h=np.maximum(o,c)*1.001
    if l is None:l=np.minimum(o,c)*.999
    return execute_hour(P,o,h,l,c,u,w,cash,D,D,F,quote,.002,.002,
        rebalance=rebalance,funding_rate=rate,funding_mark=c,
        funding_event=np.zeros(4,bool) if event is None else event)

class TestYHourlyLedger(unittest.TestCase):
    def test_flat_no_false_pnl(self):
        r=run()
        self.assertTrue(r['ok'],r);self.assertEqual(r['equity'],10000.)
        self.assertEqual(r['fees'],0.)
    def test_open_entry_self_financing(self):
        r=run(w=np.array([.2,0,0,0]),rebalance=True)
        self.assertTrue(r['ok'],r)
        self.assertGreater(r['fees'],0)
        self.assertLess(r['equity'],10000.)
        self.assertAlmostEqual(r['cash']+np.dot(r['units'],P),r['equity'])
    def test_funding_signed_long_pays_short_receives(self):
        e=np.ones(4,bool);rate=np.array([.001,.001,0,0])
        u=np.array([10.,-10.,0,0]);cash=10000.
        x=run(u=u,cash=cash,rate=rate,event=e)
        self.assertTrue(x['ok'],x);self.assertAlmostEqual(x['funding_cash_delta'],0.)
        y=run(u=np.array([10.,0,0,0]),cash=9000.,rate=rate,event=e)
        self.assertTrue(y['ok'],y);self.assertAlmostEqual(y['funding_cash_delta'],-1.)
    def test_adverse_gap_exit_precedes_alpha(self):
        u=np.array([20.,0,0,0]);o=np.array([94.,100.,100.,100.])
        r=run(u=u,cash=8000.,o=o,c=o,w=np.array([.3,0,0,0]),rebalance=True)
        self.assertTrue(r['basket_stop']);self.assertTrue(np.all(r['units']==0))
    def test_intrabar_concentration_cannot_be_hidden_by_close(self):
        u=np.array([44.9,0,0,0]);cash=5510.
        h=np.array([115.,100.1,100.1,100.1]);l=np.ones(4)*99.9
        r=run(u=u,cash=cash,h=h,l=l)
        self.assertFalse(r['ok']);self.assertEqual(r['reason'],'Y1126_INTRABAR_ASSET')
    def test_stop_cannot_erase_funding_debit(self):
        u=np.array([20.,0,0,0]);cash=8000.
        lo=np.array([94.,99.9,99.9,99.9]);hi=np.array([100.1]*4)
        rate=np.array([.001,0,0,0]);event=np.ones(4,bool)
        r=run(u=u,cash=cash,h=hi,l=lo,rate=rate,event=event)
        self.assertTrue(r['basket_stop']);self.assertAlmostEqual(r['funding_cash_delta'],-2.)
    def test_open_capacity_hard_failure(self):
        r=run(w=np.array([.2,0,0,0]),rebalance=True,quote=np.zeros(4))
        self.assertFalse(r['ok']);self.assertEqual(r['reason'],'Y1126_OPEN_CAPACITY')
    def test_plan_independent_of_future_open(self):
        u=np.array([20.,-5.,0,0]);w=np.array([.1,-.1,0,0])
        x=run(u=u,w=w,cash=8500.,rebalance=True)
        y=run(u=u,w=w,cash=8500.,rebalance=True,o=np.ones(4)*101,c=np.ones(4)*101)
        self.assertEqual(x['planned_units'],y['planned_units'])
    def test_synthetic_adversarial_accounting(self):
        rng=np.random.default_rng(1126)
        successes=failures=0
        for i in range(300):
            w=rng.uniform(-.25,.25,4)
            o=100*rng.uniform(.98,1.02,4)
            h=o*rng.uniform(1,1.06,4);l=o*rng.uniform(.94,1,4)
            c=rng.uniform(l,h)
            r=run(w=w,rebalance=True,o=o,h=h,l=l,c=c)
            if r['ok']:
                successes+=1
                self.assertAlmostEqual(r['equity'],r['cash']+np.dot(r['units'],c),places=7)
            else:failures+=1
        self.assertEqual(successes+failures,300)
        self.assertGreater(successes,0)
if __name__=='__main__':unittest.main()
