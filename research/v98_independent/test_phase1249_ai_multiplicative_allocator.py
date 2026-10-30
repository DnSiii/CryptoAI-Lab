#!/usr/bin/env python3
"""V98 AI1249 preregistered causal 240h multiplicative allocator tests."""
import unittest,hashlib
import numpy as np
from phase1249_ai_multiplicative_allocator import AIMultiplicativeAllocator,PRIORS

class TestAIAllocator(unittest.TestCase):
    def test_cold_start(self):
        a=AIMultiplicativeAllocator()
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        x=a.decide(np.zeros((4,4)),'TREND')
        self.assertEqual(x['growth_scale'],0.)
        self.assertAlmostEqual(x['weights'].sum(),1.)
    def test_regime_priors(self):
        for state,prior in PRIORS.items():
            a=AIMultiplicativeAllocator()
            x=a.decide(np.zeros((4,4)),state)
            np.testing.assert_allclose(x['weights'],prior)
    def test_previous_close_only(self):
        a=AIMultiplicativeAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        a.decide(s,'TREND')
        x=a.observe(np.array([.02,0,0,0]),np.zeros(4),np.zeros(4))
        self.assertAlmostEqual(x[0],.019)
    def test_signed_funding(self):
        a=AIMultiplicativeAllocator()
        s=np.zeros((4,4));s[0,0]=1.;s[1,0]=-1.
        a.decide(s,'TREND')
        x=a.observe(np.zeros(4),np.array([.01,0,0,0]),
            np.array([1.,0,0,0]))
        self.assertAlmostEqual(x[0],-.011)
        self.assertAlmostEqual(x[1],.009)
    def test_positive_edge(self):
        a=AIMultiplicativeAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        for _ in range(245):
            a.observe(np.array([.004,0,0,0]),np.zeros(4),np.zeros(4))
            x=a.decide(s,'TREND')
        self.assertGreater(x['growth_scale'],0.)
        self.assertTrue(np.isfinite(x['signed_target']).all())
        self.assertAlmostEqual(x['weights'].sum(),1.)
    def test_deterministic(self):
        def trial():
            a=AIMultiplicativeAllocator()
            s=np.zeros((4,4));s[0,0]=1.;s[1,1]=-1.
            rows=[]
            for t in range(300):
                a.observe(np.array([.001*np.sin(t),.002,0,0]),
                    np.zeros(4),np.zeros(4))
                x=a.decide(s,'DISPERSION')
                rows.extend(x['weights']);rows.append(x['growth_scale'])
            return hashlib.sha256(np.asarray(rows,dtype='<f8').tobytes()).hexdigest()
        self.assertEqual(trial(),trial())
    def test_invalid(self):
        a=AIMultiplicativeAllocator()
        with self.assertRaises(ValueError):
            a.decide(np.ones((4,4)),'TREND')
        with self.assertRaises(ValueError):
            a.decide(np.zeros((4,4)),'UNKNOWN')
    def test_negative_edge_no_fake_profit(self):
        a=AIMultiplicativeAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        for _ in range(245):
            a.observe(np.array([-.004,0,0,0]),np.zeros(4),np.zeros(4))
            x=a.decide(s,'TREND')
        self.assertGreaterEqual(x['growth_scale'],0.)
        self.assertTrue(np.isfinite(x['signed_target']).all())

if __name__=='__main__':unittest.main()
