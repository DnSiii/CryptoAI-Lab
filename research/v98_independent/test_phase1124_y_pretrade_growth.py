#!/usr/bin/env python3
import unittest
import numpy as np
from phase1124_y_pretrade_growth import maximize,feasible
P=np.ones(4)*100;D=np.ones(4)*.05;H=np.ones(4)*.05
F=np.ones(4)*.0002;Q=np.ones(4)*1e9
class TestYPretrade(unittest.TestCase):
    def test_growth_nonzero_and_safe(self):
        w=maximize([1.,.8,-.6,.3],P,D,H,F,Q,1e6)
        self.assertTrue(feasible(w,P,D,H,F,Q,1e6))
        self.assertGreater(np.abs(w).sum(),0)
    def test_no_quote_no_position(self):
        w=maximize([1.,1.,1.,1.],P,D,H,F,np.zeros(4),1e6)
        self.assertTrue(np.all(w==0))
    def test_2000_adversarial(self):
        rng=np.random.default_rng(1124)
        for _ in range(2000):
            raw=rng.uniform(-2,2,4)
            d=rng.uniform(.001,.5,4);h=rng.uniform(.001,.8,4)
            f=rng.uniform(0,.02,4);q=rng.uniform(1e5,5e9,4)
            cap=float(rng.choice([1e4,1e6,1e7]))
            out=maximize(raw,P,d,h,f,q,cap)
            self.assertTrue(feasible(out,P,d,h,f,q,cap))
if __name__=='__main__':unittest.main()
