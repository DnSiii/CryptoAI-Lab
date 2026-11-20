"""C27 analytic gap-bound tests; no historical prices or holdout."""
import unittest
from .v98_c27_gap_envelope import (
    worst_long_weight, preemptive_asset_cap,
    preemptive_gross_cap, prove_envelope,
)

class GapEnvelopeTests(unittest.TestCase):
    def test_20pct_up_down_asset_boundary(self):
        w=preemptive_asset_cap(.40,.20,.20)
        self.assertAlmostEqual(w,4/13)
        self.assertAlmostEqual(worst_long_weight(w,.20,.20),.40)
        self.assertTrue(prove_envelope(w,preemptive_gross_cap(.90,.20)))

    def test_20pct_all_up_gross_boundary(self):
        self.assertAlmostEqual(preemptive_gross_cap(.90,.20),.90/1.02)

    def test_unbuffered_caps_fail(self):
        with self.assertRaisesRegex(ValueError,"ASSET_ENVELOPE"):
            prove_envelope(.40,.80)
        with self.assertRaisesRegex(ValueError,"GROSS_ENVELOPE"):
            prove_envelope(.30,.90)

    def test_unbounded_gap_has_no_positive_guaranteed_cap(self):
        self.assertLess(preemptive_asset_cap(.40,1000.,.20),.001)

    def test_invalid_gap_rejected(self):
        with self.assertRaises(ValueError):
            preemptive_asset_cap(.40,.20,1.)

if __name__=="__main__":
    unittest.main()
