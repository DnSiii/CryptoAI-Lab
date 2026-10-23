import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
import pandas as pd
from phase1157_aa_sevenslot_source import ASSETS,PATHS,CAPITAL,compose_aa,canonical_hash,event_hold

def source(n=900,quote=1e8):
    rng=np.random.default_rng(1157)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(.0001,.004,(n,4))
    c=100*np.exp(np.cumsum(r,axis=0));o=np.vstack((c[0],c[:-1]))
    h=np.maximum(o,c)*(1+rng.uniform(.0001,.003,(n,4)))
    l=np.minimum(o,c)*(1-rng.uniform(.0001,.003,(n,4)))
    q=np.full((n,4),quote);f=np.zeros((n,4))
    f[::8]=rng.normal(0,.0001,(len(f[::8]),4))
    return tuple(pd.DataFrame(a,index=idx,columns=ASSETS) for a in (o,h,l,c,q,f))

class TestAASevenSlot(unittest.TestCase):
    def test_fifteen_capital_native_paths_reproducible(self):
        s=source();a,diag=compose_aa(*s,diagnostics=True)
        self.assertEqual(set(a),{(p,m) for p in PATHS for m in CAPITAL})
        self.assertTrue(diag['source_only'])
        self.assertFalse(diag['historical_pnl_computed'])
        b=compose_aa(*s)
        self.assertEqual({k:canonical_hash(v) for k,v in a.items()},
                         {k:canonical_hash(v) for k,v in b.items()})
    def test_t_minus_one_causality(self):
        s=list(source());a=compose_aa(*s)
        c=s[3].copy();c.iloc[-1]*=1.02
        h=s[1].copy();h.iloc[-1]=np.maximum(h.iloc[-1],c.iloc[-1]*1.001)
        b=compose_aa(s[0],h,s[2],c,s[4],s[5])
        for k in a:
            self.assertTrue(np.array_equal(a[k].iloc[:-1],b[k].iloc[:-1]))
    def test_2025_and_xrp_prohibited(self):
        s=list(source());bad=s.copy()
        bad[0]=bad[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaisesRegex(ValueError,'CLEAN4'):compose_aa(*bad)
        later=[v.set_axis(pd.date_range('2025-01-01',periods=len(v),freq='h',tz='UTC')) for v in s]
        with self.assertRaisesRegex(ValueError,'TRAINING_ONLY'):compose_aa(*later)
    def test_event_hold_lockout(self):
        x=event_hold(np.ones((110,4)),np.ones((110,4),bool))
        self.assertTrue(np.all(x[:12]==1))
        self.assertTrue(np.all(x[12:96]==0))
        self.assertTrue(np.all(x[96:108]==1))
if __name__=='__main__':unittest.main()
