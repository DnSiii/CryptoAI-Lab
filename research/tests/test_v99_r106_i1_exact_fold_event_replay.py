"""Exact intraday fold NAV controls. Synthetic only; never historical PnL."""
import copy
import unittest
from decimal import Decimal

from research.tests.test_v99_r106_i1_native_event_equity import flat_fixture, ms
from research.tests.test_v99_r106_i1_train_numeric_gate import fixture as numeric_fixture
from research.tools.v99_r106_i1_native_event_equity import replay, INTRADAY_FOLD_EDGES
from research.tools.v99_r106_i1_train_numeric_gate import evaluate
from research.verification.independent_v99_r106_i1_train_numeric_oracle import verify


def edge_fixture():
    doc = flat_fixture()
    for scenario in ("severe", "supersevere"):
        for row in doc["scenarios"][scenario]:
            if any(row["ts_ms"] // 86400000 == edge // 86400000
                   for edge in INTRADAY_FOLD_EDGES):
                row["fold_edge_index_usd"] = {"BTC": "40000", "ETH": "3000"}
    return doc


class ExactFoldEventTests(unittest.TestCase):
    def test_four_original_fold_clocks_from_native_flat_wallet(self):
        doc = edge_fixture()
        source = replay(doc)
        self.assertTrue(source["exact_fold_edge_nav_available"])
        for scenario in ("severe", "supersevere"):
            snapshots = source["fold_edge_snapshots"][scenario]
            self.assertEqual([x["ts_ms"] for x in snapshots], list(INTRADAY_FOLD_EDGES))
            self.assertEqual([Decimal(x["equity_usd"]) for x in snapshots],
                             [Decimal("7000")] * 4)
            self.assertEqual([Decimal(x["benchmark_usd"]) for x in snapshots],
                             [Decimal("7000")] * 4)
        numeric = evaluate(source)
        self.assertTrue(numeric["exact_chronological_fold_gate_evaluable"])
        self.assertFalse(numeric["exact_chronological_fold_gate_pass"])
        self.assertFalse(numeric["formal_numeric_train_pass_both_scenarios"])
        self.assertFalse(numeric["promotion_authorized"])
        self.assertEqual(numeric["missing_intraday_fold_boundary_utc"], [])
        self.assertEqual(verify(source, numeric)["status"],
                         "INDEPENDENT_FIXTURE_NUMERIC_REPLAY_MATCH")

    def test_missing_one_boundary_never_uses_daily_proxy_as_exact(self):
        doc = edge_fixture()
        for scenario in ("severe", "supersevere"):
            for row in doc["scenarios"][scenario]:
                if row["ts_ms"] == ms(2022, 4, 20, 23, 59, 59):
                    del row["fold_edge_index_usd"]
        source = replay(doc)
        self.assertFalse(source["exact_fold_edge_nav_available"])
        numeric = evaluate(source)
        self.assertFalse(numeric["exact_chronological_fold_gate_evaluable"])
        self.assertTrue(numeric["formal_train_freeze_blocked_by_missing_intraday_nav"])
        self.assertEqual(len(numeric["missing_intraday_fold_boundary_utc"]), 1)
        verify(source, numeric)

    def test_cross_scenario_original_edge_index_substitution_rejected(self):
        doc = edge_fixture()
        doc["scenarios"]["supersevere"][132]["fold_edge_index_usd"] = {
            "BTC": "39000", "ETH": "3000"}
        with self.assertRaisesRegex(ValueError, "SCENARIO_ORIGINAL_FOLD_INDEX_PATH_MISMATCH"):
            replay(doc)

    def test_reject_nonboundary_and_forged_caller_nav(self):
        doc = edge_fixture()
        doc["scenarios"]["severe"][0]["fold_edge_index_usd"] = {
            "BTC": "40000", "ETH": "3000"}
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_OR_SEALED_FOLD_EDGE_SOURCE"):
            replay(doc)
        doc = edge_fixture()
        doc["scenarios"]["severe"][0]["fold_edge_nav"] = "999999"
        with self.assertRaisesRegex(ValueError, "FORGED_CALLER_SUPPLIED_FOLD_NAV"):
            replay(doc)

    def test_reference_recomputes_exact_split_not_whole_day(self):
        doc = numeric_fixture()
        for scenario in ("severe", "supersevere"):
            doc["fold_edge_snapshots"] = doc.get(
                "fold_edge_snapshots", {"severe": [], "supersevere": []})
            for edge in INTRADAY_FOLD_EDGES:
                day = next(row for row in doc["scenarios"][scenario]
                           if row["ts_ms"] // 86400000 == edge // 86400000)
                # Synthetic mid-day NAV deliberately differs from daily close.
                doc["fold_edge_snapshots"][scenario].append({
                    "ts_ms": edge, "equity_usd": str(Decimal(day["equity_usd"]) * Decimal("0.99")),
                    "benchmark_usd": "10000", "actual_exposure_key": "CASH"})
        result = evaluate(doc)
        self.assertTrue(result["exact_chronological_fold_gate_evaluable"])
        self.assertEqual(verify(doc, result)["status"],
                         "INDEPENDENT_FIXTURE_NUMERIC_REPLAY_MATCH")
        self.assertNotEqual(result["scenarios"]["severe"]["exact_fold_roi_descriptive_only"],
                            result["scenarios"]["severe"]["fold_roi"])
        forged = copy.deepcopy(result)
        forged["scenarios"]["severe"]["exact_fold_roi_descriptive_only"][0] = "999"
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_EXACT_FOLD_RECOMPOSITION_MISMATCH"):
            verify(doc, forged)
        self.assertFalse(result["formal_numeric_train_pass_both_scenarios"])
        self.assertFalse(result["promotion_authorized"])


if __name__ == "__main__":
    unittest.main()
