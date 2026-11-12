"""Adversarial fail-closed tests for V99 forward receipt provenance preflight.

Synthetic receipts are ONLY security fixtures, never economic evidence.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.tools.v99_r106_forward_receipt_preflight import check


class ForwardReceiptPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        payload = b'{"source":"fixture-only","close":"2026-11-12T06:00:00Z"}'
        (self.root / "receipt.json").write_bytes(payload)
        self.manifest = {
            "mode": "RESEARCH_ONLY_NO_REAL_ORDERS",
            "epoch_id": "forward-20261112-07",
            "legacy_epoch_id": "legacy-2026",
            "epoch_start_utc": "2026-11-12T07:00:00Z",
            "receipts": [{
                "venue": "OKX", "symbol": "BTC-USDT-SWAP", "kind": "funding",
                "close_utc": "2026-11-12T06:00:00Z",
                "acquired_utc": "2026-11-12T06:05:00Z",
                "source_url_or_archive_id": "fixture:not-a-real-source",
                "raw_file": "receipt.json",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "settlement_event_id": "fixture-settlement"
            }]
        }

    def run_gate(self):
        return check(self.manifest, self.root)

    def assert_blocked(self, marker):
        result = self.run_gate()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any(marker in e for e in result["errors"]), result)
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["real_orders_authorized"])

    def test_valid_fixture_not_authorization(self):
        result = self.run_gate()
        self.assertEqual(result["status"], "RECEIPTS_PRECHECK_PASS_NOT_PUBLICATION_AUTHORIZATION")
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["real_orders_authorized"])

    def test_missing_receipt(self):
        self.manifest["receipts"] = []
        self.assert_blocked("NO_SOURCE_RECEIPTS")

    def test_hash_tamper(self):
        (self.root / "receipt.json").write_bytes(b"tampered")
        self.assert_blocked("RAW_HASH_MISMATCH")

    def test_duplicate(self):
        self.manifest["receipts"].append(dict(self.manifest["receipts"][0]))
        self.assert_blocked("DUPLICATE_RECEIPT")

    def test_future_acquisition(self):
        self.manifest["receipts"][0]["acquired_utc"] = "2026-11-12T07:01:00Z"
        self.assert_blocked("NOT_AVAILABLE_AS_OF_START")

    def test_lookahead_acquisition(self):
        self.manifest["receipts"][0]["acquired_utc"] = "2026-11-12T05:59:00Z"
        self.assert_blocked("LOOKAHEAD_ACQUISITION")

    def test_missing_settlement(self):
        del self.manifest["receipts"][0]["settlement_event_id"]
        self.assert_blocked("MISSING_FUNDING_SETTLEMENT_ID")

    def test_live_orders_mode(self):
        self.manifest["mode"] = "LIVE"
        self.assert_blocked("REAL_ORDER_MODE_NOT_FORBIDDEN")

    def test_traversal(self):
        self.manifest["receipts"][0]["raw_file"] = "../receipt.json"
        self.assert_blocked("INVALID_OR_MISSING_RAW_RECEIPT")

    def test_missing_native_fee_tier(self):
        self.manifest["receipts"][0]["kind"] = "execution"
        self.assert_blocked("MISSING_NATIVE_FEE_TIER")

    def test_reused_epoch(self):
        self.manifest["epoch_id"] = self.manifest["legacy_epoch_id"]
        self.assert_blocked("MISSING_OR_REUSED_EPOCH_ID")


if __name__ == "__main__":
    unittest.main()
