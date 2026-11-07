import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from research.v98_independent.v98_phase243_training_reader import load, START_MS, END_MS, EXPECTED_HOURS
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Phase243ReaderTest(unittest.TestCase):
    def test_complete_authenticated_clean4_and_native_funding(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root = Path(d) / "v98_independent"
            prices, funding = root / "prices", root / "funding"
            prices.mkdir(parents=True)
            funding.mkdir()
            price_manifest = {"mode": "CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA",
                              "holdout_accessed": False, "prices": {}}
            funding_manifest = {"mode": "V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY",
                                "holdout_accessed": False, "assets": {}}
            for asset in ASSETS:
                path = prices / (asset + "_1h.csv")
                with path.open("w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(("open_time", "open", "high", "low", "close", "quote_volume"))
                    for i in range(EXPECTED_HOURS):
                        t = START_MS + i * HOUR_MS
                        stamp = datetime.fromtimestamp(t / 1000, timezone.utc).isoformat()
                        writer.writerow((stamp, 100, 101, 99, 100, 1000))
                price_manifest["prices"][asset] = {"canonical_sha256": sha(path)}
                fp = funding / (asset + "_native_funding.csv")
                fp.write_text("funding_time_ms,funding_rate\n" + str(START_MS) + ",0.0001\n")
                funding_manifest["assets"][asset] = {"sha256": sha(fp)}
            mp = root / "phase243_manifest.json"
            mp.write_text(json.dumps(price_manifest))
            (funding / "funding_manifest.json").write_text(json.dumps(funding_manifest))
            result = load(prices, mp, funding)
            self.assertEqual(result["hours"], EXPECTED_HOURS)
            self.assertEqual(set(result["bars"]), set(ASSETS))
            self.assertFalse(result["holdout_accessed"])
            with (prices / "BTCUSDT_1h.csv").open("a") as f:
                f.write("2026-01-01T00:00:00+00:00,100,101,99,100,1000\n")
            with self.assertRaisesRegex(ValueError, "PHASE243_PRICE_HASH_MISMATCH"):
                load(prices, mp, funding)

    def test_missing_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as d:
            root = Path(d) / "v98_independent"
            root.mkdir()
            mp = root / "manifest.json"
            mp.write_text(json.dumps({"mode": "CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA",
                                      "holdout_accessed": False, "prices": {}}))
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_PHASE243_MANIFEST"):
                load(root, mp, root)

if __name__ == "__main__":
    unittest.main()
