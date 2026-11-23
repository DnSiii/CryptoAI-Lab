"""Synthetic-only linkage regression: no exchange data or economic PnL."""
import unittest
from unittest.mock import patch
from research.v98_independent.v98_c27_prospective_link_gate import link_inputs

SOURCE = {"start_utc": "2026-01-01T00:00:00Z",
          "end_utc": "2026-01-02T00:00:00Z",
          "receipt_sha256": "a" * 64}
CARRY = {"snapshot_sha256": "b" * 64}


class LinkTests(unittest.TestCase):
    @patch("research.v98_independent.v98_c27_prospective_link_gate.Path.read_bytes")
    @patch("research.v98_independent.v98_c27_prospective_link_gate.validate_carry")
    @patch("research.v98_independent.v98_c27_prospective_link_gate.validate_sources")
    def test_matching_digest_never_authorizes_pnl(self, sources, carry, read_bytes):
        sources.return_value = SOURCE
        carry.return_value = CARRY
        read_bytes.return_value = b'{"source_receipt_sha256":"' + b"a" * 64 + b'","warmup_receipt_sha256":"' + b"c" * 64 + b'"}'
        result = link_inputs("/tmp/v98_independent", "/tmp/v98_independent/source.json",
                             "/tmp/v98_independent/carry.json", "b" * 64)
        self.assertFalse(result["economic_replay_allowed"])
        self.assertEqual(result["source_receipt_sha256"], "a" * 64)
        read_bytes.return_value = read_bytes.return_value.replace(b"a" * 64, b"d" * 64)
        with self.assertRaisesRegex(ValueError, "CARRY_SOURCE_RECEIPT_MISMATCH"):
            link_inputs("/tmp/v98_independent", "/tmp/v98_independent/source.json",
                        "/tmp/v98_independent/carry.json", "b" * 64)


if __name__ == "__main__":
    unittest.main()
