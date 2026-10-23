#!/usr/bin/env python3
"""AH1237 causal dollar/BTC-beta neutral residual reversion tests."""
import unittest
import numpy as np
from phase1237_ah_beta_neutral_rv import ah_relative_value_source


class TestAHRV(unittest.TestCase):
    @staticmethod
    def fixture(n=420):
        t=np.arange(n,dtype=float)
        btc=.0004*t+.01*np.sin(t/7)+.004*np.sin(t/13)
        logs=np.column_stack((btc,
            1.3*btc+.012*np.sin(t/19),
            .8*btc+.02*np.cos(t/17),
            1.6*btc+.015*np.sin(t/11)))
        return 100*np.exp(logs)

    def test_active_signed_neutrality(self):
        c=self.fixture()
        w,b=ah_relative_value_source(c)
        self.assertEqual(w.shape,(420,4))
        self.assertEqual(b.shape,(420,4))
        self.assertTrue(np.all(w[:168]==0))
        self.assertGreater(np.count_nonzero(w>0),0)
        self.assertGreater(np.count_nonzero(w<0),0)
        active=np.where(np.abs(w).sum(axis=1)>0)[0]
        self.assertGreater(len(active),100)
        self.assertLess(np.max(np.abs(w[active].sum(axis=1))),1e-7)
        self.assertLess(np.max(np.abs(np.sum(w[active]*b[active],axis=1))),1e-7)
        self.assertTrue(np.all(np.abs(w).sum(axis=1)<=1+1e-10))

    def test_future_perturbation_invariance(self):
        c=self.fixture()
        a=ah_relative_value_source(c)
        c2=c.copy()
        c2[350:]*=np.array([2.,.2,3.,.4])
        b=ah_relative_value_source(c2)
        for x,y in zip(a,b):
            self.assertTrue(np.array_equal(x[:350],y[:350]))

    def test_zero_variance_fails_closed(self):
        c=self.fixture()
        c[:,0]=100.
        w,b=ah_relative_value_source(c)
        self.assertTrue(np.all(w==0))
        self.assertTrue(np.all(b==0))

    def test_deterministic_repeat(self):
        c=self.fixture()
        a=ah_relative_value_source(c)
        b=ah_relative_value_source(c)
        self.assertTrue(np.array_equal(a[0],b[0]))
        self.assertTrue(np.array_equal(a[1],b[1]))

    def test_invalid_price_rejected(self):
        c=self.fixture()
        c[200,0]=0
        with self.assertRaisesRegex(ValueError,'SOURCE_GEOMETRY'):
            ah_relative_value_source(c)


if __name__=='__main__':
    unittest.main()
