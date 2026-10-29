"""Synthetic exact-fold original quote scheduling controls; NO source certification."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from research.tools.v99_r106_i1_source_to_mark_event_spine import (
    _held_mark_clocks, compile_spine, EXACT_FOLD_EDGES,
)
from research.verification.independent_v99_r106_i1_source_spine_journal_parity import (
    verify as independent_lifecycle,
)


def ms(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)


class ExactIntradayOriginalFoldSource(unittest.TestCase):
    def setUp(self):
        self.open = ms(2022, 4, 18)
        self.expiry = ms(2022, 5, 20, 8)
        self.edge = ms(2022, 4, 20, 4)
        self.short = "BTC-20MAY22-36000-P"
        self.long = "BTC-20MAY22-32000-P"
        self.position = {
            "position_id": "BTC-APR18", "decision_ms": self.open,
            "asset": "BTC", "short_symbol": self.short, "long_symbol": self.long,
        }
        self.books = [
            {"symbol": self.short, "bid_coin": "0.05", "ask_coin": "0.052",
             "arrival_us": self.open * 1000 - 1_000_000,
             "venue_us": self.open * 1000 - 1_500_000},
            {"symbol": self.long, "bid_coin": "0.008", "ask_coin": "0.01",
             "arrival_us": self.open * 1000 - 1_000_000,
             "venue_us": self.open * 1000 - 1_500_000},
        ]
        self.entry = {
            "source_manifest_sha256": "synthetic-source-only",
            "rows": [{
                "decision_ms": self.open, "asset": "BTC",
                "signal": "POSITIVE_EX_ANTE_PREMIUM",
                "original_books": self.books,
            }],
        }

    def receipts(self, files, requests, *, omit_edge=False):
        original = {}
        for (clock, asset, symbol) in requests:
            if omit_edge and clock == self.edge:
                continue
            arrival = clock * 1000 - 1_000_000
            venue = clock * 1000 - 1_500_000
            row = {
                "exchange": "deribit", "symbol": symbol,
                "bid_price": "0.05" if symbol == self.short else "0.008",
                "ask_price": "0.052" if symbol == self.short else "0.01",
                "bid_amount": "2", "ask_amount": "2",
            }
            original[(clock, asset, symbol)] = (arrival, 1, 1, venue, row)
        return original

    def compile(self, *, omit_edge=False):
        with (
            patch("research.tools.v99_r106_i1_source_to_mark_event_spine._original_manifest",
                  return_value=({}, "synthetic-source-only")),
            patch("research.tools.v99_r106_i1_source_to_mark_event_spine.verify",
                  return_value={"independently_verified_asset_weeks": 180}),
            patch("research.tools.v99_r106_i1_source_to_mark_event_spine._last_original_quotes",
                  side_effect=lambda files, requests:
                  self.receipts(files, requests, omit_edge=omit_edge)),
        ):
            return compile_spine(".", self.entry, [self.position])

    def test_exact_active_fold_added_without_daily_interpolation(self):
        clocks = _held_mark_clocks(self.open, self.expiry)
        self.assertIn(self.edge, clocks)
        self.assertEqual(len([t for t in EXACT_FOLD_EDGES if t in clocks]), 1)
        spine = self.compile()
        self.assertEqual(spine["same_contract_exact_intraday_fold_marks"], 1)
        self.assertEqual(spine["same_contract_all_marks"],
                         spine["same_contract_daily_marks"] + 1)
        marks = [e for day in spine["days"] for e in day["market_events"]
                 if e["kind"] == "MARK_SOURCE_ONLY"]
        self.assertEqual([e["at_ms"] for e in marks if e["at_ms"] == self.edge],
                         [self.edge])
        self.assertTrue(all(e["short"]["symbol"] == self.short and
                            e["long"]["symbol"] == self.long for e in marks))
        self.assertEqual(spine["expiry_due_count"], 1)
        self.assertFalse(spine["promotion_authorized"])

        # Independent oracle does NOT import the production source clock helper.
        days = []
        for day in spine["days"]:
            events = []
            for e in day["market_events"]:
                if e["kind"] == "OPEN_SOURCE_ONLY":
                    events.append({"kind": "OPEN", "at_ms": e["at_ms"],
                                   "asset": e["asset"], "position_id": e["position_id"]})
                elif e["kind"] == "MARK_SOURCE_ONLY":
                    events.append({"kind": "MARK", "at_ms": e["at_ms"],
                                   "asset": e["asset"], "position_id": e["position_id"],
                                   "short": {"asset": e["asset"], "symbol": self.short},
                                   "long": {"asset": e["asset"], "symbol": self.long}})
                elif e["kind"] == "SETTLEMENT_DUE_SOURCE_ONLY":
                    events.append({"kind": "SETTLE_BATCH", "at_ms": e["at_ms"],
                                   "asset": e["asset"], "position_ids": [e["position_id"]]})
            days.append({"events": events})
        journal = {"fixture": False, "scenarios": {"severe": days,
                                                    "supersevere": days}}
        count = spine["same_contract_all_marks"]
        report = {
            "schema": "V99_I1_ORIGINAL_SPINE_NATIVE_JOURNAL_PARITY_V1",
            "promotion_authorized": False,
            "scenarios": {scenario: {
                "positions": 1, "source_mark_events": count,
                "source_expiry_due_events": 1, "native_event_schedule_matched": True,
            } for scenario in ("severe", "supersevere")},
        }
        self.assertEqual(independent_lifecycle(journal, report)["scenarios"]
                         ["severe"]["verified_daily_marks"], count)
        for scenario in ("severe", "supersevere"):
            for day in journal["scenarios"][scenario]:
                day["events"] = [e for e in day["events"]
                                 if not (e["kind"] == "MARK"
                                         and e["at_ms"] == self.edge)]
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_HELD_MARK_GRID_MISMATCH"):
            independent_lifecycle(journal, report)

    def test_source_edge_mark_reaches_native_exact_fold_wallet(self):
        """Synthetic source spine -> 661d wallet replay at exact edge, no PnL claim."""
        from research.tests.test_v99_r106_i1_native_event_equity import flat_fixture
        from research.tools.v99_r106_i1_native_event_equity import replay
        from research.tools.v99_r106_i1_full_archive_intake import eligible
        from research.tools.v99_r106_i1_train_numeric_gate import _fold

        spine = self.compile()
        journal = flat_fixture()
        journal["fixture"] = False
        decisions = []
        for day in eligible(True):
            at = int(day.timestamp() * 1000)
            for asset in ("BTC", "ETH"):
                positive = at == self.open and asset == "BTC"
                decisions.append({
                    "decision_ms": at, "asset": asset, "fold": _fold(at),
                    "signal": "POSITIVE_EX_ANTE_PREMIUM" if positive else "NO_30D_HISTORY",
                    "action": "OPEN" if positive else "CASH",
                    "reason": "FIXED_VERTICAL" if positive else "NO_30D_HISTORY",
                })
        journal["scenario_decisions"] = {
            "severe": [dict(row) for row in decisions],
            "supersevere": [dict(row) for row in decisions],
        }

        def native_quote(source):
            symbol = source["symbol"]
            return {
                "asset": "BTC", "symbol": symbol, "expiry_ms": self.expiry,
                "strike_usd": symbol.split("-")[2],
                "bid_coin": source["bid_coin"], "ask_coin": source["ask_coin"],
                "bid_native_lots": source.get("bid_size_source_units", "2"),
                "ask_native_lots": source.get("ask_size_source_units", "2"),
                "venue_ms": source["venue_us"] // 1000,
                "arrival_ms": source["arrival_us"] // 1000,
                "index_usd": "40000",
            }

        for scenario in ("severe", "supersevere"):
            fee = "0.0024" if scenario == "severe" else "0.0048"
            for native_day, source_day in zip(journal["scenarios"][scenario],
                                              spine["days"]):
                self.assertEqual(native_day["ts_ms"], source_day["ts_ms"])
                for source in source_day["market_events"]:
                    kind = source["kind"]
                    event = {"at_ms": source["at_ms"], "asset": "BTC"}
                    if kind == "OPEN_SOURCE_ONLY":
                        event.update({
                            "kind": "OPEN", "position_id": source["position_id"],
                            "signal": {"decision_ms": self.open, "asset": "BTC",
                                       "fold": _fold(self.open),
                                       "signal": "POSITIVE_EX_ANTE_PREMIUM"},
                            "quotes": [native_quote(q) for q in source["candidate_inventory"]],
                            "fee_coin": fee, "slippage_coin": fee,
                            "initial_margin_coin": "0.01",
                            "maintenance_margin_coin": "0.005",
                        })
                    elif kind == "MARK_SOURCE_ONLY":
                        event.update({
                            "kind": "MARK", "position_id": source["position_id"],
                            "short": native_quote(source["short"]),
                            "long": native_quote(source["long"]),
                            "fee_coin": fee, "slippage_coin": fee,
                        })
                    else:
                        event.update({
                            "kind": "SETTLE_BATCH", "position_ids": [source["position_id"]],
                            "delivery_index_usd": "40000",
                            "delivery_fees_coin": {source["position_id"]: fee},
                        })
                    native_day["events"].append(event)
                native_day["events"].sort(key=lambda e: e["at_ms"])
                if any(native_day["ts_ms"] - 86_399_000 <= edge <= native_day["ts_ms"]
                       for edge in EXACT_FOLD_EDGES):
                    native_day["fold_edge_index_usd"] = {"BTC": "40000", "ETH": "3000"}

        replayed = replay(journal)
        self.assertTrue(replayed["exact_fold_edge_nav_available"])
        self.assertEqual(
            [s["ts_ms"] for s in replayed["fold_edge_snapshots"]["severe"]],
            list(EXACT_FOLD_EDGES),
        )
        self.assertFalse(replayed["original_historical_economic_train_executed"])
        self.assertFalse(replayed["promotion_authorized"])

        # Adversarial: removing the exact edge mark cannot fall back to
        # previous day's quote, even with a same-day 23:59:59 mark present.
        for scenario in ("severe", "supersevere"):
            for day in journal["scenarios"][scenario]:
                day["events"] = [e for e in day["events"]
                                 if not (e["kind"] == "MARK"
                                         and e["at_ms"] == self.edge)]
        with self.assertRaisesRegex(ValueError, "MISSING_EXACT_FOLD_SAME_CLOCK_OPEN_MARKS"):
            replay(journal)

    def test_missing_actual_preedge_original_quote_blocks(self):
        with self.assertRaisesRegex(ValueError,
                                    "MISSING_ORIGINAL_HELD_CONTRACT_DAILY_MARK"):
            self.compile(omit_edge=True)

    def test_no_edge_for_position_already_expired(self):
        self.assertFalse(any(t in EXACT_FOLD_EDGES
                             for t in _held_mark_clocks(ms(2021, 12, 13),
                                                       ms(2022, 1, 14, 8))))


if __name__ == "__main__":
    unittest.main()
