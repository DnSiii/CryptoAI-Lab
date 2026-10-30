#!/usr/bin/env python3
"""P prereg source-only and state-aware risk tests; synthetic inputs only."""
import sys
import types
import unittest
import numpy as np
import pandas as pd

# No source archive, PnL, external engines or 2025 reads needed for tests.
try:
    from phase866_k_sevenslot_source import ASSETS, START, END
except ImportError:
    stub=types.ModuleType('phase866_k_sevenslot_source')
    stub.ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
    stub.START=pd.Timestamp('2022-12-01T00:00:00Z')
    stub.END=pd.Timestamp('2024-12-31T23:00:00Z')
    stub.PINS={a:'0'*64 for a in stub.ASSETS}
    stub.pinned_training_frames=lambda _: (_ for _ in ()).throw(RuntimeError('no real data in synthetic tests'))
    sys.modules[stub.__name__]=stub
    ASSETS,START,END=stub.ASSETS,stub.START,stub.END
try:
    from phase1002_lp_opening_repair import repair_open_lp
except ImportError:
    stub=types.ModuleType('phase1002_lp_opening_repair')
    stub.PARTICIPATION=.05
    def opening_repair(cash,units,opening,prev_quote,fee):
        v=units*opening
        eq=cash+v.sum()
        if v.sum()>1.75*eq or (v>.70*eq).any():
            raise RuntimeError('opening repair requires full production module')
        return cash,units.copy(),np.zeros(4),True
    stub.repair_open_lp=opening_repair
    sys.modules[stub.__name__]=stub

from phase1024_p_sevenslot_source import compose_p, PATHS, _waterfill, p_shocks
from phase1025_p_state_aware_governor import corners, survives, stress_repair, execute_open


def fixture():
    index=pd.date_range(START,END,freq='h')
    t=np.arange(len(index),dtype=float)
    logc=np.stack([np.log(100)+(.000017+.000004*j)*t+.05*np.sin(t/(80+20*j)+j)
                   -.12*np.exp(-((t-3000)/90)**2) for j in range(4)],axis=1)
    close=pd.DataFrame(np.exp(logc),index=index,columns=ASSETS)
    opening=close*(1+.0003*np.sin(t[:,None]/12+np.arange(4)))
    high=np.maximum(opening,close)*1.006
    low=np.minimum(opening,close)*.994
    quote=pd.DataFrame(np.tile(np.array([1e8,5e7,2e7,3e7]),(len(index),1)),index=index,columns=ASSETS)
    quote.iloc[::101,:]*=3
    return opening,high,low,close,quote

class PSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.frames=fixture()

    def test_all_five_paths_and_budgets(self):
        paths,info=compose_p(*self.frames,diagnostics=True)
        self.assertEqual(tuple(paths),PATHS)
        self.assertEqual(sum(info['regime_hours'].values()),18288)
        self.assertEqual(len(info['sleeve_active_hours']),4)
        for name,p in paths.items():
            a=p.to_numpy()
            self.assertTrue(np.isfinite(a).all())
            self.assertGreaterEqual(a.min(),0)
            self.assertLessEqual(a.max(),.70+1e-9)
            self.assertLessEqual(a.sum(axis=1).max(),1.75+1e-9)
            self.assertEqual(info['paths'][name]['updates'],int(info['paths'][name]['updates']))
        self.assertTrue(np.any(paths['P_full'].to_numpy()!=paths['P_core_only'].to_numpy()))

    def test_no_2025_or_invalid_geometry(self):
        op,hi,lo,cl,q=self.frames
        shifted=cl.copy();shifted.index+=pd.Timedelta(hours=1)
        with self.assertRaises(ValueError):compose_p(op,hi,lo,shifted,q)
        bad=hi.copy();bad.iloc[-1,0]=0
        with self.assertRaises(ValueError):compose_p(op,bad,lo,cl,q)

    def test_tminus1_no_future_dependency(self):
        op,hi,lo,cl,q=self.frames
        base=compose_p(op,hi,lo,cl,q)['P_full'].to_numpy()
        future=cl.copy();future.iloc[-1,0]*=1.5
        hi2=hi.copy();hi2.iloc[-1,0]=max(hi2.iloc[-1,0],future.iloc[-1,0])
        changed=compose_p(op,hi2,lo,future,q)['P_full'].to_numpy()
        np.testing.assert_array_equal(base[:-1],changed[:-1])

    def test_shock_warmup_and_waterfill(self):
        op,hi,lo,_,_=self.frames
        dn,up=p_shocks(op,hi,lo)
        self.assertTrue(np.isnan(dn[:1439]).all())
        self.assertTrue(np.isfinite(up[1439:]).all())
        np.testing.assert_allclose(_waterfill([1,0,0,0],1.65),[.70,0,0,0])

class PStateTests(unittest.TestCase):
    def test_exact_sixteen_corners(self):
        self.assertEqual(corners([.1]*4,[.3]*4).shape,(16,4))
        self.assertFalse(survives(-.8,np.array([.45]*4),np.ones(4),[.5]*4,[.5]*4))
        self.assertTrue(survives(.6,np.array([.1]*4),np.ones(4),[.1]*4,[.2]*4))

    def test_stress_repair_deterministic_and_survives(self):
        cash=.1;units=np.array([.4,.4,.3,.2]);op=np.ones(4)
        q=np.full(4,1000.)
        dn=np.array([.55,.5,.4,.3]);up=np.array([10.0,.6,.7,.5])
        a=stress_repair(cash,units,op,q,.001,dn,up,.01)
        b=stress_repair(cash,units,op,q,.001,dn,up,.01)
        self.assertTrue(a[3])
        self.assertTrue(survives(a[0],a[1],op,dn,up,.01,baseline=cash+units.sum()))
        np.testing.assert_array_equal(a[2],b[2])
        self.assertGreater(a[2].sum(),0)

    def test_stress_repair_no_liquidity_fails_closed(self):
        result=stress_repair(.1,np.array([.4,.4,.3,.2]),np.ones(4),np.zeros(4),.001,
                             [.55,.5,.4,.3],[10.0,.6,.7,.5],.01)
        self.assertFalse(result[3])

    def test_execution_causal_and_no_same_hour_rebuy(self):
        result=execute_open(.6,np.array([.1,.1,.1,.1]),np.ones(4),np.full(4,1000.),
                            np.array([.7,.7,.2,.15]),.001,[.15]*4,[.5]*4,
                            funding_buffer=.01,mode='capacity_1m')
        self.assertTrue(result['ok'],result)
        self.assertTrue(survives(result['cash'],result['units'],np.ones(4),[.15]*4,[.5]*4,
                                 .01,baseline=1.))
        self.assertLessEqual(result['buys_usd'].sum(),result['pre_open_equity']*1.75+1e-9)

    def test_seeded_random_stress_repair_survival(self):
        rng=np.random.default_rng(1025)
        successes=0
        for _ in range(500):
            eq=10000.
            w=rng.dirichlet(np.ones(4))*rng.uniform(.3,1.75)
            w=np.minimum(w,.7)
            v=w*eq
            cash=eq-v.sum()
            dn=rng.uniform(.01,.65,4)
            up=rng.uniform(.01,1.3,4)
            c,u,s,ok=stress_repair(cash,v,np.ones(4),np.full(4,1e8),.002,dn,up,25.)
            if ok:
                successes+=1
                self.assertTrue(survives(c,u,np.ones(4),dn,up,25.,baseline=eq,tol=1e-8))
                self.assertTrue((s>=0).all())
        self.assertGreater(successes,100)

if __name__=='__main__':unittest.main()
