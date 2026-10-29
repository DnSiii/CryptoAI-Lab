"""Exact intraday fold NAV controls. Synthetic only; never historical PnL."""
import copy
import unittest
from decimal import Decimal

from research.tests.test_v99_r106_i1_native_event_equity import flat_fixture, ms, quote
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

    def test_live_position_requires_original_same_clock_edge_mark(self):
        doc = edge_fixture()
        entry, expiry = ms(2022, 4, 18), ms(2022, 5, 20, 8)
        short, long = "BTC-20MAY22-36000-P", "BTC-20MAY22-32000-P"
        def book(symbol, bid, ask, clock):
            q = quote(symbol, bid, ask, clock)
            q["expiry_ms"] = expiry
            return q
        for scenario in ("severe", "supersevere"):
            fee = "0.0024" if scenario == "severe" else "0.0048"
            rows = doc["scenarios"][scenario]
            opening = next(r for r in rows if r["ts_ms"] == ms(2022, 4, 18, 23, 59, 59))
            opening["events"].append({
                "kind": "OPEN", "at_ms": entry, "asset": "BTC",
                "position_id": "BTC-EDGE",
                "signal": {"decision_ms": entry, "asset": "BTC", "fold": 1,
                           "signal": "POSITIVE_EX_ANTE_PREMIUM"},
                "quotes": [book(short, "0.05", "0.052", entry),
                           book(long, "0.008", "0.01", entry)],
                "fee_coin": fee, "slippage_coin": fee,
                "initial_margin_coin": "0.01", "maintenance_margin_coin": "0.005"})
            for row in rows:
                clock = row["ts_ms"]
                if entry <= clock < expiry:
                    if clock == ms(2022, 4, 20, 23, 59, 59):
                        edge = ms(2022, 4, 20, 4)
                        row["events"].append({
                            "kind": "MARK", "at_ms": edge, "asset": "BTC",
                            "position_id": "BTC-EDGE", "fee_coin": fee,
                            "slippage_coin": fee,
                            "short": book(short, "0.05", "0.052", edge),
                            "long": book(long, "0.008", "0.01", edge)})
                    row["events"].append({
                        "kind": "MARK", "at_ms": clock, "asset": "BTC",
                        "position_id": "BTC-EDGE", "fee_coin": fee,
                        "slippage_coin": fee,
                        "short": book(short, "0.05", "0.052", clock),
                        "long": book(long, "0.008", "0.01", clock)})
                if clock == ms(2022, 5, 20, 23, 59, 59):
                    row["events"].append({
                        "kind": "SETTLE_BATCH", "at_ms": expiry, "asset": "BTC",
                        "position_ids": ["BTC-EDGE"],
                        "delivery_index_usd": "40000",
                        "delivery_fees_coin": {"BTC-EDGE": fee}})
        source = replay(doc)
        self.assertTrue(source["exact_fold_edge_nav_available"])
        self.assertNotEqual(source["fold_edge_snapshots"]["severe"][0]["equity_usd"], "7000.0")
        numeric = evaluate(source)
        verify(source, numeric)
        self.assertFalse(numeric["promotion_authorized"])
        for scenario in ("severe", "supersevere"):
            row = next(r for r in doc["scenarios"][scenario]
                       if r["ts_ms"] == ms(2022, 4, 20, 23, 59, 59))
            row["events"] = [e for e in row["events"] if e["at_ms"] != ms(2022, 4, 20, 4)]
        with self.assertRaisesRegex(ValueError, "MISSING_EXACT_FOLD_SAME_CLOCK_OPEN_MARKS"):
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
