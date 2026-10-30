import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
import pandas as pd
from phase1143_z_sevenslot_source import (
    ASSETS,PATHS,CAPITAL,corner_gate,optimize_joint,compose_z,
    event_hold,beta_neutral,canonical_hash,sleeves_and_regimes,prior_adverse_bounds)

def source(n=840):
    rng=np.random.default_rng(1143)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    ret=rng.normal(.0003,.005,(n,4))
    c=100*np.exp(np.cumsum(ret,axis=0))
    o=np.vstack([c[0],c[:-1]])
    h=np.maximum(c,o)*(1+rng.uniform(.0001,.006,(n,4)))
    l=np.minimum(c,o)*(1-rng.uniform(.0001,.006,(n,4)))
    q=np.full((n,4),50_000_000.,dtype=float)
    funding=np.zeros((n,4))
    funding[::8]=rng.normal(0,.0001,(len(funding[::8]),4))
    return tuple(pd.DataFrame(a,index=idx,columns=ASSETS) for a in (o,h,l,c,q,funding))

class TestZSource(unittest.TestCase):
    def test_81_corners_count_and_risk(self):
        self.assertTrue(corner_gate(np.array([.1,-.1,0,0]),np.full(4,.1),np.full(4,.1),np.full(4,.001)))
        self.assertFalse(corner_gate(np.array([.6,0,0,0]),np.full(4,.1),np.full(4,.1),np.zeros(4)))
        self.assertFalse(corner_gate(np.array([.44,0,0,0]),np.full(4,.5),np.full(4,.1),np.zeros(4)))
    def test_capital_participation(self):
        args=(np.array([.03,-.02,.01,0]),np.eye(4)*.001,np.zeros(4),
              np.full(4,.1),np.full(4,.1),np.full(4,.001),np.full(4,1e6))
        a=optimize_joint(*args,10000.)
        b=optimize_joint(*args,10000000.)
        self.assertLessEqual(np.max(np.abs(a)),.45)
        self.assertTrue(np.all(np.abs(b)<=.8*.01*1e6/(1e7*1.002)+1e-6))
        self.assertTrue(corner_gate(a,args[3],args[4],args[5]))
        self.assertFalse(np.array_equal(a,b))
    def test_event_hold_and_lockout(self):
        d=np.ones((100,4));e=np.ones((100,4),bool)
        h=event_hold(d,e)
        self.assertTrue(np.all(h[:16]==1))
        self.assertTrue(np.all(h[16:72]==0))
        self.assertTrue(np.all(h[72:88]==1))
    def test_beta_hedge(self):
        self.assertIsNone(beta_neutral(-1,1))
        a,b=beta_neutral(1,2)
        self.assertAlmostEqual(a*1+b*2,0)
    def test_full_composition_and_hash(self):
        result,diag=compose_z(*source(),diagnostics=True)
        self.assertEqual(len(result),15)
        self.assertTrue(all(len(x)==840 for x in result.values()))
        self.assertFalse(diag['historical_pnl_computed'])
        self.assertTrue(all(len(canonical_hash(x))==64 for x in result.values()))
        self.assertEqual(set(result),{(p,m) for p in PATHS for m in CAPITAL})
    def test_all_fifteen_capital_native_targets_pass_prior_corners(self):
        src=source();r=compose_z(*src)
        dn,up,fb=prior_adverse_bounds(src[3],src[1],src[2],src[5])
        for (path,mode),frame in r.items():
            weights=frame.to_numpy(float)
            for t in range(720,840,12):
                old=weights[t-1]
                new=weights[t]
                self.assertTrue(corner_gate(new,dn[t],up[t],fb[t],old),(path,mode,t))
                self.assertLessEqual(abs(new).max(),.45+1e-8)
                self.assertLessEqual(abs(new).sum(),1.35+1e-8)
                self.assertLessEqual(abs(new.sum()),.75+1e-8)
                cap=.8*.01*src[4].iloc[t].to_numpy()/(CAPITAL[mode]*1.002)
                self.assertTrue(np.all(abs(new-old)<=cap+1e-6))
    def test_phase1149_infeasible_inventory_reduce_only_or_hard_block(self):
        old=np.array([.44,-.44,.3,0.]);dn=np.full(4,.3);up=np.full(4,.4)
        fund=np.full(4,.002);alpha=np.array([.02,-.02,.01,0.])
        self.assertFalse(corner_gate(old,dn,up,fund,old))
        w=optimize_joint(alpha,np.eye(4)*.001,old,dn,up,fund,
                         np.full(4,1e9),10000.)
        self.assertTrue(corner_gate(w,dn,up,fund,old))
        self.assertLess(np.abs(w).sum(),np.abs(old).sum())
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_PRIOR_INVENTORY'):
            optimize_joint(alpha,np.eye(4)*.001,old,dn,up,fund,
                           np.zeros(4),10000.)

    def test_zero_quote_cannot_open_position(self):
        w=optimize_joint(np.ones(4)*.1,np.eye(4)*.01,np.zeros(4),
            np.full(4,.1),np.full(4,.1),np.zeros(4),np.zeros(4),10000)
        self.assertTrue(np.array_equal(w,np.zeros(4)))
    def test_no_future_and_t_minus_one(self):
        s=list(source())
        r1=compose_z(*s)
        changed=s[3].copy();changed.iloc[-1]*=1.01
        high=s[1].copy();high.iloc[-1]=np.maximum(high.iloc[-1],changed.iloc[-1]*1.001)
        low=s[2].copy();low.iloc[-1]=np.minimum(low.iloc[-1],changed.iloc[-1]*.999)
        r2=compose_z(s[0],high,low,changed,s[4],s[5])
        for key in r1:
            self.assertTrue(np.array_equal(r1[key].iloc[:-1].to_numpy(),r2[key].iloc[:-1].to_numpy()))
    def test_reject_future_and_xrp(self):
        s=list(source())
        idx=pd.date_range('2025-01-01',periods=840,freq='h',tz='UTC')
        later=[pd.DataFrame(x.to_numpy(),index=idx,columns=ASSETS) for x in s]
        with self.assertRaisesRegex(ValueError,'TRAINING_ONLY'):
            compose_z(*later)
        bad=s.copy();bad[0]=bad[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaisesRegex(ValueError,'CLEAN4'):
            compose_z(*bad)
    def test_carry_and_regime_determinism(self):
        s=source()
        a,r,_=sleeves_and_regimes(*s)
        b,r2,_=sleeves_and_regimes(*s)
        self.assertTrue(np.array_equal(r,r2))
        for k in a:self.assertTrue(np.array_equal(a[k],b[k]))

if __name__=='__main__':unittest.main()
