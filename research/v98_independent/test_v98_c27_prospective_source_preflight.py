"""Source-only prospective firewall tests; no future market data accessed."""
import tempfile
import csv
import hashlib
import json
import unittest
from pathlib import Path
from research.v98_independent.v98_c27_prospective_source_preflight import stamp_ms, validate, TRAIN_END

class ProspectiveFirewallTests(unittest.TestCase):
    def test_funding_order_and_source_integrity(self):
        # Synthetic fixtures only; never touches future market observations.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "v98_independent"
            root.mkdir()
            assets = {}
            for asset in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"):
                price = root / (asset + "_price.csv")
                funding = root / (asset + "_funding.csv")
                with price.open("w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["open_time","open","high","low","close","quote_volume"])
                    for hour in (0,1,2):
                        w.writerow([f"2026-01-01T0{hour}:00:00Z",100,110,90,101,500])
                with funding.open("w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["timestamp_utc","funding_rate"])
                    w.writerow(["2026-01-01T01:00:00Z",0.0001])
                    w.writerow(["2026-01-01T00:00:00Z",0.0002])
                assets[asset] = {
                    "price_file":price.name,
                    "price_sha256":hashlib.sha256(price.read_bytes()).hexdigest(),
                    "funding_file":funding.name,
                    "funding_sha256":hashlib.sha256(funding.read_bytes()).hexdigest()}
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps({
                "mode":"V98_C27_PROSPECTIVE_SOURCE_ONLY",
                "candidate_commit":"6c609dacde9f197ba58ed23546bd14fda968a035",
                "exchange":"Binance","product":"USD-M","interval":"1h",
                "phase083_used":False,"fitting_allowed":False,
                "assets":assets,
                "start_utc":"2026-01-01T00:00:00Z",
                "end_utc":"2026-01-01T03:00:00Z",
                "window_precommitted":True,"precommit_reference":"synthetic-fixture-only"}))
            with self.assertRaisesRegex(ValueError, "PROSPECTIVE_BAD_FUNDING"):
                validate(root, receipt)
            for asset in assets:
                funding = root / assets[asset]["funding_file"]
                lines = funding.read_text().splitlines()
                funding.write_text(chr(10).join([lines[0],lines[2],lines[1]]) + chr(10))
                assets[asset]["funding_sha256"] = hashlib.sha256(funding.read_bytes()).hexdigest()
            receipt_data = json.loads(receipt.read_text())
            receipt_data["assets"] = assets
            receipt.write_text(json.dumps(receipt_data))
            self.assertEqual(validate(root, receipt)["hours"], 3)

    def test_receipt_must_be_inside_data_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "v98_independent"
            root.mkdir()
            external = Path(d) / "another_v98_independent"
            external.mkdir()
            receipt = external / "receipt.json"
            receipt.write_text("{}")
            with self.assertRaisesRegex(ValueError, "V98_NAMESPACE_REQUIRED"):
                validate(root, receipt)

    def test_malformed_price_schema_rejected_before_pnl(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "v98_independent"
            root.mkdir()
            assets = {}
            for asset in ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"):
                price = root / (asset + "_price.csv")
                funding = root / (asset + "_funding.csv")
                price.write_text("open_time,open,high,low,close,quote_volume,untrusted_extra\\n"
                                 "2026-01-01T00:00:00Z,100,110,90,101,500,1\\n"
                                 "2026-01-01T01:00:00Z,100,110,90,101,500,1\\n")
                funding.write_text("timestamp_utc,funding_rate\\n2026-01-01T00:00:00Z,0.0001\\n")
                assets[asset] = {
                    "price_file": price.name,
                    "price_sha256": hashlib.sha256(price.read_bytes()).hexdigest(),
                    "funding_file": funding.name,
                    "funding_sha256": hashlib.sha256(funding.read_bytes()).hexdigest()}
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps({
                "mode": "V98_C27_PROSPECTIVE_SOURCE_ONLY",
                "candidate_commit": "6c609dacde9f197ba58ed23546bd14fda968a035",
                "exchange": "Binance", "product": "USD-M", "interval": "1h",
                "phase083_used": False, "fitting_allowed": False,
                "assets": assets,
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T02:00:00Z",
                "window_precommitted": True, "precommit_reference": "synthetic-only"}))
            with self.assertRaisesRegex(ValueError, "PROSPECTIVE_PRICE_SCHEMA"):
                validate(root, receipt)

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
