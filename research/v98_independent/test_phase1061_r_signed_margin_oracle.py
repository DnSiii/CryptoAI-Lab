#!/usr/bin/env python3
"""V98 R signed LP tests: 16 corners, signed cash and capital scale."""
import unittest
import numpy as np
from phase1061_r_signed_margin_oracle import execute,audit,corners,PARTICIPATION

class RMarginTest(unittest.TestCase):
    def test_sixteen(self):self.assertEqual(corners(np.full(4,.1),np.full(4,.2)).shape,(16,4))
    def test_invalid_shock(self):
        with self.assertRaises(ValueError):corners(np.full(4,1.0),np.zeros(4))
    def test_zero_position(self):self.assertTrue(audit(10000,np.zeros(4),np.ones(4),np.full(4,.1),np.full(4,.1))['ok'])
    def test_signed_short(self):
        r=execute(10000,np.zeros(4),np.ones(4),np.ones(4)*1e8,np.array([-.2,.2,0,0]),.0007,np.full(4,.1),np.full(4,.1))
        self.assertTrue(r['ok'],r);self.assertLess(r['units'][0],0);self.assertGreater(r['units'][1],0)
    def test_capacity(self):
        r=execute(1e6,np.zeros(4),np.ones(4),np.ones(4)*100,np.array([.2,0,0,0]),.0007,np.full(4,.05),np.full(4,.05),mode='capacity_1m')
        self.assertTrue(r['ok'],r);self.assertLessEqual(np.abs(r['trade_usd']).max(),PARTICIPATION*100+1e-4)
    def test_extreme_risk(self):
        r=execute(10000,np.zeros(4),np.ones(4),np.ones(4)*1e8,np.array([.4,.2,-.2,0]),.002,np.full(4,.70),np.full(4,1.5))
        self.assertTrue(r['ok'],r);self.assertTrue(audit(r['cash'],r['units'],np.ones(4),np.full(4,.70),np.full(4,1.5),baseline=10000)['ok'])
    def test_randomized_signed(self):
        rng=np.random.default_rng(321)
        for _ in range(100):
            initial=float(rng.choice([10000,1e6,1e7]));opening=rng.uniform(10,1000,4)
            w=rng.normal(0,.15,4);w*=min(1.,.44/max(abs(w)),.68/max(abs(sum(w)),1e-12),1.19/sum(abs(w)))
            d=rng.uniform(0,.3,4);h=rng.uniform(0,.4,4)
            result=execute(initial,np.zeros(4),opening,np.full(4,1e12),w,.0012,d,h)
            self.assertTrue(result['ok'],result)
            self.assertTrue(audit(result['cash'],result['units'],opening,d,h,baseline=initial)['ok'])
    def test_causal_interface(self):
        # No current/future OHLC or funding arguments accepted by execute().
        with self.assertRaises(TypeError):execute(10000,np.zeros(4),np.ones(4),np.ones(4),np.zeros(4),.001,np.zeros(4),np.zeros(4),future_close=np.ones(4))

if __name__=='__main__':unittest.main()
