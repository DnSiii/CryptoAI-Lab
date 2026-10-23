"""V governor deterministic maximum feasible scale under 16-corner survival."""
import unittest
import numpy as np
from phase1101_v_robust_governor import max_feasible_weights,all_corners_feasible

class VGovernorTests(unittest.TestCase):
    def setUp(self):
        self.p=np.array([100.,120.,90.,140.])
        self.d=np.array([.03,.04,.05,.06]);self.h=np.array([.04,.05,.06,.07])
        self.f=np.full(4,.0003)
    def test_saturated_raw_gets_robust_slack(self):
        w=np.array([.44998,.2,-.1,0.])
        out=max_feasible_weights(w,self.p,self.d,self.h,self.f)
        self.assertTrue(all_corners_feasible(out,self.p,self.d,self.h,self.f))
        self.assertLess(abs(out[0]),.44998)
        self.assertGreater(abs(out[0]),.25)
    def test_maximize_feasible_not_minimize_risk(self):
        w=np.array([.5,.3,-.2,.1]);out=max_feasible_weights(w,self.p,self.d,self.h,self.f)
        self.assertTrue(all_corners_feasible(out,self.p,self.d,self.h,self.f))
        ratio=max(abs(out))/max(abs(w))
        self.assertGreater(ratio,.3)
        if ratio<.999:
            self.assertFalse(all_corners_feasible((ratio+.0001)*w,self.p,self.d,self.h,self.f))
    def test_zero_no_positions(self):
        self.assertTrue((max_feasible_weights(np.zeros(4),self.p,self.d,self.h,self.f)==0).all())
    def test_invalid_nonfinite_fails(self):
        with self.assertRaisesRegex(ValueError,'PRIOR_INPUT'):
            max_feasible_weights(np.array([np.nan,0,0,0]),self.p,self.d,self.h,self.f)
    def test_3000_seeded_adversarial_books(self):
        rng=np.random.default_rng(1101)
        for _ in range(3000):
            w=rng.uniform(-1.5,1.5,4)
            d=rng.uniform(0,.35,4);h=rng.uniform(0,.4,4)
            f=rng.uniform(0,.02,4)
            out=max_feasible_weights(w,self.p,d,h,f)
            self.assertTrue(all_corners_feasible(out,self.p,d,h,f))
            self.assertLessEqual(abs(out).max(),.45+1e-9)
            self.assertLessEqual(abs(out.sum()),.75+1e-9)
            self.assertLessEqual(abs(out).sum(),1.35+1e-9)
    def test_signed_short_long(self):
        for w in (np.array([-.8,.6,-.3,.2]),np.array([1.,1.,1.,1.]),
                  np.array([-1.,-1.,-1.,-1.])):
            out=max_feasible_weights(w,self.p,self.d,self.h,self.f)
            self.assertTrue(all_corners_feasible(out,self.p,self.d,self.h,self.f))
            self.assertTrue(np.all((out==0)|(np.sign(out)==np.sign(w))))

if __name__=='__main__':unittest.main()
