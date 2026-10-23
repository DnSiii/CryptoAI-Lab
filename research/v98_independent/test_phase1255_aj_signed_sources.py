#!/usr/bin/env python3
"""V98 AJ1255 preregistered deterministic signed-source and router unit gates."""
import hashlib
import unittest
import numpy as np
from phase1255_aj_signed_sources import (
    growth_core,opportunity,relative_value,stress_recovery,
    regime_router,source_bundle)

def fixture(n=900):
    t=np.arange(n)[:,None]
    c=100*np.exp(t*np.array([.001,-.001,.0004,-.0003])[None,:]+
                 .01*np.sin(t/np.array([13.,17.,19.,23.])))
    h=c*1.0001
    l=c*.9999
    r=np.zeros_like(c)
    e=np.zeros_like(c)
    e[::8]=1.
    r[::8]=np.array([.0001,-.0001,.00015,-.00015])
    return c,h,l,r,e

class TestAJSources(unittest.TestCase):
    def test_growth_dual_speed_signed(self):
        c,*_=fixture()
        w=growth_core(c)
        self.assertTrue(np.any(w[-100:]>0))
        self.assertTrue(np.any(w[-100:]<0))
        self.assertTrue(np.all(np.abs(w).sum(axis=1)<=1.0000001))
        self.assertTrue(np.all(w[:336]==0))

    def test_growth_disagreement_is_flat(self):
        c,*_=fixture()
        c[880:,0]*=np.exp(-.03*np.arange(20))
        w=growth_core(c)
        self.assertEqual(w[-1,0],0.)

    def test_opportunity_breakout_and_ttl(self):
        c=np.full((350,4),100.)
        c[200:210,0]=125.
        c[210:,0]=65.
        h=c*1.0001
        l=c*.9999
        w=opportunity(c,h,l)
        self.assertGreater(w[200,0],0)
        self.assertLess(w[210,0],0)
        self.assertEqual(w[230,0],0)

    def test_rank_rv_exact_dollar_neutral(self):
        c,h,l,r,e=fixture()
        w=relative_value(c,r,e)
        self.assertTrue(np.array_equal(w[400:].sum(axis=1),np.zeros(500)))
        self.assertTrue(np.all(np.abs(w[400:]).sum(axis=1)==1))
        self.assertEqual(set(np.unique(w[400:])),{-.25,.25})

    def test_rank_rv_stable_ties(self):
        c=np.full((400,4),100.)
        r=np.zeros_like(c)
        e=np.zeros_like(c)
        w=relative_value(c,r,e)
        np.testing.assert_array_equal(w[-1],[.25,.25,-.25,-.25])

    def test_rv_funding_affects_ranks(self):
        c,h,l,r,e=fixture()
        baseline=relative_value(c,r,e)
        r[::8,0]=.1
        changed=relative_value(c,r,e)
        self.assertFalse(np.array_equal(baseline[-1],changed[-1]))

    def test_stress_recovery(self):
        c=np.full((550,4),100.)
        c[400:]*=.5
        c[430:]*=1.5
        w=stress_recovery(c)
        self.assertTrue(np.all(w[400]==-.25))
        self.assertTrue(np.any(np.all(w[430:465]==.25,axis=1)))

    def test_router_crisis_rebound(self):
        c=np.full((550,4),100.)
        c[400:]*=.5
        c[430:]*=1.5
        state=regime_router(c)['state']
        self.assertEqual(state[400],'CRISIS')
        self.assertEqual(state[430],'REBOUND')

    def test_router_trend_range(self):
        c=np.full((500,4),100.)
        self.assertEqual(regime_router(c)['state'][-1],'RANGE')
        t=np.arange(500)[:,None]
        drift=np.array([.001,.001,.001,-.0001])[None,:]
        c=100*np.exp(t*drift)
        self.assertEqual(regime_router(c)['state'][-1],'TREND')

    def test_future_invariance(self):
        c,h,l,r,e=fixture()
        a=source_bundle(c,h,l,r,e)
        c[810:]*=1.4
        h[810:]*=1.4
        l[810:]*=1.4
        b=source_bundle(c,h,l,r,e)
        for k in range(4):
            np.testing.assert_array_equal(a[k][:800],b[k][:800])
        np.testing.assert_array_equal(a[4]['state'][:800],b[4]['state'][:800])

    def test_invalid(self):
        c,h,l,r,e=fixture()
        c[0,0]=0.
        with self.assertRaises(ValueError):
            source_bundle(c,h,l,r,e)

    def test_repeat_digest(self):
        c,h,l,r,e=fixture()
        a=source_bundle(c,h,l,r,e)
        b=source_bundle(c,h,l,r,e)
        for i in range(4):
            sha=lambda x:hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
            self.assertEqual(sha(a[i]),sha(b[i]))

if __name__=='__main__':
    unittest.main()
