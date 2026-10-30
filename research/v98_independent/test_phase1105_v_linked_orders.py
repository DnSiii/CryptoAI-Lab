"""V independent linked-order synthetic adversarial tests."""
import unittest
import numpy as np
from phase1105_v_linked_orders import preplace,opening_orders,protective_fill

class VLinkedTests(unittest.TestCase):
    def setUp(self):
        self.p=np.full(4,100.);self.d=np.full(4,.05);self.h=np.full(4,.05)
        self.q=np.full(4,1e7)
    def test_reversal_flat_first(self):
        carried=np.array([5.,0,0,0]);desired=np.array([-5.,0,0,0])
        b=preplace(self.p,carried,desired,self.d,self.h,self.q)
        x=opening_orders(b,carried,desired,self.p,.0007,.0007)
        self.assertTrue(x['ok']);self.assertEqual(x['units'][0],0.)
        self.assertEqual(x['events'][0]['action'],'FLAT_REVERSAL')
    def test_reversal_capacity_fails_closed(self):
        c=np.array([100.,0,0,0]);w=-c
        b=preplace(self.p,c,w,self.d,self.h,np.full(4,100.))
        self.assertEqual(opening_orders(b,c,w,self.p,.0007,.0007)['reason'],
                         'V_MANDATORY_OPEN_CAPACITY')
    def test_both_touched_stop_first(self):
        c=np.array([5.,0,0,0]);b=preplace(self.p,c,c,self.d,self.h,self.q)
        x=protective_fill(b,c,self.p,self.p*1.1,self.p*.9,.0007,.0007)
        self.assertTrue(x['ok']);self.assertEqual(x['events'][0]['action'],'STOP')
        self.assertTrue(x['events'][0]['both_touched'])
        self.assertEqual(x['units'][0],0.)
    def test_gap_fill_worse_than_stop(self):
        c=np.array([5.,0,0,0]);b=preplace(self.p,c,c,self.d,self.h,self.q)
        o=np.array([90.,100,100,100]);hi=o*1.001;lo=o*.999
        x=protective_fill(b,c,o,hi,lo,.0007,.0007)
        self.assertTrue(x['ok']);self.assertLess(x['events'][0]['price'],90.)
    def test_no_undercoverage(self):
        c=np.array([5.,0,0,0]);b=preplace(self.p,c,c,self.d,self.h,self.q)
        x=protective_fill(b,np.array([10.,0,0,0]),self.p,self.p*1.01,self.p*.99,.0007,.0007)
        self.assertFalse(x['ok'])
    def test_short_stop_worse_gap(self):
        c=np.array([-5.,0,0,0]);b=preplace(self.p,c,c,self.d,self.h,self.q)
        o=np.array([110.,100,100,100]);hi=o*1.001;lo=o*.999
        x=protective_fill(b,c,o,hi,lo,.0007,.0007)
        self.assertTrue(x['ok']);self.assertGreater(x['events'][0]['price'],110.)
    def test_2000_random_reduce_only(self):
        rng=np.random.default_rng(1105)
        for _ in range(2000):
            u=rng.uniform(-10,10,4)
            b=preplace(self.p,u,u,self.d,self.h,self.q)
            hi=self.p*rng.uniform(1,1.1,4)
            lo=self.p*rng.uniform(.9,1,4)
            x=protective_fill(b,u,self.p,hi,lo,.0007,.0007)
            self.assertTrue(x['ok'])
            self.assertTrue((np.abs(x['units'])<=np.abs(u)+1e-9).all())
            self.assertTrue(((x['units']==0)|(np.sign(x['units'])==np.sign(u))).all())

if __name__=='__main__':unittest.main()
