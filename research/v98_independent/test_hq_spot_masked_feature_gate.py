"""Synthetic-only HQ canonical consumer gate tests, no Binance/holdout access."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import hq_spot_masked_feature_gate as gate


class HQFeatureInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "v98_independent"
        cls.root.mkdir()
        buf = io.StringIO(newline="")
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(gate.FIELDS)
        for asset in gate.ASSETS:
            for i in range(gate.HOURS):
                t = gate.START + i * 3600000
                if t == gate.MISSING:
                    writer.writerow((asset, t, "0", "0", "", "", "", "", ""))
                else:
                    writer.writerow((asset, t, "1", "0" if t == gate.PARTIAL else "1",
                                     "100", "110", "90", "105", "1000"))
        cls.raw = buf.getvalue().encode()
        cls.receipt = {
            "decision": "PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC",
            "validation_2025_read": False, "data_2026_read": False,
            "historical_system_pnl_computed": False,
            "complete_grid_source_rejection_still_active": True,
            "publisher_early_close_partial_asset_hours": 4,
            "eligible_full_hour_asset_hours": 73144,
            "canonical_sha256": hashlib.sha256(cls.raw).hexdigest(),
        }
        cls.data = cls.root / "hq_spot_calendar_masked.csv"
        cls.receipt_path = cls.root / "hq_masked_source_receipt.json"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.data.write_bytes(self.raw)
        self.receipt_path.write_text(json.dumps(self.receipt))

    def run_gate(self):
        return gate.load_verified(self.data, self.receipt_path)

    def mutate(self, before, after):
        changed = self.data.read_bytes().replace(before, after, 1)
        self.data.write_bytes(changed)
        receipt = dict(self.receipt)
        receipt["canonical_sha256"] = hashlib.sha256(changed).hexdigest()
        self.receipt_path.write_text(json.dumps(receipt))

    def test_exact_complete_source_and_causal_partial_gap(self):
        x = self.run_gate()
        self.assertEqual((x["observed_asset_hours"], x["eligible_asset_hours"]), (73148, 73144))
        btc = x["assets"]["BTCUSDT"]
        ix = (gate.PARTIAL - gate.START) // 3600000
        self.assertFalse(btc["eligible"][ix])
        self.assertFalse(btc["eligible"][ix+1])
        self.assertIsNone(btc["close"][ix+1])
        self.assertFalse(gate.valid_window(btc["eligible"], ix+2, 2))
        self.assertTrue(gate.valid_window(btc["eligible"], ix+3, 2))
        self.assertFalse(x["holdout_2025_read"])

    def test_canonical_tamper_rejected(self):
        self.data.write_bytes(self.raw + b"tamper")
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            self.run_gate()

    def test_filled_gap_is_rejected_even_with_matching_hash(self):
        needle = f"BTCUSDT,{gate.MISSING},0,0,,,,,\n".encode()
        repl = f"BTCUSDT,{gate.MISSING},1,1,100,110,90,105,1000\n".encode()
        self.assertIn(needle, self.raw)
        self.mutate(needle, repl)
        with self.assertRaisesRegex(ValueError, "MISSING_BAR_FILLED"):
            self.run_gate()

    def test_partial_bar_falsely_full_rejected(self):
        needle = f"BTCUSDT,{gate.PARTIAL},1,0,100,110,90,105,1000\n".encode()
        repl = f"BTCUSDT,{gate.PARTIAL},1,1,100,110,90,105,1000\n".encode()
        self.assertIn(needle, self.raw)
        self.mutate(needle, repl)
        with self.assertRaisesRegex(ValueError, "PARTIAL_MASK_MISMATCH"):
            self.run_gate()

    def test_future_row_rejected_even_with_matching_hash(self):
        self.data.write_bytes(self.raw + f"BTCUSDT,{gate.CUT},1,1,100,110,90,105,1000\n".encode())
        receipt = dict(self.receipt)
        receipt["canonical_sha256"] = hashlib.sha256(self.data.read_bytes()).hexdigest()
        self.receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "EXTRA_ROWS_OR_HOLDOUT"):
            self.run_gate()


if __name__ == "__main__":
    unittest.main()
