#!/usr/bin/env python3
"""W 256-state adversarial contract, synthetic only, no OHLC/PnL."""
import unittest
import numpy as np
from phase1110_w_256state_governor import (
    STATES,max_feasible_w,executable_256_feasible,N,ITERATIONS)
P=np.array([30000.,2000.,300.,40.])
D=np.array([.09,.12,.16,.24]);H=np.array([.08,.10,.14,.22])
F=np.array([.0003,.0004,.0005,.0006]);Q=np.array([5e9,2e9,1e9,5e8])
CAP=1e6
def check(w,capital=CAP,q=Q,d=D,h=H,f=F):
    return executable_256_feasible(w,P,d,h,f,q,capital)
def maximize(w,capital=CAP,q=Q,d=D,h=H,f=F):
    return max_feasible_w(w,P,d,h,f,q,capital)

class TestWGovernor(unittest.TestCase):
    def test_exact_256_states_and_32_bisections(self):
        self.assertEqual(STATES.shape,(256,4))
        self.assertEqual(len({tuple(x) for x in STATES}),256)
        self.assertEqual(ITERATIONS,32)
    def test_zero_and_nonzero_growth(self):
        self.assertTrue(check(np.zeros(N)))
        out=maximize([2.,2.,2.,2.])
        self.assertTrue(check(out));self.assertTrue(np.any(out>0))
    def test_stopped_short_hedge_cannot_unmask_longs(self):
        raw=np.array([.4,.4,-.4,0.])
        self.assertFalse(check(raw))
        out=maximize(raw)
        self.assertTrue(check(out))
        self.assertLess(np.max(np.abs(out)),.4)
        self.assertTrue(np.any((STATES[:,0]==0)&(STATES[:,1]==0)&(STATES[:,2]==2)))
    def test_partial_limit_then_hedge_stop(self):
        out=maximize([.4,.4,-.4,0.])
        self.assertTrue(check(out))
        self.assertTrue(np.any((STATES[:,0]==3)&(STATES[:,1]==0)&(STATES[:,2]==2)))
    def test_liquidity_limits_growth(self):
        q=np.ones(4)*1e5
        out=maximize([1.,1.,1.,1.],capital=1e7,q=q)
        self.assertTrue(check(out,capital=1e7,q=q))
        self.assertLessEqual(np.abs(out).max(),1e-4)
    def test_zero_quote_no_trade(self):
        out=maximize([1.,-1.,1.,-1.],q=np.zeros(4))
        self.assertTrue(np.all(out==0))
    def test_more_funding_does_not_increase_exposure(self):
        raw=[.5,-.4,.5,-.3]
        a=maximize(raw,f=np.zeros(4))
        b=maximize(raw,f=np.ones(4)*.03)
        self.assertLessEqual(np.abs(b).sum(),np.abs(a).sum()+1e-6)
    def test_reject_invalid_prior(self):
        for bad in ([np.nan,0,0,0],[1,2,3],[np.inf,0,0,0]):
            with self.assertRaises(ValueError):maximize(bad)
        with self.assertRaises(ValueError):maximize([1,0,0,0],capital=0)
        with self.assertRaises(ValueError):maximize([1,0,0,0],d=np.ones(4))
    def test_quantization_and_reproducibility(self):
        a=maximize([.75,-.2,.5,-.3]);b=maximize([.75,-.2,.5,-.3])
        np.testing.assert_array_equal(a,b)
        np.testing.assert_allclose(a*1e6,np.round(a*1e6),atol=1e-8,rtol=0)
    def test_3000_seeded_adversarial_books(self):
        rng=np.random.default_rng(1110)
        for _ in range(3000):
            raw=rng.uniform(-2.,2.,4)
            d=rng.uniform(.001,.45,4);h=rng.uniform(.001,.65,4)
            f=rng.uniform(0,.02,4);q=rng.uniform(1e5,5e9,4)
            capital=float(rng.choice([1e4,1e6,1e7]))
            out=maximize(raw,capital,q,d,h,f)
            self.assertTrue(check(out,capital,q,d,h,f))
            nz=np.abs(out)>0
            self.assertTrue(np.all(np.sign(out[nz])==np.sign(raw[nz])))
if __name__=='__main__':unittest.main()
