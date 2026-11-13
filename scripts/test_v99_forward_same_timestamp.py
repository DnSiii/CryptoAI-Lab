"""Adversarial tests for exchange fills sharing a timestamp (no economic promotion)."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("gate", Path(__file__).with_name("validate_v99_forward_epoch_manifest.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def manifest():
    return {
        "mode": "RESEARCH_ONLY", "real_orders_enabled": False,
        "economics_status": "UNVERIFIED", "variants": sorted(gate.VARIANTS),
        "epoch_id": "timestamp-test", "output_namespace": "research-forward-epochs/timestamp-test",
        "predecessor": {"ledger_sha256": "a"*64, "commit_sha": "abc", "immutable_source": "archive"},
        "start_after_utc": "2026-11-10T00:00:00Z",
        "last_historical_reference_by_variant": {v: "2026-11-09T00:00:00Z" for v in gate.VARIANTS},
        "receipts": [],
    }

def receipt(t, h):
    return {
        "source": "exchange", "captured_at_utc": "2026-11-10T00:00:03Z",
        "event_at_utc": t, "instrument": "BTC-USDT", "units": "BTC",
        "quantity": "0.001", "price": "100", "fee_currency": "USDT",
        "fee_amount": "0.01", "settled_funding": "0", "raw_sha256": h*64,
    }

class SameTimestampTests(unittest.TestCase):
    def test_distinct_same_time_accepted(self):
        m = manifest()
        m["receipts"] = [receipt("2026-11-10T00:00:01Z", "b"), receipt("2026-11-10T00:00:01Z", "c")]
        self.assertEqual(gate.validate(m)["receipts_declared"], 2)
        self.assertFalse(gate.validate(m)["economic_validation"])

    def test_duplicate_hash_rejected(self):
        m = manifest()
        m["receipts"] = [receipt("2026-11-10T00:00:01Z", "b"), receipt("2026-11-10T00:00:01Z", "b")]
        with self.assertRaisesRegex(ValueError, "duplicate raw receipt"):
            gate.validate(m)

    def test_backwards_time_rejected(self):
        m = manifest()
        m["receipts"] = [receipt("2026-11-10T00:00:02Z", "b"), receipt("2026-11-10T00:00:01Z", "c")]
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            gate.validate(m)

    def test_boundary_time_rejected(self):
        m = manifest()
        m["receipts"] = [receipt("2026-11-10T00:00:00Z", "b")]
        with self.assertRaisesRegex(ValueError, "pre-boundary"):
            gate.validate(m)

if __name__ == "__main__":
    unittest.main()
