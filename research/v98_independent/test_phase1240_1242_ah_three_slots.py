#!/usr/bin/env python3
"""V98 AH1240-1242 preregistered causal three-slot and collateral tests."""
import unittest,hashlib
import numpy as np
from phase1240_ah_regime_router import ah_regime_router
from phase1241_ah_online_growth_allocator import AHOnlineGrowthAllocator
from phase1242_ah_signed_governor import ah_governor_target
from phase1234_ah_signed_variation_margin import scenario_audit,settle_hour

def data(n=140,drift=(.001,.001,.001,.001)):
    t=np.arange(n)[:,None]
    c=100*np.exp(t*np.asarray(drift)[None,:])
    return c,np.zeros_like(c),np.zeros_like(c)

class TestRouter(unittest.TestCase):
    def test_trend(self):
        self.assertEqual(ah_regime_router(*data())['state'][-1],'TREND')
    def test_dispersion(self):
        self.assertEqual(ah_regime_router(*data(drift=(.002,-.002,0,0)))['state'][-1],'DISPERSION')
    def test_hazard(self):
        r=np.zeros(140)
        r[116]=-.20
        c=100*np.exp(np.cumsum(r))
        C=np.repeat(c[:,None],4,axis=1)
        self.assertEqual(ah_regime_router(C,np.zeros_like(C),np.zeros_like(C))['state'][120],'HAZARD')
    def test_future_perturbation(self):
        c,r,e=data()
        a=ah_regime_router(c,r,e)
        c[125:]*=10.
        b=ah_regime_router(c,r,e)
        self.assertEqual(a['state'][120],b['state'][120])
        self.assertEqual(a['market_skew'][120],b['market_skew'][120])
    def test_bad_geometry(self):
        with self.assertRaises(ValueError):
            ah_regime_router(np.ones((140,5)),np.ones((140,5)),np.zeros((140,5)))
    def test_native_funding_breadth(self):
        c,r,e=data()
        e[::8]=1.
        r[::8]=.0001
        a=ah_regime_router(c,r,e)
        self.assertAlmostEqual(a['funding_breadth'][-1],1.)

class TestAllocator(unittest.TestCase):
    def test_cold_start_and_simplex(self):
        a=AHOnlineGrowthAllocator()
        s=np.zeros((4,4));s[0,0]=1.;s[1,1]=-1.
        a.observe(np.zeros(4),np.zeros(4),np.zeros(4))
        v=a.decide(s,'TREND')
        self.assertEqual(v['growth_scale'],0.)
        self.assertAlmostEqual(v['sleeve_weights'].sum(),1.)
        self.assertTrue(np.all(v['sleeve_weights']>=0))
    def test_prior_signal_only(self):
        a=AHOnlineGrowthAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        a.decide(s,'TREND')
        paper=a.observe(np.array([.02,0,0,0]),np.zeros(4),np.zeros(4))
        self.assertAlmostEqual(paper[0],.02-.001)
        self.assertAlmostEqual(paper[1],0.)
    def test_funding_signs(self):
        a=AHOnlineGrowthAllocator()
        s=np.zeros((4,4));s[0,0]=1.;s[1,0]=-1.
        a.decide(s,'TREND')
        x=a.observe(np.zeros(4),np.array([.01,0,0,0]),np.array([1.,0,0,0]))
        self.assertAlmostEqual(x[0],-.011)
        self.assertAlmostEqual(x[1],.009)
    def test_online_growth_nonzero(self):
        a=AHOnlineGrowthAllocator()
        s=np.zeros((4,4));s[0,0]=1.
        for i in range(170):
            a.observe(np.array([.005,0,0,0]),np.zeros(4),np.zeros(4))
            v=a.decide(s,'TREND')
        self.assertGreater(v['growth_scale'],0)
        self.assertTrue(np.isfinite(v['signed_target']).all())
        self.assertAlmostEqual(v['sleeve_weights'].sum(),1.)
    def test_invalid(self):
        a=AHOnlineGrowthAllocator()
        with self.assertRaises(ValueError):
            a.decide(np.ones((4,4)),'TREND')
        with self.assertRaises(ValueError):
            a.decide(np.zeros((4,4)),'UNKNOWN')
    def test_reproducible(self):
        def trial():
            a=AHOnlineGrowthAllocator()
            s=np.zeros((4,4));s[0,0]=1.;s[1,1]=-1.
            out=[]
            for t in range(200):
                a.observe(np.array([.002*np.sin(t),.001,0.,0.]),np.zeros(4),np.zeros(4))
                v=a.decide(s,'DISPERSION')
                out.extend(v['sleeve_weights'])
                out.append(v['growth_scale'])
            return hashlib.sha256(np.asarray(out,dtype='<f8').tobytes()).hexdigest()
        self.assertEqual(trial(),trial())

class TestGovernor(unittest.TestCase):
    def args(self):
        z=np.zeros(4)
        return dict(cash_previous=10000.,old_units=z,prior_close=np.full(4,100.),
            opening=np.full(4,100.),signed_target=np.array([3.,-3.,0.,0.]),
            prior_down=np.full(4,.45),prior_up=np.full(4,.8),
            funding_bound=np.full(4,.0005),prior_quote=np.full(4,1e9),
            min_quote=np.full(4,1e9))
    def test_signed_feasible_bisection(self):
        kw=self.args();r=ah_governor_target(**kw)
        self.assertLess(r['fraction'],1.)
        self.assertGreater(r['fraction'],0.)
        self.assertLess(r['units'][1],0.)
        ok,_=scenario_audit(10000.,r['units'],np.full(4,100.),
            np.full(4,55.),np.full(4,180.),.001,np.full(4,.0005),10000.)
        self.assertTrue(ok)
    def test_no_lookahead_interface(self):
        self.assertNotIn('current_high',ah_governor_target.__code__.co_varnames)
        self.assertNotIn('current_low',ah_governor_target.__code__.co_varnames)
    def test_liquidity_cap(self):
        kw=self.args()
        kw['prior_quote']=np.full(4,1000.)
        kw['min_quote']=np.full(4,1000.)
        r=ah_governor_target(**kw)
        self.assertTrue(np.all(np.abs(r['units'])*100 <=3./(2.2*1.8)+1e-6))
    def test_carried_fail_closed(self):
        kw=self.args()
        kw['cash_previous']=1000.
        kw['old_units']=np.array([100.,0,0,0])
        with self.assertRaisesRegex(ValueError,'CARRIED_'):
            ah_governor_target(**kw)
    def test_modes(self):
        kw=self.args()
        for fee in ('base','severe','supersevere'):
            for order in ('carried_before_fill','new_after_fill'):
                r=ah_governor_target(**kw,fee_mode=fee,order=order)
                self.assertTrue(np.isfinite(r['units']).all())
    def test_actual_ledger_signed(self):
        kw=self.args();r=ah_governor_target(**kw)
        p=np.full(4,100.);z=np.zeros(4)
        out=settle_hour(10000.,z,p,p,p*1.01,p*.99,p,
            r['units'],np.full(4,1e9),np.full(4,1e9),
            np.full(4,.45),np.full(4,.8),np.full(4,.0005),
            np.zeros(4),z,p*.99,p*1.01)
        self.assertLess(out['cash'],10000.)
        self.assertTrue(out['cash_settled'])
        self.assertFalse(out['hidden_borrow'])
    def test_deterministic(self):
        kw=self.args()
        x=ah_governor_target(**kw)
        y=ah_governor_target(**kw)
        np.testing.assert_array_equal(x['units'],y['units'])
    def test_bad_inputs(self):
        kw=self.args();kw['prior_down']=np.full(4,1.1)
        with self.assertRaises(ValueError):
            ah_governor_target(**kw)

if __name__=='__main__':
    unittest.main()
