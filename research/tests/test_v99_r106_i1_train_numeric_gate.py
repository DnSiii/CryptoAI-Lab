"""Fixture-only complete-TRAIN numeric risk gate controls, not option profits."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from research.verification.independent_v99_r106_i1_train_numeric_oracle import verify as independent_verify
from research.tools.v99_r106_i1_train_numeric_gate import (
    DAYS, FIRST, REGIMES, SCENARIOS, _expected_clock, _fold, evaluate, evaluate_provisional,
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



def with_exact_synthetic_snapshots(doc, *, two_negative_folds=False):
    """Synthetic same-clock NAV controls; NOT original Deribit market evidence."""
    clocks = tuple(int(datetime(y, m, d, h, tzinfo=timezone.utc)
                       .timestamp() * 1000) for y, m, d, h in (
        (2022, 4, 20, 4), (2022, 8, 30, 9),
        (2023, 1, 9, 14), (2023, 5, 21, 19),
    ))
    snapshots = {}
    for scenario in SCENARIOS:
        rows = doc["scenarios"][scenario]
        events = []
        for j, clock in enumerate(clocks):
            day = next(i for i, row in enumerate(rows) if row["ts_ms"] >= clock)
            previous = rows[day - 1]
            nav = ("1000" if j == 0 else "100") if (
                two_negative_folds and j < 2) else previous["equity_usd"]
            events.append({
                "ts_ms": clock, "equity_usd": nav,
                "benchmark_usd": previous["benchmark_usd"],
            })
        snapshots[scenario] = events
    doc["fold_edge_snapshots"] = snapshots
    doc["exact_fold_edge_nav_available"] = True
    return doc


class NumericTrainGateTests(unittest.TestCase):
    def test_full_661_day_dual_scenario_synthetic_screen_and_independent_roi(self):
        source = fixture()
        result = evaluate(source)
        self.assertEqual(result["days_per_scenario"], 661)
        self.assertEqual(independent_verify(source, result)["status"],
                         "INDEPENDENT_FIXTURE_NUMERIC_REPLAY_MATCH")
        forged = copy.deepcopy(result)
        forged["scenarios"]["severe"]["remove_best_day_roi"] = "999"
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_NUMERIC_METRIC_MISMATCH"):
            independent_verify(source, forged)
        self.assertTrue(result["daily_proxy_numeric_screen_pass_both_scenarios"])
        self.assertFalse(result["numeric_train_pass_both_scenarios"])
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

    def test_daily_only_nav_cannot_claim_exact_intraday_fold_gate(self):
        doc = fixture()
        result = evaluate(doc)
        # Synthetic daily-proxy screen may pass 5/5, but the actual original
        # folds switch at 04, 09, 14, 19 UTC rather than daily 23:59:59.
        self.assertTrue(result["daily_proxy_numeric_screen_pass_both_scenarios"])
        self.assertFalse(result["numeric_train_pass_both_scenarios"])
        self.assertEqual(result["fold_attribution"], "DAILY_PROXY_NOT_EXACT")
        self.assertFalse(result["exact_chronological_fold_gate_evaluable"])
        self.assertFalse(result["exact_chronological_fold_gate_pass"])
        self.assertTrue(result["formal_train_freeze_blocked_by_missing_intraday_nav"])
        self.assertEqual(result["missing_intraday_fold_boundary_utc"], [
            "2022-04-20T04:00:00+00:00",
            "2022-08-30T09:00:00+00:00",
            "2023-01-09T14:00:00+00:00",
            "2023-05-21T19:00:00+00:00",
        ])
        for key, forged_value in (
            ("exact_chronological_fold_gate_evaluable", True),
            ("exact_chronological_fold_gate_pass", True),
            ("missing_intraday_fold_boundary_utc", []),
            ("fold_attribution", "EXACT"),
        ):
            forged = copy.deepcopy(result)
            forged[key] = forged_value
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                        AssertionError, "INDEPENDENT_EXACT_FOLD_BOUNDARY_UNRESOLVED"):
                    independent_verify(doc, forged)

    def test_exact_positive_synthetic_folds_control_numeric_screen_not_promotion(self):
        doc = with_exact_synthetic_snapshots(fixture())
        report = evaluate(doc)
        self.assertTrue(report["daily_proxy_numeric_screen_pass_both_scenarios"])
        self.assertTrue(report["exact_chronological_fold_gate_evaluable"])
        self.assertTrue(report["exact_fold_screen_pass_both_scenarios"])
        self.assertTrue(report["numeric_train_pass_both_scenarios"])
        self.assertFalse(report["formal_numeric_train_pass_both_scenarios"])
        self.assertFalse(report["exact_chronological_fold_gate_pass"])
        self.assertFalse(report["promotion_authorized"])
        independent_verify(doc, report)

    def test_daily_winning_proxy_cannot_hide_two_negative_exact_folds(self):
        doc = with_exact_synthetic_snapshots(fixture(), two_negative_folds=True)
        report = evaluate(doc)
        self.assertTrue(report["daily_proxy_numeric_screen_pass_both_scenarios"])
        self.assertTrue(report["exact_chronological_fold_gate_evaluable"])
        self.assertFalse(report["exact_fold_screen_pass_both_scenarios"])
        self.assertFalse(report["numeric_train_pass_both_scenarios"])
        self.assertEqual(report["scenarios"]["severe"]["exact_positive_folds"], 3)
        independent_verify(doc, report)
        forged = copy.deepcopy(report)
        forged["numeric_train_pass_both_scenarios"] = True
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_PAIRED_SCENARIO_MISMATCH"):
            independent_verify(doc, forged)

    def test_missing_exact_edges_cannot_forge_numeric_pass(self):
        doc = fixture()
        report = evaluate(doc)
        self.assertTrue(report["daily_proxy_numeric_screen_pass_both_scenarios"])
        forged = copy.deepcopy(report)
        forged["numeric_train_pass_both_scenarios"] = True
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_PAIRED_SCENARIO_MISMATCH"):
            independent_verify(doc, forged)

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


    def test_uncertified_nonfixture_native_event_replay_diagnostic(self):
        # This is an explicitly SYNTHETIC 661-day journal with no original
        # Deribit options lifecycle; the nonfixture tag does not certify it.
        from research.tests.test_v99_r106_i1_native_event_equity import (
            flat_fixture, complete_fixed_decisions,
        )
        from research.tools.v99_r106_i1_native_event_equity import replay
        doc = flat_fixture()
        doc["fixture"] = False
        doc["scenario_decisions"] = {
            scenario: complete_fixed_decisions() for scenario in SCENARIOS
        }
        source = replay(doc)
        self.assertEqual(source["status"], "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY")
        with self.assertRaisesRegex(ValueError, "PROVENANCE_NOT_CERTIFIED"):
            evaluate(source)  # the OFFICIAL gate remains sealed
        report = evaluate_provisional(source)
        self.assertEqual(report["status"],
                         "PROVISIONAL_NONFIXTURE_NUMERIC_DIAGNOSTIC_NOT_CERTIFIED")
        self.assertFalse(report["source_fixture"])
        self.assertTrue(report["numeric_screen_descriptive_only"])
        self.assertFalse(report["original_options_economic_train_certified"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["numeric_train_pass_both_scenarios"])
        self.assertEqual(independent_verify(source, report)["status"],
                         "INDEPENDENT_PROVISIONAL_NUMERIC_REPLAY_MATCH_NOT_CERTIFIED")
        forged = copy.deepcopy(report)
        forged["scenarios"]["severe"]["max_drawdown"] = "0.99"
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_NUMERIC_METRIC_MISMATCH"):
            independent_verify(source, forged)

    def test_explicit_provisional_cli_replay_is_never_certified(self):
        import json
        import tempfile
        from pathlib import Path
        from research.tools.v99_r106_i1_train_numeric_gate import main
        from research.tests.test_v99_r106_i1_native_event_equity import (
            flat_fixture, complete_fixed_decisions,
        )
        from research.tools.v99_r106_i1_native_event_equity import replay
        source = flat_fixture()
        source["fixture"] = False
        source["scenario_decisions"] = {
            scenario: complete_fixed_decisions() for scenario in SCENARIOS
        }
        journal = replay(source)
        with tempfile.TemporaryDirectory() as tmp:
            inp, out = Path(tmp)/"native.json", Path(tmp)/"diagnostic.json"
            inp.write_text(json.dumps(journal), encoding="utf-8")
            result = main(inp, out, provisional=True)
            disk = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result, disk)
            self.assertEqual(independent_verify(journal, disk)["status"],
                             "INDEPENDENT_PROVISIONAL_NUMERIC_REPLAY_MATCH_NOT_CERTIFIED")
            self.assertFalse(disk["original_options_economic_train_certified"])
            self.assertFalse(disk["promotion_authorized"])
            with self.assertRaisesRegex(ValueError, "PROVENANCE_NOT_CERTIFIED"):
                main(inp, out)  # cannot silently choose provisional mode

    def test_provisional_diagnostic_fails_closed_on_forged_provenance(self):
        from research.tests.test_v99_r106_i1_native_event_equity import (
            flat_fixture, complete_fixed_decisions,
        )
        from research.tools.v99_r106_i1_native_event_equity import replay
        doc = flat_fixture()
        doc["fixture"] = False
        doc["scenario_decisions"] = {
            scenario: complete_fixed_decisions() for scenario in SCENARIOS
        }
        original = replay(doc)
        for key, value in (
            ("fixture", True),
            ("status", "ORIGINAL_ECONOMIC_TRAIN_CERTIFIED"),
            ("original_source_receipts_independently_authenticated", True),
            ("original_options_economic_train_certified", True),
            ("historical_native_fee_certified", True),
            ("promotion_authorized", True),
            ("validation_opened", True),
        ):
            with self.subTest(key=key):
                source = copy.deepcopy(original)
                source[key] = value
                with self.assertRaisesRegex(ValueError,
                        "PROVENANCE_NOT_CERTIFIED|PROVISIONAL_SOURCE_OR_CERTIFICATION_FORGERY"):
                    evaluate_provisional(source)
        incomplete = copy.deepcopy(original)
        incomplete["scenarios"]["severe"].pop()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_661_DAY"):
            evaluate_provisional(incomplete)


if __name__ == "__main__":
    unittest.main()
