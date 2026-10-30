#!/usr/bin/env python3
"""S signed 16-corner risk and causal capacity execution tests, synthetic only."""
import unittest
import numpy as np
from phase1073_s_signed_execution import execute,audit,corners,GROSS_CAP,ASSET_CAP,NET_CAP
class SExecution(unittest.TestCase):
    def test_corners(self):
        a=corners(np.ones(4)*.1,np.ones(4)*.2)
        self.assertEqual(a.shape,(16,4));self.assertEqual(len({tuple(x) for x in a}),16)
    def test_zero(self):
        r=execute(10000.,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e8,np.zeros(4),.0007,np.ones(4)*.1,np.ones(4)*.1)
        self.assertTrue(r['ok']);self.assertAlmostEqual(r['cash'],10000.);self.assertAlmostEqual(r['fee_usd'],0.)
    def test_signed_target_and_stress(self):
        r=execute(10000.,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e8,np.array([.3,-.25,.2,-.15]),.0007,np.ones(4)*.1,np.ones(4)*.1)
        self.assertTrue(r['ok'],r);self.assertGreater(r['units'][0],0);self.assertLess(r['units'][1],0)
        self.assertTrue(audit(r['cash'],r['units'],np.ones(4)*100.,np.ones(4)*.1,np.ones(4)*.1,baseline=10000.)['ok'])
    def test_funding_buffer_reduces_exposure(self):
        args=(10000.,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e8,np.array([.3,-.25,.2,-.15]),.0007,np.ones(4)*.1,np.ones(4)*.1)
        r=execute(*args,buffer=2000.);self.assertTrue(r['ok'],r)
        self.assertTrue(audit(r['cash'],r['units'],args[2],args[6],args[7],baseline=10000.,buffer=2000.)['ok'])
    def test_capacity(self):
        r=execute(1e6,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e6,np.array([.3,-.25,.2,-.15]),.0012,np.ones(4)*.1,np.ones(4)*.1,mode='capacity_1m')
        self.assertTrue(r['ok'],r);self.assertLessEqual(np.abs(r['trade_usd']).max(),10000.+.1)
    def test_reject_unbounded(self):
        with self.assertRaises(ValueError):execute(10000.,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e8,np.ones(4),.0007,np.ones(4)*.1,np.ones(4)*.1)
    def test_reject_future_invalid(self):
        with self.assertRaises(ValueError):corners(np.array([.1,.1,.1,1.]),np.zeros(4))
    def test_adversarial_1000(self):
        rng=np.random.default_rng(20261023)
        for _ in range(1000):
            w=rng.normal(0,.2,4);w*=min(1.,1.3/np.abs(w).sum(),.44/np.abs(w).max(),.74/max(abs(w.sum()),1e-12))
            down=rng.uniform(0,.2,4);up=rng.uniform(0,.2,4)
            r=execute(10000.,np.zeros(4),np.ones(4)*100.,np.ones(4)*1e8,w,.0012,down,up)
            if r['ok']:
                self.assertTrue(audit(r['cash'],r['units'],np.ones(4)*100.,down,up,baseline=10000.)['ok'])
if __name__=='__main__':unittest.main()
