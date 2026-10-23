import unittest
import numpy as np
from phase1040_q_signed_margin_oracle import corner_audit,execute_signed,factors

class SignedQTests(unittest.TestCase):
    def test_sixteen_corners(self):
        self.assertEqual(factors(np.full(4,.1),np.full(4,.2)).shape,(16,4))
    def test_short_liability(self):
        self.assertTrue(corner_audit(120,np.array([-1.,0,0,0]),np.array([20.,20,20,20]),np.full(4,.1),np.full(4,.1))['ok'])
        self.assertFalse(corner_audit(120,np.array([-1.,0,0,0]),np.array([20.,20,20,20]),np.full(4,.1),np.array([10.,0,0,0]))['ok'])
    def test_zero_target_cash(self):
        r=execute_signed(1000,np.zeros(4),np.ones(4)*100,np.ones(4)*1e8,np.zeros(4),.001,np.ones(4)*.1,np.ones(4)*.1)
        self.assertTrue(r['ok']);self.assertAlmostEqual(r['cash'],1000)
    def test_signed_pair_target(self):
        r=execute_signed(1000,np.zeros(4),np.ones(4)*100,np.ones(4)*1e8,np.array([.20,-.20,0,0]),.001,np.ones(4)*.1,np.ones(4)*.1)
        self.assertTrue(r['ok'],r);self.assertGreater(r['units'][0],0);self.assertLess(r['units'][1],0)
        self.assertTrue(corner_audit(r['cash'],r['units'],np.ones(4)*100,np.ones(4)*.1,np.ones(4)*.1,baseline=1000)['ok'])
    def test_participation(self):
        r=execute_signed(1000,np.zeros(4),np.ones(4)*100,np.ones(4)*100,np.array([.20,-.20,0,0]),.001,np.ones(4)*.1,np.ones(4)*.1)
        self.assertTrue(r['ok'],r);self.assertLessEqual(abs(r['trade_usd'][0]),1+1e-6)
    def test_adversarial_signed_states(self):
        rng=np.random.default_rng(1040)
        passed=0
        for _ in range(250):
            opening=np.exp(rng.uniform(2,7,4));w=rng.uniform(-.2,.2,4)
            w-=w.mean();q=np.full(4,1e8)
            down=rng.uniform(.01,.25,4);up=rng.uniform(.01,.3,4)
            r=execute_signed(10000,np.zeros(4),opening,q,w,.001,down,up,mode='immediate')
            if r['ok']:
                passed+=1
                self.assertTrue(corner_audit(r['cash'],r['units'],opening,down,up,baseline=10000)['ok'])
        self.assertGreater(passed,150)
    def test_invalid(self):
        with self.assertRaises(ValueError):factors([.1]*3,[.2]*4)
        with self.assertRaises(ValueError):execute_signed(1000,np.zeros(4),np.ones(4),np.ones(4),np.array([2,0,0,0]),.001,np.ones(4)*.1,np.ones(4)*.1)

if __name__=='__main__':unittest.main()
