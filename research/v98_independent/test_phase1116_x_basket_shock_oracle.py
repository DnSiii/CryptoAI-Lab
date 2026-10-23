#!/usr/bin/env python3
"""X 2000 adverse basket executions; synthetic only, no historical PnL."""
import unittest
import numpy as np
from phase1116_x_basket_shock_oracle import execute_preplaced_basket
P=np.ones(4)*100;Z=np.zeros(4);D=np.ones(4)*.1;H=np.ones(4)*.1;Q=np.ones(4)*1e9
def run(u=None,h=None,l=None,c=None,q=None,fee=.002,slip=.002,**kw):
    u=np.asarray(Z if u is None else u,float)
    h=np.asarray(P if h is None else h,float)
    l=np.asarray(P if l is None else l,float)
    c=np.asarray(P if c is None else c,float)
    q=np.asarray(Q if q is None else q,float)
    cash=10000.-float(np.dot(u,P))
    return execute_preplaced_basket(P,P,h,l,c,u,cash,D,H,q,fee,slip,**kw)

class TestXBasket(unittest.TestCase):
    def test_no_exposure_unrelated_shock(self):
        x=run(h=[100,140,100,100])
        self.assertTrue(x['ok']);self.assertFalse(x['basket_stop'])
    def test_short_hedge_stop_flattens_longs(self):
        x=run(u=[30,30,-30,0],h=[100,100,130,100],c=[100,100,125,100])
        self.assertTrue(x['ok']);self.assertTrue(x['basket_stop'])
        self.assertTrue(np.all(x['units']==0));self.assertEqual(len(x['events']),3)
    def test_new_extreme_not_automatic_reject(self):
        x=run(u=[20,0,0,0],l=[65,100,100,100],c=[70,100,100,100])
        self.assertTrue(x['ok']);self.assertTrue(x['basket_stop'])
        self.assertAlmostEqual(x['events'][0]['fill_price'],65*(1-.002))
    def test_both_touched_stop_first(self):
        x=run(u=[20,-10,0,0],h=[110,100,100,100],l=[90,100,100,100])
        self.assertTrue(x['ok']);self.assertTrue(x['basket_stop'])
        self.assertFalse(any(e['action']=='PARTIAL_LIMIT' for e in x['events']))
    def test_partial_limit_one_third(self):
        x=run(u=[20,0,0,0],h=[110,100,100,100],
              l=[99,100,100,100],c=[105,100,100,100])
        self.assertTrue(x['ok']);self.assertFalse(x['basket_stop'])
        self.assertAlmostEqual(x['units'][0],20*2/3)
    def test_untradeable_exit_fails_closed(self):
        x=run(u=[20,0,0,0],l=[90,100,100,100],q=[100,1e9,1e9,1e9])
        self.assertFalse(x['ok'])
        self.assertEqual(x['reason'],'X_UNTRADEABLE_MANDATORY_EXIT')
    def test_signed_funding_only_survivors(self):
        kw={'funding_rate':np.array([.01,0,0,0]),
            'funding_mark':P,'funding_event':np.array([True,False,False,False])}
        a=run(u=[20,0,0,0],**kw)
        b=run(u=[20,0,0,0],l=[90,100,100,100],**kw)
        self.assertTrue(a['ok'] and b['ok'])
        self.assertAlmostEqual(a['signed_funding_cash_delta'],-20.)
        self.assertAlmostEqual(b['signed_funding_cash_delta'],0.)
    def test_2000_seeded_shock_books(self):
        rng=np.random.default_rng(1116)
        passed=0;rejected=0
        for _ in range(2000):
            u=rng.uniform(-30,30,4)
            hi=100*(1+rng.uniform(0,.5,4))
            lo=100*(1-rng.uniform(0,.5,4))
            c=np.minimum(hi,np.maximum(lo,rng.uniform(60,140,4)))
            x=run(u=u,h=hi,l=lo,c=c)
            if x['ok']:
                passed+=1
                if x['basket_stop']:
                    self.assertTrue(np.abs(x['units']).max()<1e-8)
            else:rejected+=1
        self.assertEqual(passed+rejected,2000)
        self.assertGreater(passed,100)
if __name__=='__main__':unittest.main()
