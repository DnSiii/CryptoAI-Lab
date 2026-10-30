"""V98 Independent Q signed corner oracle, synthetic only, no historical PnL."""
import itertools
import unittest
import numpy as np
from phase1040_q_signed_margin_oracle import corner_audit,execute_signed


def brute(cash,u,o,dn,up,baseline,buffer=0):
    if baseline<=0:return False
    all_factors=[np.ones(4)]
    all_factors += [np.array([1+up[j] if bits[j] else 1-dn[j] for j in range(4)])
                    for bits in itertools.product((False,True),repeat=4)]
    for factors in all_factors:
        prices=o*factors
        v=u*prices;eq=cash+v.sum()-buffer
        if eq<.25*baseline-1e-9*baseline or eq<=0 or np.abs(v).sum()>1.4*eq+1e-9*baseline or np.abs(v).max()>.55*eq+1e-9*baseline or abs(v.sum())>.65*eq+1e-9*baseline:
            return False
    return True


class QIndependentOracle(unittest.TestCase):
    def test_5000_signed_random_states_exact_corners(self):
        rng=np.random.default_rng(1045)
        mismatches=0
        for _ in range(5000):
            o=np.exp(rng.uniform(2,10,4));base=10000.
            u=rng.uniform(-.8,.8,4)*base/o
            cash=base-np.dot(u,o)
            dn=rng.uniform(.01,.8,4);up=rng.uniform(.01,1.2,4)
            buffer=rng.uniform(0,250)
            a=corner_audit(cash,u,o,dn,up,baseline=base,buffer=buffer)['ok']
            b=brute(cash,u,o,dn,up,base,buffer)
            mismatches+=int(a!=b)
        self.assertEqual(mismatches,0)
    def test_3600_lp_signed_cash_funding_and_liquidity(self):
        rng=np.random.default_rng(1046)
        successes=0
        for mode in ('immediate','capacity_1m','capacity_10m'):
            for _ in range(1200):
                o=np.exp(rng.uniform(2,10,4));q=np.exp(rng.uniform(4,17,4))
                w=rng.uniform(-.35,.35,4)
                w*=min(1.,.6/max(abs(w.sum()),1e-4),1.3/max(abs(w).sum(),1e-4))
                dn=rng.uniform(.02,.45,4);up=rng.uniform(.02,.55,4)
                fee=float(rng.choice([.0007,.0012,.002]));buffer=float(rng.uniform(0,200))
                r=execute_signed(10000,np.zeros(4),o,q,w,fee,dn,up,funding_buffer=buffer,mode=mode)
                if r['ok']:
                    successes+=1
                    self.assertTrue(brute(r['cash'],r['units'],o,dn,up,10000,buffer))
                    self.assertAlmostEqual(r['cash']+float(np.dot(r['units'],o))+r['fee_usd'],10000,delta=1e-5)
                    if mode!='immediate':
                        self.assertTrue((np.abs(r['trade_usd'])<=.01*q+1e-5).all())
        self.assertGreater(successes,3500)
    def test_repeatability(self):
        o=np.array([30000.,2000.,300.,80.]);u=np.array([.01,-.2,.5,-1.]);q=np.ones(4)*1e7
        cash=10000-np.dot(u,o);w=np.array([.3,-.2,.1,-.1]);dn=np.ones(4)*.15;up=np.ones(4)*.2
        a=execute_signed(cash,u,o,q,w,.0012,dn,up,mode='capacity_1m')
        b=execute_signed(cash,u,o,q,w,.0012,dn,up,mode='capacity_1m')
        self.assertEqual(a['ok'],b['ok'])
        if a['ok']:
            np.testing.assert_array_equal(a['units'],b['units']);self.assertEqual(a['cash'],b['cash'])

if __name__=='__main__':unittest.main()
