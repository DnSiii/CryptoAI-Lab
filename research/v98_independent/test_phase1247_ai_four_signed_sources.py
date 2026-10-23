#!/usr/bin/env python3
"""V98 AI1247 preregistered causal signed sources and router unit tests."""
import unittest,hashlib
import numpy as np
from phase1247_ai_four_signed_sources import (
    growth_core,opportunity,relative_value,stress_factor,
    regime_router,source_bundle)

def smooth(n=330,drift=(.001,-.001,.0005,-.0005)):
    t=np.arange(n)[:,None]
    c=100*np.exp(t*np.asarray(drift)[None,:]+
        .008*np.sin(t/np.array([9.,11.,13.,15.])))
    h=c*1.0001;l=c*.9999
    r=np.zeros_like(c);e=np.zeros_like(c)
    return c,h,l,r,e

class TestAISources(unittest.TestCase):
    def test_growth_signed(self):
        c,h,l,r,e=smooth()
        x=growth_core(c,r,e)
        self.assertTrue(np.any(x[-50:]>0))
        self.assertTrue(np.any(x[-50:]<0))
        self.assertTrue(np.all(np.abs(x).sum(axis=1)<=1.0000001))
    def test_growth_funding_changes_sign(self):
        c,h,l,r,e=smooth()
        e[::8]=1.;r[::8,0]=.01
        a=growth_core(c,np.zeros_like(c),np.zeros_like(c))
        b=growth_core(c,r,e)
        self.assertFalse(np.array_equal(a[-1],b[-1]))
    def test_opportunity_signed_and_ttl(self):
        c=np.full((300,4),100.)
        c[160:180,0]=120.
        c[180:,0]=70.
        h=c*1.0001;l=c*.9999
        x=opportunity(c,h,l)
        self.assertGreater(x[160,0],0)
        self.assertLess(x[180,0],0)
        self.assertEqual(x[190,0],0)
    def test_rv_beta_neutral(self):
        c,h,l,r,e=smooth()
        w,b=relative_value(c)
        active=np.flatnonzero(np.abs(w).sum(axis=1)>0)
        self.assertGreater(len(active),0)
        for t in active:
            self.assertLess(abs(w[t].sum()),1e-8)
            self.assertLess(abs(w[t]@b[t]),1e-8)
    def test_stress_preposition_and_release(self):
        c=np.full((280,4),100.)
        c[120:]*=.70
        w=stress_factor(c)
        self.assertTrue(np.all(w[125]==-.25))
        self.assertTrue(np.all(w[260]==0))
    def test_router_trend(self):
        c,h,l,r,e=smooth(drift=(.001,.001,.001,.001))
        self.assertEqual(regime_router(c,r,e)['state'][-1],'TREND')
    def test_router_dispersion(self):
        c,h,l,r,e=smooth(drift=(.002,-.002,0,0))
        self.assertEqual(regime_router(c,r,e)['state'][-1],'DISPERSION')
    def test_router_hazard(self):
        lr=np.zeros(300);lr[270]=-.2
        c=np.repeat((100*np.exp(np.cumsum(lr)))[:,None],4,axis=1)
        z=np.zeros_like(c)
        self.assertEqual(regime_router(c,z,z)['state'][290],'HAZARD')
    def test_router_recovery(self):
        lr=np.zeros(300);lr[270]=.2
        c=np.repeat((100*np.exp(np.cumsum(lr)))[:,None],4,axis=1)
        z=np.zeros_like(c)
        self.assertEqual(regime_router(c,z,z)['state'][290],'RECOVERY')
    def test_future_invariance(self):
        c,h,l,r,e=smooth()
        a=source_bundle(c,h,l,r,e)
        c[310:]*=1.5;h[310:]*=1.5;l[310:]*=1.5
        b=source_bundle(c,h,l,r,e)
        for i in range(4):
            np.testing.assert_array_equal(a[i][:305],b[i][:305])
        np.testing.assert_array_equal(a[4]['state'][:305],b[4]['state'][:305])
    def test_invalid(self):
        c,h,l,r,e=smooth()
        c[0,0]=0.
        with self.assertRaises(ValueError):source_bundle(c,h,l,r,e)
    def test_reproducible(self):
        c,h,l,r,e=smooth()
        a=source_bundle(c,h,l,r,e)
        b=source_bundle(c,h,l,r,e)
        def sha(x):
            return hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
        for i in range(4):self.assertEqual(sha(a[i]),sha(b[i]))

if __name__=='__main__':unittest.main()
