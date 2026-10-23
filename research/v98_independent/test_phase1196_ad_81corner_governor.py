import unittest
import numpy as np
from phase1196_ad_81corner_governor import CORNERS,feasible,propose


class GovernorTests(unittest.TestCase):
    def setUp(self):
        self.p=np.full(4,100.)
        self.d=np.full(4,.25)
        self.u=np.full(4,.30)
        self.f=np.full(4,.005)
        self.q=np.full(4,1e7)
        self.qmin=np.full(4,1e7)
        self.old=np.zeros(4)
        self.eq=10000.

    def gate(self,n,old=None,q=None,qmin=None):
        return feasible(n,self.old if old is None else old,self.p,self.eq,
                        self.d,self.u,self.f,self.q if q is None else q,
                        self.qmin if qmin is None else qmin)

    def test_eighty_one_corners(self):
        self.assertEqual(CORNERS.shape,(81,4))
        self.assertEqual(len(set(map(tuple,CORNERS))),81)

    def test_flat_is_feasible(self):
        self.assertTrue(self.gate(np.zeros(4)))

    def test_small_exposure_feasible(self):
        self.assertTrue(self.gate(np.full(4,2.)))

    def test_huge_leverage_rejected(self):
        self.assertFalse(self.gate(np.full(4,100.)))

    def test_short_squeeze_rejected(self):
        self.assertFalse(self.gate(np.full(4,-50.)))

    def test_no_free_exit(self):
        carried=np.full(4,10.)
        candidate,alpha=propose(np.zeros(4),carried,self.p,self.eq,self.d,self.u,self.f,
                    np.zeros(4),np.zeros(4))
        np.testing.assert_array_equal(candidate,carried)
        self.assertEqual(alpha,0)

    def test_unexecutable_overexposure_fails(self):
        carried=np.full(4,50.)
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE'):
            propose(np.zeros(4),carried,self.p,self.eq,self.d,self.u,self.f,
                    np.zeros(4),np.zeros(4))

    def test_interpolation_no_teleport(self):
        candidate,alpha=propose(np.full(4,.2),self.old,self.p,self.eq,
            self.d,self.u,self.f,np.full(4,10000.),np.full(4,1e7))
        self.assertTrue(0<=alpha<1)
        self.assertTrue(self.gate(candidate,q=np.full(4,10000.)))

    def test_bad_input_fails_closed(self):
        self.assertFalse(self.gate(np.array([np.nan,0,0,0])))

    def test_adverse_funding_rejected(self):
        self.assertFalse(feasible(np.full(4,10.),self.old,self.p,self.eq,
            self.d,self.u,np.full(4,2.),self.q,self.qmin))


if __name__=='__main__':unittest.main()
