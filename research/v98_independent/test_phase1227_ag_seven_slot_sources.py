#!/usr/bin/env python3
"""AG1227 causal seven-slot source and actual-NAV stress tests."""
import unittest
import numpy as np
from phase1227_ag_seven_slot_sources import (
    causal_sources,AGStress,AGAllocator,PATHS,BASE_CASH)


class TestAGSources(unittest.TestCase):
    @staticmethod
    def fixture(n=400):
        t=np.arange(n,dtype=float)
        trends=np.array([.0008,.0004,-.0003,.0006])
        c=100*np.exp(t[:,None]*trends+
                     .006*np.sin(t[:,None]/np.array([11.,13.,17.,19.])))
        q=1e12*(1+.5*np.sin(t[:,None]/7+np.arange(4))**2)
        return c,q

    def test_shapes_and_activity(self):
        c,q=self.fixture()
        g,op,rv,r=causal_sources(c,q)
        self.assertEqual(g.shape,(400,4))
        self.assertEqual(op.shape,(400,4))
        self.assertEqual(rv.shape,(400,4))
        self.assertEqual(r.shape,(400,))
        self.assertGreater(np.count_nonzero(g),0)
        self.assertGreater(np.count_nonzero(op),0)
        self.assertGreater(np.count_nonzero(rv),0)
        self.assertGreater(np.count_nonzero(r),0)
        self.assertTrue(np.all(g>=0))
        self.assertTrue(np.all(op>=0))
        self.assertTrue(np.all(rv>=0))

    def test_future_perturbation_invariance(self):
        c,q=self.fixture()
        a=causal_sources(c,q)
        c2=c.copy();q2=q.copy()
        c2[330:]*=np.array([3.,.2,5.,.3])
        q2[330:]*=100.
        b=causal_sources(c2,q2)
        for x,y in zip(a,b):
            self.assertTrue(np.array_equal(x[:329],y[:329]))

    def test_no_warmup_execution(self):
        c,q=self.fixture()
        for x in causal_sources(c,q):
            self.assertTrue(np.all(x[:169]==0))

    def test_stress_hysteresis_and_recovery(self):
        x=AGStress()
        for _ in range(48): self.assertEqual(x.step(10000.,0),BASE_CASH)
        self.assertEqual(x.step(8000.,-.20),.45)
        for _ in range(23): self.assertEqual(x.step(10000.,.05),.45)
        self.assertEqual(x.step(10000.,0),BASE_CASH)
        self.assertGreaterEqual(x.active_hours,24)

    def test_path_ablations_do_not_mutate_sources(self):
        c,q=self.fixture()
        g,op,rv,r=causal_sources(c,q)
        g0=g.copy();o0=op.copy();rv0=rv.copy()
        for path in PATHS:
            a=AGAllocator()
            for t in range(169,400):
                prev=np.log(c[t]/c[t-1])
                mu=a.step(prev,g[t],op[t],rv[t],r[t],.1,path)
                self.assertEqual(mu.shape,(4,))
                self.assertTrue(np.isfinite(mu).all())
        self.assertTrue(np.array_equal(g,g0))
        self.assertTrue(np.array_equal(op,o0))
        self.assertTrue(np.array_equal(rv,rv0))

    def test_deterministic_source_and_allocator(self):
        c,q=self.fixture()
        g,op,rv,r=causal_sources(c,q)
        a=AGAllocator();b=AGAllocator()
        for t in range(169,400):
            lr=np.log(c[t]/c[t-1])
            x=a.step(lr,g[t],op[t],rv[t],r[t],.1,'AG_full')
            y=b.step(lr,g[t],op[t],rv[t],r[t],.1,'AG_full')
            self.assertTrue(np.array_equal(x,y))


if __name__=='__main__':
    unittest.main()
