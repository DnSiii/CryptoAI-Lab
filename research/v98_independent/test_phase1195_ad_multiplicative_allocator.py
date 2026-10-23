import unittest
import numpy as np
from phase1195_ad_multiplicative_allocator import ADAllocator,sleeve_matrix


class AllocatorTests(unittest.TestCase):
    def setUp(self):
        self.a=ADAllocator()
        self.matrix=sleeve_matrix([.25]*4,[1,0,0,-1],[.5,-.5,0,0],[-.0375]*4)
        self.router=np.array([.2,.3,.5])

    def test_conversion_and_mix(self):
        target,posterior=self.a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,self.router)
        self.assertEqual(target.shape,(4,))
        self.assertTrue(np.isfinite(target).all())
        self.assertAlmostEqual(float(posterior.sum()),1,places=12)

    def test_no_free_funding(self):
        self.a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,self.router)
        self.a.step(np.zeros(4),np.array([.05,0,0,0]),np.array([1,0,0,0]),self.matrix,self.router)
        self.assertLess(self.a.wealth[0],1)
        self.assertGreater(self.a.wealth[1],.99)

    def test_turnover_charged_next_completed_bar(self):
        self.a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,self.router)
        self.a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,self.router)
        self.assertLess(self.a.wealth[0],1)
        self.assertLess(self.a.wealth[2],1)

    def test_router_changes_allocation_not_past_wealth(self):
        a=ADAllocator();b=ADAllocator()
        x,_=a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,[.8,.1,.1])
        y,_=b.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,[.1,.1,.8])
        self.assertFalse(np.array_equal(x,y))
        np.testing.assert_array_equal(a.wealth,b.wealth)

    def test_invalid_event_mask_rejected(self):
        with self.assertRaisesRegex(ValueError,'STATE_INPUT'):
            self.a.step(np.zeros(4),np.ones(4),np.zeros(4),self.matrix,self.router)

    def test_invalid_rv_rejected(self):
        with self.assertRaisesRegex(ValueError,'RV_NEUTRALITY'):
            sleeve_matrix([.25]*4,[0]*4,[1,0,0,0],[0]*4)

    def test_invalid_stress_rejected(self):
        with self.assertRaisesRegex(ValueError,'STRESS_INTENT'):
            sleeve_matrix([.25]*4,[0]*4,[0]*4,[.1]*4)

    def test_insolvency_rejected(self):
        self.a.step(np.zeros(4),np.zeros(4),np.zeros(4),self.matrix,self.router)
        with self.assertRaisesRegex(ValueError,'VIRTUAL_INSOLVENCY'):
            self.a.step(np.array([-10.,0,0,0]),np.zeros(4),np.zeros(4),self.matrix,self.router)

    def test_no_pnl_claim(self):
        self.assertFalse(self.a.diagnostic()['historical_system_pnl_computed'])
        self.assertFalse(self.a.diagnostic()['actual_execution_proven'])


if __name__=='__main__':unittest.main()
