"""V98 Phase998 fail-closed economic gate tests; no data/network/PnL."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import phase998_n_provenance_90cell as p


class Phase998GateTests(unittest.TestCase):
    def test_ten_frozen_source_hashes_unchanged(self):
        self.assertEqual(len(p.FROZEN_FILES), 10)
        p.verify_frozen_files()

    def test_source_sha_drift_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sample.py").write_bytes(b"wrong")
            with patch.object(p, "FROZEN_FILES", {"sample.py": "0" * 64}):
                with self.assertRaisesRegex(PermissionError, "FROZEN_N_SOURCE_SHA_DRIFT"):
                    p.verify_frozen_files(root)

    def test_ohlc_failure_blocks_before_mark_fetch(self):
        with patch.object(p, "verify_frozen_files"), patch.object(p, "fresh_ohlc", return_value={"decision": "BLOCKED"}), patch.object(p, "fresh_policy") as mark:
            with self.assertRaisesRegex(PermissionError, "FRESH_100_OHLC"):
                p.fresh_source_gate()
            mark.assert_not_called()

    def test_unverified_mark_policy_rejected(self):
        receipt = {"decision": p.PASS_OHLC, "vendor_origin_attested": True,
                   "assets": {asset: {"sha256": p.PINS[asset], "monthly_archives": 25,
                                      "hours": 18288} for asset in p.ASSETS}}
        with patch.object(p, "verify_frozen_files"), patch.object(p, "fresh_ohlc", return_value=receipt), patch.object(p, "fresh_policy", return_value=2):
            with self.assertRaisesRegex(PermissionError, "FRESH_100_MARK"):
                p.fresh_source_gate()

    def test_no_economic_candidate_autopromotion(self):
        self.assertTrue(p.OUT.name.startswith("phase998_"))
        self.assertNotIn("phase797", p.OUT.name)


if __name__ == "__main__":
    unittest.main()
