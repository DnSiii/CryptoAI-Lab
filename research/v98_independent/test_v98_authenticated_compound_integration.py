import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.v98_independent import v98_authenticated_compound_integration as integration
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS


class IntegrationTest(unittest.TestCase):
    def test_previous_hour_execution_and_cost_independence(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as root:
            root = Path(root)
            slots = root / "slots.csv"
            with slots.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                for i in range(3):
                    for asset in ASSETS:
                        writer.writerow({"asset": asset,
                                         "hour_open_ms": integration.START_MS+i*HOUR_MS,
                                         "growth_core": .5 if asset == ASSETS[0] else 0.,
                                         "opportunity": 0, "relative_value": 0,
                                         "stress_recovery": 0, "regime_router": 1,
                                         "dynamic_allocator": 1, "risk_governor": 1})
            bars = {a: [(100., 110., 90., 110., 1.)]*3 for a in ASSETS}
            source = {"bars": bars, "funding": {a: {} for a in ASSETS},
                      "price_manifest_sha256": "price", "funding_manifest_sha256": "funding"}
            with patch.object(integration, "EXPECTED_HOURS", 3), patch.object(
                integration, "load", return_value=source
            ):
                result = integration.run(slots, root, root/"manifest.json",
                                         root, root/"out", capital=1000,
                                         fee_bps=10, slippage_bps=0)
            self.assertEqual(result["status"], "ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE")
            self.assertEqual(set(result["scenarios"]), {"1.0", "2.0", "4.0"})
            import json
            ledger = json.loads((root/"out"/"compound_ledger_1.0.json").read_text())
            self.assertEqual(ledger[0]["turnover_usd"], 0.)
            self.assertGreater(ledger[1]["turnover_usd"], 0.)
            self.assertNotEqual(result["scenarios"]["1.0"]["final_equity_usd"],
                                result["scenarios"]["4.0"]["final_equity_usd"])

    def test_reject_incomplete_slots_before_pnl(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as root:
            root = Path(root)
            slots = root/"slots.csv"
            with slots.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
            source = {"bars": {}, "funding": {}, "price_manifest_sha256": "p",
                      "funding_manifest_sha256": "f"}
            with patch.object(integration, "EXPECTED_HOURS", 3), patch.object(
                integration, "load", return_value=source
            ):
                with self.assertRaisesRegex(ValueError, "INCOMPLETE_FULL_HISTORY_SLOTS"):
                    integration.run(slots, root, root/"manifest.json", root, root/"out",
                                    capital=1000, fee_bps=1, slippage_bps=1)


if __name__ == "__main__":
    unittest.main()
