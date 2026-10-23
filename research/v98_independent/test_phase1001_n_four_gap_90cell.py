"""V98 Phase1001 pre-economic no-network source and frozen-pin tests."""
import unittest
from unittest.mock import patch
import phase1001_n_four_gap_90cell as p


class FourGapEconomicGateTests(unittest.TestCase):
    def test_ten_frozen_economic_hashes(self):
        p.verify_frozen_files()

    def test_source_failure_blocks_before_economics(self):
        with patch.object(p, "verify_frozen_files"), patch.object(p, "fresh_ohlc", return_value={"decision":"BLOCKED"}), patch.object(p, "fresh_policy") as marks:
            with self.assertRaisesRegex(PermissionError, "FRESH_100_OHLC"):
                p.fresh_source_gate()
            marks.assert_not_called()

    def test_four_gap_source_rejection_blocks(self):
        valid = {"decision":p.PASS_OHLC, "vendor_origin_attested":True,
                 "assets":{a:{"sha256":p.PINS[a],"monthly_archives":25,"hours":18288} for a in p.ASSETS}}
        with patch.object(p, "verify_frozen_files"), patch.object(p, "fresh_ohlc", return_value=valid), patch.object(p, "fresh_policy", return_value=2):
            with self.assertRaisesRegex(PermissionError, "FRESH_FOUR_GAP"):
                p.fresh_source_gate()

    def test_unmodified_five_path_target_set(self):
        self.assertEqual(tuple(p.FROZEN_N),p.N_PATHS)
        self.assertEqual(len(p.FROZEN_N),5)


if __name__=="__main__":
    unittest.main()
