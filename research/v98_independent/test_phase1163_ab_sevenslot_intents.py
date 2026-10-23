import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np,pandas as pd
from phase1163_ab_sevenslot_intents import ASSETS,CAPITAL,PATHS,compose_ab_intents,canonical_hash,event_hold

def source(n=950):
    rng=np.random.default_rng(1163)
    idx=pd.date_range('2022-12-01',periods=n,freq='h',tz='UTC')
    r=rng.normal(.0001,.004,(n,4));c=100*np.exp(np.cumsum(r,axis=0))
    o=np.vstack((c[0],c[:-1]));h=np.maximum(o,c)*1.001;l=np.minimum(o,c)*.999
    q=np.full((n,4),1e8);f=np.zeros((n,4));f[::8]=.0001
    return tuple(pd.DataFrame(x,index=idx,columns=ASSETS) for x in (o,h,l,c,q,f))

class TestAB(unittest.TestCase):
    def test_15_intents_and_hashes(self):
        s=source();a,diag=compose_ab_intents(*s,diagnostics=True)
        self.assertEqual(set(a),{(p,m) for p in PATHS for m in CAPITAL})
        self.assertEqual(len(set(canonical_hash(x) for x in a.values())),15)
        self.assertFalse(diag['historical_pnl_computed'])
        self.assertTrue(diag['stateful_nav_execution_required'])
    def test_causal_t_minus_one(self):
        s=list(source());a=compose_ab_intents(*s)
        c=s[3].copy();c.iloc[-1]*=1.01
        h=s[1].copy();h.iloc[-1]=np.maximum(h.iloc[-1],c.iloc[-1]*1.001)
        b=compose_ab_intents(s[0],h,s[2],c,s[4],s[5])
        for k in a:self.assertTrue(np.array_equal(a[k].iloc[:-1],b[k].iloc[:-1]))
    def test_no_2025_or_xrp(self):
        s=list(source());bad=s.copy();bad[0]=bad[0].rename(columns={'BTCUSDT':'XRPUSDT'})
        with self.assertRaisesRegex(ValueError,'CLEAN4'):compose_ab_intents(*bad)
        later=[x.set_axis(pd.date_range('2025-01-01',periods=len(x),freq='h',tz='UTC')) for x in s]
        with self.assertRaisesRegex(ValueError,'TRAINING_ONLY'):compose_ab_intents(*later)
    def test_event_lockout(self):
        h=event_hold(np.ones((150,4)),np.ones((150,4),bool))
        self.assertTrue(np.all(h[:24]==1))
        self.assertTrue(np.all(h[24:120]==0))
        self.assertTrue(np.all(h[120:144]==1))
if __name__=='__main__':unittest.main()
