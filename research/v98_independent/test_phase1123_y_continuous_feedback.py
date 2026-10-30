#!/usr/bin/env python3
"""Y 3000 synthetic adverse books and six feedback contracts, no PnL."""
import unittest
import numpy as np
from phase1123_y_continuous_feedback import max_safe_retention,evaluate,STATES
P=np.ones(4)*100;Q=np.ones(4)*1e9
D=np.ones(4)*.04;H=np.ones(4)*.04;F=np.ones(4)*.0002

class TestYFeedback(unittest.TestCase):
    def test_81_mark_states(self):
        self.assertEqual(STATES.shape,(81,4))
        self.assertEqual(len({tuple(s) for s in STATES}),81)
    def test_max_growth_no_unnecessary_reduction(self):
        u=np.array([5.,-5.,0,0]);cash=10000.
        x=max_safe_retention(P,P,u,cash,D,H,F,Q,.002,.002)
        self.assertTrue(x['ok']);self.assertEqual(x['retention'],1.)
    def test_favorable_long_cap_drift_trimmed(self):
        u=np.array([44.9068,0,0,0]);cash=10000.-4490.68
        x=max_safe_retention(P,P,u,cash,D,H,F,Q,.002,.002)
        self.assertTrue(x['ok']);self.assertLess(x['retention'],1.)
        self.assertTrue(evaluate(x['retention'],P,P,u,cash,D,H,F,Q,.002,.002))
    def test_untradeable_reduction_rejected(self):
        u=np.array([70.,0,0,0]);cash=3000.
        x=max_safe_retention(P,P,u,cash,D,H,F,np.zeros(4),.002,.002)
        self.assertFalse(x['ok'])
        self.assertEqual(x['reason'],'Y_NO_LIQUID_SAFE_RETENTION')
    def test_no_sign_flip_or_increase(self):
        u=np.array([60.,-30.,20.,-10.]);cash=6000.
        x=max_safe_retention(P,P,u,cash,D,H,F,Q,.002,.002)
        self.assertTrue(x['ok'])
        self.assertTrue(np.all(np.abs(x['units'])<=np.abs(u)+1e-8))
        self.assertTrue(np.all(np.sign(x['units'])==np.sign(u)))
    def test_3000_adversarial(self):
        rng=np.random.default_rng(1123);success=0;rejected=0
        for _ in range(3000):
            w=rng.uniform(-.9,.9,4);u=w*10000/P
            cash=10000.-float(np.dot(u,P))
            d=rng.uniform(.001,.3,4);h=rng.uniform(.001,.4,4)
            f=rng.uniform(0,.005,4);q=rng.uniform(1e5,1e9,4)
            x=max_safe_retention(P,P,u,cash,d,h,f,q,.002,.002)
            if x['ok']:
                success+=1
                self.assertTrue(evaluate(x['retention'],P,P,u,cash,d,h,f,q,.002,.002))
                self.assertTrue(np.all(np.abs(x['units'])<=np.abs(u)+1e-8))
            else:rejected+=1
        self.assertEqual(success+rejected,3000)
        self.assertGreater(success,100)
if __name__=='__main__':unittest.main()
