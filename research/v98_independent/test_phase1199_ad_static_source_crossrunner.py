import unittest
import numpy as np
from phase1198_ad_complete_synthetic import fixture,source_slots
from phase1199_ad_static_source_crossrunner import static_hash,PATHS,MODES


class StaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames,*_=fixture()
        cls.core,cls.router,cls.opp,cls.rv=source_slots(cls.frames)
        cls.idx=cls.frames[0].index

    def test_fifteen_distinct_static_hashes(self):
        hashes=[static_hash(self.idx,self.core,self.router,self.opp,self.rv,p,m)
                for p in PATHS for m in MODES]
        self.assertEqual(len(hashes),15)
        self.assertEqual(len(set(hashes)),15)

    def test_ablation_does_not_mutate_source(self):
        original=self.rv.copy()
        static_hash(self.idx,self.core,self.router,self.opp,self.rv,'AD_core_only',MODES[0])
        np.testing.assert_array_equal(original,self.rv)

    def test_reproducible(self):
        a=static_hash(self.idx,self.core,self.router,self.opp,self.rv,'AD_full',MODES[0])
        b=static_hash(self.idx,self.core.copy(),self.router.copy(),self.opp.copy(),
                      self.rv.copy(),'AD_full',MODES[0])
        self.assertEqual(a,b)

    def test_invalid_mode_rejected(self):
        with self.assertRaisesRegex(ValueError,'PATH_MODE'):
            static_hash(self.idx,self.core,self.router,self.opp,self.rv,'AD_full','future')


if __name__=='__main__':unittest.main()
