"""Synthetic-only carry-in gate regressions."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_c27_carry_state_gate import validate_carry, ASSETS, BASELINE

class CarryGateTests(unittest.TestCase):
    def test_valid_structure_and_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v98_independent"
            root.mkdir()
            path = root / "carry.json"
            state = {
                "candidate_commit": BASELINE, "clock_utc": "2026-01-01T00:00:00Z",
                "decision_clock_utc": "2026-01-01T00:00:00Z",
                "equity_usd": 10000, "peak_equity_usd": 12000,
                "positions": {a: {"quantity": 0, "entry_price": 1, "margin_usd": 0} for a in ASSETS},
                "pending_orders": [], "warmup_receipt_sha256": "a"*64,
                "source_receipt_sha256": "b"*64
            }
            def check():
                path.write_text(json.dumps(state))
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                return validate_carry(root, path, state["clock_utc"], digest)
            self.assertFalse(check()["economic_replay_allowed"])
            state["positions"]["BTCUSDT"]["quantity"] = float("nan")
            with self.assertRaisesRegex(ValueError, "CARRY_POSITION"):
                check()
            state["positions"]["BTCUSDT"]["quantity"] = 0
            state["pending_orders"] = [{"side": "BUY"}]
            with self.assertRaisesRegex(ValueError, "CARRY_PENDING_ORDERS_UNSUPPORTED"):
                check()
            state["pending_orders"] = []
            state["peak_equity_usd"] = 9000
            with self.assertRaisesRegex(ValueError, "CARRY_EQUITY"):
                check()
            state["peak_equity_usd"] = 12000
            path.write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, "CARRY_DIGEST"):
                validate_carry(root, path, state["clock_utc"], "0"*64)

if __name__ == "__main__":
    unittest.main()
