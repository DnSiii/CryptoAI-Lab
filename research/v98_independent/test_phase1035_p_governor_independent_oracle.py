#!/usr/bin/env python3
"""P independent 16-corner oracle, synthetic adversarial risk states only."""
import itertools,sys,types,unittest
import numpy as np
try:import phase1002_lp_opening_repair
except ImportError:
    s=types.ModuleType('phase1002_lp_opening_repair');s.PARTICIPATION=.05
    s.repair_open_lp=lambda c,u,o,q,f:(c,u.copy(),np.zeros(4),True)
    sys.modules[s.__name__]=s
from phase1025_p_state_aware_governor import survives,stress_repair,execute_open


def independent_oracle(cash,units,opening,down,up,buffer,baseline):
    for mask in itertools.product((0,1),repeat=4):
        prices=opening*np.array([1+up[j] if mask[j] else 1-down[j] for j in range(4)])
        notionals=units*prices
        equity=cash+notionals.sum()-buffer
        if equity < .10*baseline-1e-8*baseline:return False
        if notionals.sum()>1.75*equity+1e-8*baseline:return False
        if (notionals>.70*equity+1e-8*baseline).any():return False
    return True

class PIndependentOracle(unittest.TestCase):
    def test_5000_states_independent_sixteen_corner_equivalence(self):
        rng=np.random.default_rng(1035)
        for _ in range(5000):
            eq=rng.uniform(100,1e7)
            gross=rng.uniform(0,1.75)
            w=np.minimum(rng.dirichlet(np.ones(4))*gross,.7)
            op=np.exp(rng.uniform(1,9,4))
            units=w*eq/op
            cash=eq-float((units*op).sum())
            down=rng.uniform(.001,.9,4)
            up=rng.uniform(.001,2.,4)
            buffer=eq*rng.uniform(0,.03)
            expected=independent_oracle(cash,units,op,down,up,buffer,eq)
            self.assertEqual(survives(cash,units,op,down,up,buffer,baseline=eq,tol=1e-8),expected)

    def test_2000_exact_lp_repairs_independent_oracle(self):
        rng=np.random.default_rng(1036)
        passed=0
        for _ in range(2000):
            eq=rng.uniform(1e3,1e7)
            gross=rng.uniform(.1,1.75)
            w=np.minimum(rng.dirichlet(np.ones(4))*gross,.7)
            op=np.exp(rng.uniform(1,8,4))
            u=w*eq/op
            cash=eq-float((u*op).sum())
            down=rng.uniform(.01,.8,4)
            up=rng.uniform(.01,3,4)
            buffer=eq*rng.uniform(0,.02)
            fee=float(rng.choice([.0007,.0012,.002]))
            c2,u2,sold,ok=stress_repair(cash,u,op,np.full(4,1e12),fee,down,up,buffer)
            if ok:
                passed+=1
                self.assertTrue(independent_oracle(c2,u2,op,down,up,buffer,eq))
                self.assertTrue((sold>=0).all())
                self.assertLessEqual(sold.sum(),float((u*op).sum())+1e-7*eq)
        self.assertGreater(passed,100)

    def test_1000_open_executions_independent_oracle(self):
        rng=np.random.default_rng(1037)
        accepted=0
        for _ in range(1000):
            eq=1e6
            op=np.array([100.,200.,300.,400.])
            gross=rng.uniform(0,1.65)
            w=np.minimum(rng.dirichlet(np.ones(4))*gross,.7)
            u=w*eq/op
            cash=eq-float((u*op).sum())
            target=np.minimum(rng.dirichlet(np.ones(4))*rng.uniform(.3,1.65),.7)
            down=rng.uniform(.01,.65,4)
            up=rng.uniform(.01,1.5,4)
            buffer=rng.uniform(0,1000)
            fee=float(rng.choice([.0007,.0012,.002]))
            mode=str(rng.choice(['immediate','capacity_1m','capacity_10m']))
            result=execute_open(cash,u,op,np.full(4,1e12),target,fee,down,up,funding_buffer=buffer,mode=mode)
            if result['ok']:
                accepted+=1
                self.assertTrue(independent_oracle(result['cash'],result['units'],op,down,up,buffer,eq))
                self.assertTrue((result['buys_usd'][(result['opening_repair_usd']+result['stress_repair_usd'])>1e-8]==0).all())
        self.assertGreater(accepted,50)

if __name__=='__main__':unittest.main()
