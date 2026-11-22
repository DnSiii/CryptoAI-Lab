"""Source-only prospective firewall tests; no future market data accessed."""
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_c27_prospective_source_preflight import stamp_ms, validate, TRAIN_END

class ProspectiveFirewallTests(unittest.TestCase):
    def test_utc_required(self):
        with self.assertRaises(ValueError):
            stamp_ms("2026-01-01T00:00:00")
        self.assertEqual(stamp_ms("2026-01-01T00:00:00Z"), TRAIN_END)

    def test_namespace_required_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "V98_NAMESPACE_REQUIRED"):
                validate(d, Path(d) / "receipt.json")

    def test_no_uncommitted_or_nonprospective_window(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root = Path(d) / "v98_independent"
            root.mkdir()
            receipt = root / "receipt.json"
            import json
            base = {"mode":"V98_C27_PROSPECTIVE_SOURCE_ONLY",
                    "candidate_commit":"6c609dacde9f197ba58ed23546bd14fda968a035",
                    "exchange":"Binance","product":"USD-M","interval":"1h",
                    "phase083_used":False,"fitting_allowed":False,
                    "assets":{a:{} for a in ("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")},
                    "start_utc":"2025-12-31T23:00:00Z",
                    "end_utc":"2026-01-01T01:00:00Z",
                    "window_precommitted":True,"precommit_reference":"test-only"}
            receipt.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,"VALIDATION_WINDOW_NOT_PROSPECTIVE"):
                validate(root, receipt)
            base["start_utc"]="2026-01-01T00:00:00Z"
            base["window_precommitted"]=False
            receipt.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,"VALIDATION_WINDOW_NOT_PRECOMMITTED"):
                validate(root, receipt)

if __name__ == "__main__":
    unittest.main()
