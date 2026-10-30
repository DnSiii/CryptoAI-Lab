import unittest
import numpy as np
from test_phase1214_af_dual_ewma_core import sample
from phase1216_af_long_only_rv import (
    af_relative_value_source,allocate_residual,LIQUIDITY)


class AFLongOnlyRVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=sample()
        cls.out=af_relative_value_source(*cls.f)

    def test_strict_336h_quote_warmup(self):
        self.assertTrue(np.all(self.out[:LIQUIDITY]==0))

    def test_funded_two_leader_rotation_activates(self):
        w=self.out[500]
        self.assertGreater(w[0],0)
        self.assertGreater(w[1],0)
        self.assertEqual(w[2],0)
        self.assertEqual(w[3],0)
        self.assertAlmostEqual(w.sum(),.15,places=10)

    def test_no_short_and_no_unfunded_gross(self):
        self.assertTrue(np.all(self.out>=0))
        self.assertLessEqual(self.out.max(),.10+1e-10)
        self.assertLessEqual(self.out.sum(axis=1).max(),.15+1e-10)

    def test_capped_residual_redistribution(self):
        w=allocate_residual(np.array([10.,1.,0.,0.]))
        np.testing.assert_allclose(w,[.10,.05,0,0],atol=1e-10)

    def test_future_close_change_cannot_change_previous_rv(self):
        f=[x.copy() for x in self.f]
        f[3].iloc[500,0]*=1.05
        f[1].iloc[500,0]=max(f[1].iloc[500,0],f[3].iloc[500,0])
        new=af_relative_value_source(*f)
        np.testing.assert_array_equal(self.out[:500],new[:500])
        self.assertFalse(np.array_equal(self.out[500:],new[500:]))

    def test_current_quote_change_only_affects_future(self):
        f=[x.copy() for x in self.f]
        f[4].iloc[500,0]=0
        new=af_relative_value_source(*f)
        np.testing.assert_array_equal(self.out[:501],new[:501])
        self.assertNotEqual(self.out[501].sum(),new[501].sum())

    def test_deterministic_reproduction(self):
        np.testing.assert_array_equal(self.out,af_relative_value_source(*self.f))


if __name__=='__main__':unittest.main()
