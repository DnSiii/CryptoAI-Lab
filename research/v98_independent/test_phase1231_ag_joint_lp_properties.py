#!/usr/bin/env python3
"""V98 AG1231 independent randomized joint LP and corner survivability properties."""
import unittest
import numpy as np
from phase1226_ag_atomic_portfolio import (
    joint_plan,corner_audit,CORNERS,COSTS,ASSET_CAP,GROSS_CAP,EQUITY_FLOOR)


class TestAGLPProperties(unittest.TestCase):
    def test_random_carried_inventory_and_actual_costs(self):
        rng=np.random.default_rng(1231)
        p=np.array([100.,150.,50.,200.])
        q=np.full(4,1e12)
        tested=0
        for k in range(250):
            old_z=rng.uniform(0,12000,4)
            old=old_z/p
            cash=float(rng.uniform(500,15000))
            mu=rng.uniform(-.025,.065,4)
            d=rng.uniform(.12,.70,4)
            u=rng.uniform(.12,.90,4)
            f=rng.uniform(.0001,.006,4)
            reserve=float(rng.choice([.1,.2,.45]))
            fee_mode=list(COSTS)[k%3]
            result=joint_plan(old,p,cash,mu,d,u,f,q,q,
                              fee_mode,cash_floor=reserve)
            fee,slip=COSTS[fee_mode]
            z=result['units']*p
            turn=float(np.abs(z-old_z).sum())
            eq=cash+old_z.sum()
            self.assertAlmostEqual(result['cash']+z.sum()+
                                   (fee+slip)*turn,eq,places=5)
            self.assertGreaterEqual(result['cash'],reserve*eq-2e-5)
            self.assertTrue(np.all(z>=0))
            ratios=np.stack([1-d,np.ones(4),1+u])[CORNERS,np.arange(4)]
            ok,reason=corner_audit(z,old_z,eq,ratios,f,fee+slip,
                                   fee+slip,q,q,cash_floor=reserve,tol=2e-5)
            self.assertTrue(ok,reason)
            self.assertTrue(np.isfinite(result['growth_utility']))
            tested+=1
        self.assertEqual(tested,250)

    def test_joint_infeasibility_fails_closed(self):
        p=np.array([100.,150.,50.,200.])
        old=np.array([100.,0.,0.,0.])
        with self.assertRaisesRegex(ValueError,'NO_JOINT_FEASIBLE'):
            joint_plan(old,p,0.,np.ones(4)*.04,np.ones(4)*.8,
                       np.ones(4)*.9,np.full(4,.01),
                       np.zeros(4),np.full(4,1e12),'supersevere',
                       cash_floor=.45)


if __name__=='__main__':
    unittest.main()
