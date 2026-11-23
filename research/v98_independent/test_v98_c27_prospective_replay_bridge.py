"""Synthetic-only tests for V98 C27 prospective input bridge."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_c27_prospective_replay_bridge import prepare

class BridgeTests(unittest.TestCase):
    def test_verified_inputs_and_fail_closed_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "v98_independent"
            root.mkdir()
            assets = {}
            for asset in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"):
                p = root / (asset + "_price.csv")
                f = root / (asset + "_funding.csv")
                with p.open("w", newline="") as out:
                    w = csv.writer(out)
                    w.writerow(["open_time", "open", "high", "low", "close", "quote_volume"])
                    for hour in range(3):
                        w.writerow([f"2026-01-01T0{hour}:00:00Z", 100, 110, 90, 101, 500])
                with f.open("w", newline="") as out:
                    w = csv.writer(out)
                    w.writerow(["timestamp_utc", "funding_rate"])
                    w.writerow(["2026-01-01T01:00:00Z", "0.0001"])
                assets[asset] = dict(price_file=p.name, price_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                     funding_file=f.name, funding_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps(dict(mode="V98_C27_PROSPECTIVE_SOURCE_ONLY",
                candidate_commit="6c609dacde9f197ba58ed23546bd14fda968a035",
                exchange="Binance", product="USD-M", interval="1h",
                phase083_used=False, fitting_allowed=False, assets=assets,
                start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T03:00:00Z",
                window_precommitted=True, precommit_reference="synthetic-fixture-only")))
            result = prepare(root, receipt)
            self.assertFalse(result["economic_replay_allowed"])
            self.assertEqual(result["bars"]["BTCUSDT"][0], (100.,110.,90.,101.,500.))
            self.assertEqual(result["funding_by_hour"]["SOLUSDT"], {1:0.0001})
            with (root / "BTCUSDT_price.csv").open("a") as out:
                out.write("malicious,0,0,0,0,0\n")
            with self.assertRaisesRegex(ValueError, "PROVENANCE_HASH_OR_PATH"):
                prepare(root, receipt)

if __name__ == "__main__":
    unittest.main()
