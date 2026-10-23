#!/usr/bin/env python3
import unittest
import numpy as np
from phase1117_x_contingent_governor import STATES,feasible,maximize
P=np.ones(4)*100;D=np.ones(4)*.1;H=np.ones(4)*.1
F=np.ones(4)*.0005;Q=np.ones(4)*1e9
class TestXGovernor(unittest.TestCase):
    def test_256_states(self):
        self.assertEqual(STATES.shape,(256,4))
        self.assertEqual(len({tuple(x) for x in STATES}),256)
    def test_basket_stops_cover_hedge_removal(self):
        w=maximize([.4,.4,-.4,0],P,D,H,F,Q,1e6)
        self.assertTrue(feasible(w,P,D,H,F,Q,1e6))
        self.assertGreater(np.abs(w).sum(),0)
        self.assertEqual(feasible(w,P,D,H,F,Q,1e6,details=True)['basket_stop_states'],175)
    def test_quote_cap_and_invalid(self):
        out=maximize([1,1,1,1],P,D,H,F,np.zeros(4),1e6)
        self.assertTrue(np.all(out==0))
        with self.assertRaises(ValueError):
            maximize([1,2,3],P,D,H,F,Q,1e6)
    def test_2000_adversarial(self):
        rng=np.random.default_rng(1117)
        for _ in range(2000):
            w=rng.uniform(-2,2,4);d=rng.uniform(.001,.5,4)
            h=rng.uniform(.001,.8,4);f=rng.uniform(0,.02,4)
            q=rng.uniform(1e5,5e9,4)
            cap=float(rng.choice([1e4,1e6,1e7]))
            out=maximize(w,P,d,h,f,q,cap)
            self.assertTrue(feasible(out,P,d,h,f,q,cap))
if __name__=='__main__':unittest.main()
