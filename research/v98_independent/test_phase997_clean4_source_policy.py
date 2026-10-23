"""V98 Phase997 source-only deterministic tests. No network or historical PnL."""
import csv
import hashlib
import io
import unittest
from unittest.mock import patch
import phase997_clean4_source_policy as p
from test_phase996_btc_feb_gap_resolution import fixture


def expected_synthetic_sha(monthly, daily):
    rows = [r for day in range(1,29) for r in daily[day]]
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(rows)
    return hashlib.sha256(stream.getvalue().encode()).hexdigest()


class SourcePolicyTests(unittest.TestCase):
    def test_strict_original_parser_accepts_only_exact_reconstruction(self):
        monthly, daily = fixture()
        with patch.object(p, "DERIVATIVE_SHA", expected_synthetic_sha(monthly,daily)):
            bounds, overlap = p.canonical_derivative(monthly, daily)
        self.assertEqual(len(bounds), 84)
        self.assertEqual(overlap["different_rows"], 0)

    def test_reconstruction_sha_mismatch_fails_closed(self):
        monthly, daily = fixture()
        with self.assertRaisesRegex(PermissionError, "DERIVATIVE_SHA_DRIFT"):
            p.canonical_derivative(monthly, daily)

    def test_alternate_gap_rejected_before_sha(self):
        monthly, daily = fixture()
        monthly.pop(0)
        with self.assertRaises(ValueError):
            p.canonical_derivative(monthly, daily)

    def test_unapproved_overlap_edit_rejected_before_sha(self):
        monthly, daily = fixture()
        daily[2][0][4] = "100.75"
        with self.assertRaises(ValueError):
            p.canonical_derivative(monthly, daily)

    def test_output_is_not_frozen_phase797_file(self):
        self.assertNotEqual(p.BOUNDS.name, "phase797_conservative_training_funding_bounds.csv")
        self.assertNotEqual(p.OUT.name, "phase797_official_mark_archive_receipt.json")


if __name__ == "__main__":
    unittest.main()
