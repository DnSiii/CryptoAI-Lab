"""Adversarial, read-only tests for V13 raw-notional forensic classifier."""
import unittest
from scripts.audit_v13_paper_raw_provenance import classify

def record(shown, raw, previous=0.2, new=0.3):
    return {"order_value_brl": shown, "order_value_brl_unrounded": raw,
            "previous_weight": previous, "new_weight": new}

class RawProvenanceTests(unittest.TestCase):
    def test_valid_subcent(self):
        self.assertEqual(classify(record(0, 0.004)), "verified_subcent")
    def test_zero_without_evidence(self):
        r = record(0, None)
        self.assertEqual(classify(r), "missing_raw_provenance")
    def test_zero_or_negative_raw(self):
        for raw in (0, -0.001):
            with self.subTest(raw=raw):
                self.assertEqual(classify(record(0, raw)), "invalid_raw")
    def test_nonfinite(self):
        for raw in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(raw=raw):
                self.assertEqual(classify(record(0, raw)), "invalid_raw")
    def test_half_cent_boundary(self):
        self.assertNotEqual(classify(record(0, 0.005)), "verified_subcent")
    def test_mismatch(self):
        self.assertEqual(classify(record(1.0, 2.0)), "raw_display_mismatch")
    def test_missing_raw_positive_is_not_certified(self):
        self.assertEqual(classify(record(1.0, None)), "positive_display_without_raw")
    def test_zero_weight_delta(self):
        self.assertEqual(classify(record(0, 0.001, 0.2, 0.2)), "invalid_display_or_weight")
    def test_invalid_display(self):
        self.assertEqual(classify(record(float("nan"), 0.001)), "invalid_display_or_weight")
    def test_negative_display_rejected(self):
        self.assertEqual(classify(record(-0.01, 0.01)), "invalid_display_or_weight")
    def test_valid_positive(self):
        self.assertEqual(classify(record(1.23, 1.234)), "verified_positive")

if __name__ == "__main__":
    unittest.main()
