#!/usr/bin/env python3
"""V98 Phase1015 deterministic source-only transport synthetic tests."""
from __future__ import annotations
import unittest
import numpy as np
from phase1015_canonical_transport import canonical_scalar, canonical_array
from phase1006_o_sevenslot_source import robust_scale, verify_corners, waterfill


class CanonicalTransportTests(unittest.TestCase):
    def test_no_exposure_increase_and_fixed_decimal_quantum(self):
        for x in (.7,.35,.123456789,.00000123456789,1.499999,1e-12):
            q=canonical_scalar(x)
            self.assertGreaterEqual(q,0)
            self.assertLess(q,x)
        self.assertEqual(canonical_scalar(0.),0.)

    def test_cross_cpu_scale_float_noise_same_canonical(self):
        for x in (.35,.123456789,.70000000001,.000123456789):
            self.assertEqual(canonical_scalar(x),canonical_scalar(x+1e-13))
            self.assertEqual(canonical_scalar(x),canonical_scalar(x-1e-13))

    def test_reject_nonfinite_negative_wrong_shape(self):
        for x in (np.nan,np.inf,-.01):
            with self.assertRaises(ValueError):
                canonical_scalar(x)
        with self.assertRaises(ValueError):
            canonical_array(np.ones((3,5)))
        with self.assertRaises(ValueError):
            canonical_array(np.array([[np.nan,0,0,0]]))

    def test_3000_governed_synthetic_scenarios_remain_safe(self):
        rng=np.random.default_rng(1015)
        n=3000
        score=rng.uniform(.001,1,(n,4))
        gross=rng.uniform(.2,1.5,n)
        raw=np.vstack([waterfill(score[i],float(gross[i])) for i in range(n)])
        down=rng.uniform(0,.8,(n,4))
        up=rng.uniform(0,.8,(n,4))
        scaled=raw*robust_scale(raw,down,up)[:,None]
        canon=canonical_array(scaled)
        self.assertTrue((canon<=scaled+1e-15).all())
        self.assertTrue(verify_corners(canon,down,up,tol=1e-9))
        self.assertLess(float((scaled-canon).max()),1e-7)
        self.assertEqual(int(np.count_nonzero((scaled>0)!=(canon>0))),0)


if __name__=="__main__":
    unittest.main()
