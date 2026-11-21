"""Adversarial tests for read-only V13 ledger triage."""
import unittest
from scripts.triage_v13_ledger_discrepancies import triage


class TriageTests(unittest.TestCase):
    def test_separate_categories_and_preserve_examples(self):
        rows = [
            {"symbol": "BTCUSDT", "order_value_brl": 0, "order_value_brl_unrounded": "0.0022489"},
            {"symbol": "ETHUSDT", "order_value_brl": "7.81", "order_value_brl_unrounded": "7.7148819"},
            {"symbol": "ETHUSDT", "order_value_brl": "5.00"},
            {"symbol": "BTCUSDT", "order_value_brl": "-1", "order_value_brl_unrounded": "1"},
            {"symbol": "BTCUSDT", "order_value_brl": "1", "order_value_brl_unrounded": "0"},
            {"symbol": "BTCUSDT", "order_value_brl": "1.23", "order_value_brl_unrounded": "1.2301"},
        ]
        result = triage({"decisions": [{"timestamp": "historical", "adjustments": rows}]})
        self.assertEqual(sum(result["counts"].values()), 6)
        self.assertEqual(result["counts"]["mismatch"], 1)
        self.assertEqual(result["counts"]["missing_raw"], 1)
        self.assertEqual(result["counts"]["subcent_simulated_notional"], 1)
        self.assertEqual(result["counts"]["matched"], 1)
        self.assertEqual(result["max_abs_mismatch_brl_by_symbol"]["ETHUSDT"], "0.0951181")
        self.assertEqual(result["examples_by_category"]["mismatch"][0]["adjustment_index"], 1)

    def test_full_mismatch_manifest_preserves_all_row_identifiers(self):
        rows = [{"symbol": "ETH", "order_value_brl": "10.00", "order_value_brl_unrounded": "9.00"} for _ in range(15)]
        result = triage({"decisions": [{"timestamp": "t", "adjustments": rows}]})
        self.assertEqual(result["counts"]["mismatch"], 15)
        self.assertEqual(len(result["examples_by_category"]["mismatch"]), 10)
        self.assertEqual(len(result["mismatch_manifest"]), 15)
        self.assertEqual([r["adjustment_index"] for r in result["mismatch_manifest"]], list(range(15)))
        self.assertTrue(all(len(r["row_sha256"]) == 64 for r in result["mismatch_manifest"]))

    def test_missing_raw_manifest_keeps_all_rows_and_indices(self):
        rows = [{"symbol": "BTC", "order_value_brl": "1.00"} for _ in range(17)]
        result = triage({"decisions": [{"timestamp": "t", "adjustments": rows}]})
        self.assertEqual(result["counts"]["missing_raw"], 17)
        self.assertEqual(len(result["missing_raw_manifest"]), 17)
        self.assertEqual([r["adjustment_index"] for r in result["missing_raw_manifest"]], list(range(17)))
        self.assertTrue(all(len(r["row_sha256"]) == 64 for r in result["missing_raw_manifest"]))
        self.assertEqual(len(result["examples_by_category"]["missing_raw"]), 10)

    def test_examples_not_monopolized_by_missing_raw(self):
        rows = [{"symbol": "BTC", "order_value_brl": "1"} for _ in range(50)]
        rows.append({"symbol": "ETH", "order_value_brl": "2", "order_value_brl_unrounded": "1"})
        result = triage({"decisions": [{"adjustments": rows}]})
        self.assertEqual(len(result["examples_by_category"]["missing_raw"]), 10)
        self.assertEqual(len(result["examples_by_category"]["mismatch"]), 1)


if __name__ == "__main__":
    unittest.main()
