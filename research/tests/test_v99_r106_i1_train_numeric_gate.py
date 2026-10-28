"""Fixture-only complete-TRAIN numeric risk gate controls, not option profits."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_i1_train_numeric_gate import (
    DAYS, FIRST, REGIMES, SCENARIOS, _expected_clock, _fold, evaluate,
)


def fixture():
    start = Decimal("10000")
    result = {
        "schema": "V99_I1_FIXED_90W_DAILY_TRAIN_EQUITY_INPUT_V1",
        "fixture": True, "initial_capital_usd": str(start), "scenarios": {},
    }
    for scenario in SCENARIOS:
        equity, benchmark = start, start
        rows = []
        for i in range(DAYS):
            # Synthetic deliberately mixed gains/losses, NOT options prices.
            factor = (Decimal("0.999") if i % 7 == 0
                      else Decimal("1.003") if scenario == "severe"
                      else Decimal("1.002"))
            equity *= factor
            benchmark *= Decimal("1.0001")
            ts = _expected_clock(i)
            rows.append({
                "ts_ms": ts, "fold": _fold(ts),
                "regime": REGIMES[i % len(REGIMES)],
                "equity_usd": str(equity),
                "benchmark_usd": str(benchmark),
                "actual_exposure_key": ("A" if scenario == "severe"
                                        else "B" if i % 19 == 0 else "A"),
            })
        result["scenarios"][scenario] = rows
    return result


class NumericTrainGateTests(unittest.TestCase):
    def test_full_661_day_dual_scenario_synthetic_screen_and_independent_roi(self):
        source = fixture()
        result = evaluate(source)
        self.assertEqual(result["days_per_scenario"], 661)
        self.assertTrue(result["numeric_train_pass_both_scenarios"])
        self.assertEqual(result["scenario_path_divergence_days"], len(range(0, DAYS, 19)))
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["freeze_authorized"])
        self.assertFalse(result["original_options_economic_train_certified"])
        self.assertFalse(result["holdout_opened"])
        self.assertFalse(result["validation_opened"])
        for name in SCENARIOS:
            actual = result["scenarios"][name]
            self.assertEqual(actual["positive_folds"], 5)
            self.assertEqual(sum(actual["regime_days"].values()), DAYS)
            self.assertTrue(all(actual["gates"].values()))
            # Independently recompute total from the final native-USD-equivalent
            # fixture ledger snapshot; do not trust the gate's internal factors.
            independent = Decimal(source["scenarios"][name][-1]["equity_usd"]) / Decimal("10000") - 1
            self.assertEqual(Decimal(actual["total_roi"]), independent)
            self.assertLess(Decimal(actual["max_drawdown"]), 0)
            self.assertGreater(Decimal(actual["remove_best_day_roi"]), 0)

    def test_loss_must_reject_not_promote(self):
        doc = fixture()
        for name in SCENARIOS:
            equity = Decimal("10000")
            for row in doc["scenarios"][name]:
                equity *= Decimal("0.998")
                row["equity_usd"] = str(equity)
        result = evaluate(doc)
        self.assertFalse(result["numeric_train_pass_both_scenarios"])
        for name in SCENARIOS:
            self.assertFalse(result["scenarios"][name]["gates"]["positive_total"])
            self.assertFalse(result["scenarios"][name]["gates"]["fold_positive"])

    def test_missing_or_duplicate_day_fails_closed(self):
        for change in ("missing", "duplicate", "sealed", "reorder", "fold"):
            with self.subTest(change=change):
                doc = fixture()
                rows = doc["scenarios"]["severe"]
                if change == "missing":
                    rows.pop()
                elif change == "duplicate":
                    rows[1] = dict(rows[0])
                elif change == "sealed":
                    rows[-1]["ts_ms"] = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp()*1000)
                elif change == "reorder":
                    rows[10], rows[11] = rows[11], rows[10]
                else:
                    rows[1]["fold"] = 5
                with self.assertRaises(ValueError):
                    evaluate(doc)

    def test_missing_regime_blocks_numeric_pass(self):
        doc = fixture()
        for name in SCENARIOS:
            for row in doc["scenarios"][name]:
                row["regime"] = "BULL_LOW_VOL"
        result = evaluate(doc)
        self.assertFalse(result["numeric_train_pass_both_scenarios"])
        self.assertFalse(result["scenarios"]["severe"]["gates"]["six_regimes_present"])

    def test_scenario_mismatch_rejected(self):
        for key, value in (("benchmark_usd", "999999"),
                           ("regime", "BEAR_HIGH_VOL")):
            doc = fixture()
            doc["scenarios"]["supersevere"][20][key] = value
            with self.assertRaisesRegex(ValueError, "SCENARIO_BENCHMARK_OR_REGIME"):
                evaluate(doc)

    def test_no_boolean_provenance_or_nonfixture_promotion(self):
        for change in ("nonfixture", "missing_scenario", "wrong_schema"):
            with self.subTest(change=change):
                doc = fixture()
                if change == "nonfixture":
                    doc["fixture"] = False
                elif change == "missing_scenario":
                    del doc["scenarios"]["supersevere"]
                else:
                    doc["schema"] = "ORIGINAL_ECONOMIC_TRAIN_CERTIFIED"
                with self.assertRaisesRegex(ValueError, "PROVENANCE_NOT_CERTIFIED"):
                    evaluate(doc)

    def test_invalid_equity_and_regime_fails_closed(self):
        for key, value in (("equity_usd", "NaN"),
                           ("equity_usd", "0"),
                           ("equity_usd", "-1"),
                           ("benchmark_usd", True),
                           ("regime", "POSTHOC_WINNING_REGIME"),
                           ("actual_exposure_key", "")):
            with self.subTest(key=key, value=value):
                doc = fixture()
                doc["scenarios"]["severe"][2][key] = value
                with self.assertRaises(ValueError):
                    evaluate(doc)


if __name__ == "__main__":
    unittest.main()
