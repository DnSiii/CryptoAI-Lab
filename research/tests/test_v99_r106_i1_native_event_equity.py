"""Synthetic controls for native event-to-equity engine; NO original ROI."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_i1_native_event_equity import replay, SCHEMA
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_train_numeric_gate import (
    DAYS, REGIMES, SCENARIOS, _expected_clock, _fold, evaluate,
)

BTC_INDEX = "40000"
ETH_INDEX = "3000"


def flat_fixture():
    doc = {
        "schema": SCHEMA, "fixture": True,
        "initial_coin": {"BTC": "0.1", "ETH": "1"},
        "initial_index_usd": {"BTC": BTC_INDEX, "ETH": ETH_INDEX},
        "initial_capital_usd": "7000",
        "scenarios": {},
    }
    for scenario in SCENARIOS:
        doc["scenarios"][scenario] = [
            {"ts_ms": _expected_clock(i), "fold": _fold(_expected_clock(i)),
             "regime": REGIMES[i % 6], "benchmark_usd": "7000",
             "index_usd": {"BTC": BTC_INDEX, "ETH": ETH_INDEX}, "events": []}
            for i in range(DAYS)
        ]
    return doc


def ms(y, m, d, h=0, minute=0, second=0):
    return int(datetime(y, m, d, h, minute, second,
                        tzinfo=timezone.utc).timestamp()*1000)


def quote(symbol, bid, ask, at_ms):
    return {
        "asset": "BTC", "symbol": symbol, "expiry_ms": ms(2022, 1, 14, 8),
        "strike_usd": symbol.split("-")[2], "bid_coin": bid,
        "ask_coin": ask, "bid_native_lots": "2", "ask_native_lots": "2",
        "venue_ms": at_ms-1500, "arrival_ms": at_ms-1000,
        "index_usd": BTC_INDEX,
    }


def one_position_fixture():
    doc = flat_fixture()
    entry = ms(2021, 12, 13)
    expiry = ms(2022, 1, 14, 8)
    short = "BTC-14JAN22-36000-P"
    long = "BTC-14JAN22-32000-P"
    for scenario in SCENARIOS:
        fee = "0.0024" if scenario == "severe" else "0.0048"
        rows = doc["scenarios"][scenario]
        row = next(x for x in rows if x["ts_ms"] == ms(2021, 12, 13, 23, 59, 59))
        row["events"].append({
            "kind": "OPEN", "at_ms": entry, "asset": "BTC",
            "position_id": "BTC-W1",
            "signal": {"decision_ms": entry, "asset": "BTC", "fold": 1,
                       "signal": "POSITIVE_EX_ANTE_PREMIUM"},
            "quotes": [quote(short, "0.05", "0.052", entry),
                       quote(long, "0.008", "0.01", entry)],
            "fee_coin": fee, "slippage_coin": fee,
            "initial_margin_coin": "0.01", "maintenance_margin_coin": "0.005",
        })
        for item in rows:
            clock = item["ts_ms"]
            if entry <= clock < expiry:
                item["events"].append({
                    "kind": "MARK", "at_ms": clock, "asset": "BTC",
                    "position_id": "BTC-W1", "fee_coin": fee,
                    "slippage_coin": fee,
                    "short": quote(short, "0.05", "0.052", clock),
                    "long": quote(long, "0.008", "0.01", clock),
                })
            if ms(2022, 1, 14, 23, 59, 59) == clock:
                item["events"].append({
                    "kind": "SETTLE_BATCH", "at_ms": expiry, "asset": "BTC",
                    "position_ids": ["BTC-W1"], "delivery_index_usd": BTC_INDEX,
                    "delivery_fees_coin": {"BTC-W1": fee},
                })
        # The daily events are chronological within the expiry date.
    return doc



def complete_fixed_decisions(*, one_open=False):
    """Synthetic 180-row audit ledger, NOT independently verified signals."""
    rows = []
    for day in eligible(True):
        at = int(day.timestamp()*1000)
        for asset in ("BTC", "ETH"):
            opening = one_open and asset == "BTC" and at == ms(2021, 12, 13)
            rows.append({
                "decision_ms": at, "asset": asset, "fold": _fold(at),
                "signal": ("POSITIVE_EX_ANTE_PREMIUM" if opening
                           else "NO_30D_HISTORY"),
                "action": "OPEN" if opening else "CASH",
                "reason": "FIXED_VERTICAL" if opening else "NO_30D_HISTORY",
            })
    assert len(rows) == 180
    return rows


class NativeEventEquityTests(unittest.TestCase):
    def test_661_day_two_coin_flat_native_identity(self):
        source = flat_fixture()
        report = replay(source)
        self.assertEqual(len(report["scenarios"]["severe"]), DAYS)
        for scenario in SCENARIOS:
            self.assertEqual({x["equity_usd"] for x in report["scenarios"][scenario]},
                             {"7000.0"})
            self.assertEqual({x["actual_exposure_key"] for x in report["scenarios"][scenario]},
                             {"CASH"})
        self.assertFalse(report["original_options_economic_train_certified"])
        self.assertFalse(report["promotion_authorized"])
        # An actual 661d numeric run on these derived synthetic flat wallets
        # correctly REJECTS positive-return and benchmark-excess gates.
        numeric = evaluate(report)
        self.assertFalse(numeric["numeric_train_pass_both_scenarios"])
        self.assertFalse(numeric["scenarios"]["severe"]["gates"]["positive_total"])

    def test_original_shape_single_vertical_661d_native_accounting(self):
        source = one_position_fixture()
        report = replay(source)
        # Independent arithmetic from quoted sides, not reported equity:
        # Severe opening 0.05 - 0.01 - 2*(0.0024) = +0.0352 BTC;
        # expiry pays 0 intrinsic and 0.0024 BTC fee.
        # Supersevere opening +0.0304 BTC; expiry fee 0.0048.
        expected = {"severe": Decimal("0.1328"),
                    "supersevere": Decimal("0.1256")}
        for scenario in SCENARIOS:
            rows = report["scenarios"][scenario]
            final = Decimal(rows[-1]["equity_usd"])
            independent = expected[scenario]*Decimal(BTC_INDEX) + Decimal(ETH_INDEX)
            self.assertEqual(final, independent)
            self.assertEqual(rows[-1]["actual_exposure_key"], "CASH")
            self.assertEqual(next(x for x in rows if x["ts_ms"] ==
                                  ms(2021, 12, 13, 23, 59, 59))["actual_exposure_key"],
                             "BTC:BTC-W1")
            self.assertLess(Decimal(next(x for x in rows if x["ts_ms"] ==
                                         ms(2021, 12, 13, 23, 59, 59))["equity_usd"]),
                            Decimal("7000"))
        self.assertFalse(report["original_source_receipts_independently_authenticated"])
        self.assertFalse(report["historical_native_fee_certified"])
        # Run the existing ex-ante numeric gate on the DERIVED event equity,
        # not a hand-written profitable NAV series. One winning fold is not
        # stable growth; the synthetic trade must NOT be promoted.
        numeric = evaluate(report)
        self.assertFalse(numeric["numeric_train_pass_both_scenarios"])
        for scenario in SCENARIOS:
            self.assertEqual(numeric["scenarios"][scenario]["positive_folds"], 1)
            self.assertFalse(numeric["scenarios"][scenario]["gates"]["fold_positive"])
        self.assertFalse(numeric["promotion_authorized"])

    def test_missing_mark_after_open_fails_closed(self):
        doc = one_position_fixture()
        for scenario in SCENARIOS:
            rows = doc["scenarios"][scenario]
            first = next(x for x in rows if x["ts_ms"] ==
                         ms(2021, 12, 13, 23, 59, 59))
            first["events"].pop()
        with self.assertRaisesRegex(ValueError, "MISSING_SAME_CLOCK_DAILY_OPEN_MARK"):
            replay(doc)

    def test_forged_credit_or_caller_nav_rejected(self):
        doc = flat_fixture()
        doc["scenarios"]["severe"][0]["events"] = [{
            "kind": "CREDIT", "asset": "BTC",
            "at_ms": ms(2021, 12, 9, 8), "amount_coin": "1000"}]
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_NATIVE_CASH_FLOW"):
            replay(doc)
        doc = flat_fixture()
        doc["scenarios"]["severe"][0]["equity_usd"] = "99999999"
        # Caller-provided equity is never read, so it cannot inflate results.
        self.assertEqual(replay(doc)["scenarios"]["severe"][0]["equity_usd"], "7000.0")

    def test_sealed_and_wrong_source_index_rejected(self):
        doc = flat_fixture()
        doc["scenarios"]["severe"][-1]["ts_ms"] = ms(2023, 10, 1)
        with self.assertRaisesRegex(ValueError, "FORGED_OR_SEALED_DAILY_EVENT_GRID"):
            replay(doc)
        doc = one_position_fixture()
        for row in doc["scenarios"]["severe"]:
            if row["ts_ms"] == ms(2021, 12, 13, 23, 59, 59):
                row["index_usd"]["BTC"] = "45000"
        with self.assertRaisesRegex(ValueError, "UNBOUND_ORIGINAL_INDEX"):
            replay(doc)

    def test_one_entry_per_asset_week_is_not_bypassable(self):
        doc = one_position_fixture()
        first = next(x for x in doc["scenarios"]["severe"] if x["ts_ms"] ==
                     ms(2021, 12, 13, 23, 59, 59))
        forged = copy.deepcopy(first["events"][0])
        forged["position_id"] = "BTC-W1-EXTRA"
        first["events"].insert(1, forged)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_FIXED_ASSET_WEEK_ENTRY"):
            replay(doc)

    def test_common_original_index_path_required_for_both_cost_scenarios(self):
        doc = flat_fixture()
        doc["scenarios"]["supersevere"][120]["index_usd"]["BTC"] = "41000"
        # Remove the optional supplied benchmark so this adversarial case
        # reaches the independent cross-scenario original-index path guard.
        del doc["scenarios"]["supersevere"][120]["benchmark_usd"]
        # Passive native benchmark is derived from each scenario's indices,
        # so mismatched original paths also mismatch the benchmark first.
        with self.assertRaisesRegex(ValueError,
                                    "SCENARIO_(BENCHMARK_OR_REGIME|ORIGINAL_INDEX)_PATH_MISMATCH"):
            replay(doc)

    def test_original_native_scenario_fee_floor_enforced(self):
        doc = one_position_fixture()
        first = next(x for x in doc["scenarios"]["severe"] if x["ts_ms"] ==
                     ms(2021, 12, 13, 23, 59, 59))
        first["events"][0]["fee_coin"] = "0.0001"
        with self.assertRaisesRegex(ValueError, "SEVERE_SUPERSEVERE_FRICTION_UNDERPAYMENT"):
            replay(doc)

    def test_661d_varying_native_collateral_benchmark_is_derived(self):
        doc = flat_fixture()
        for scenario in SCENARIOS:
            for i, row in enumerate(doc["scenarios"][scenario]):
                btc = Decimal("40000") + Decimal(i)*Decimal("13")
                eth = Decimal("3000") - Decimal(i)*Decimal("2")
                row["index_usd"] = {"BTC": str(btc), "ETH": str(eth)}
                # No caller-supplied benchmark: it must be derived from
                # initial 0.1 BTC + 1 ETH, not the static USD initial NAV.
                del row["benchmark_usd"]
        report = replay(doc)
        for scenario in SCENARIOS:
            rows = report["scenarios"][scenario]
            for i in (0, 1, 120, 330, 660):
                expected = (Decimal("0.1")*(Decimal("40000")+Decimal(i)*13)
                            + Decimal("3000")-Decimal(i)*2)
                self.assertEqual(Decimal(rows[i]["benchmark_usd"]), expected)
                self.assertEqual(Decimal(rows[i]["equity_usd"]), expected)
        self.assertFalse(report["original_options_economic_train_certified"])

    def test_positive_coin_beta_is_not_option_alpha(self):
        doc = flat_fixture()
        for scenario in SCENARIOS:
            for i, row in enumerate(doc["scenarios"][scenario]):
                row["index_usd"] = {
                    "BTC": str(Decimal("40000") + Decimal(i)*13),
                    "ETH": str(Decimal("3000") + Decimal(i)*2),
                }
                del row["benchmark_usd"]
        report = replay(doc)
        numeric = evaluate(report)
        for scenario in SCENARIOS:
            outcome = numeric["scenarios"][scenario]
            # USD NAV grows from passive BTC/ETH collateral only; the
            # fixed native options strategy never opened a position.
            self.assertGreater(Decimal(outcome["total_roi"]), 0)
            self.assertEqual(outcome["total_roi"], outcome["benchmark_roi"])
            self.assertFalse(outcome["gates"]["original_benchmark_excess"])
            self.assertFalse(outcome["numeric_pass"])
        self.assertFalse(numeric["numeric_train_pass_both_scenarios"])
        self.assertFalse(numeric["promotion_authorized"])

    def test_forged_low_or_high_passive_benchmark_rejected(self):
        for forged in ("1", "999999999"):
            with self.subTest(forged=forged):
                doc = flat_fixture()
                doc["scenarios"]["severe"][40]["benchmark_usd"] = forged
                with self.assertRaisesRegex(ValueError,
                                            "FORGED_PASSIVE_NATIVE_BENCHMARK"):
                    replay(doc)

    def test_nonfixture_replay_is_explicitly_uncertified(self):
        doc = flat_fixture()
        doc["fixture"] = False
        with self.assertRaisesRegex(ValueError, "MISSING_COMPLETE_FIXED_180_DECISION_LEDGER"):
            replay(doc)
        doc["decisions"] = complete_fixed_decisions()
        report = replay(doc)
        self.assertEqual(report["status"], "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY")
        self.assertFalse(report["original_historical_economic_train_executed"])
        self.assertFalse(report["promotion_authorized"])
        # The official numeric gate still refuses nonfixture without independent
        # original source/fill/fee/margin attestation.
        with self.assertRaisesRegex(ValueError, "PROVENANCE_NOT_CERTIFIED"):
            evaluate(report)


    def test_180_decisions_cover_actual_one_open_in_both_cost_paths(self):
        doc = one_position_fixture()
        doc["decisions"] = complete_fixed_decisions(one_open=True)
        report = replay(doc)
        self.assertEqual(len(report["scenarios"]["severe"]), 661)
        self.assertFalse(report["original_options_economic_train_certified"])
        self.assertFalse(report["promotion_authorized"])

    def test_missing_shifted_duplicate_and_cherrypicked_decisions_rejected(self):
        original = one_position_fixture()
        original["decisions"] = complete_fixed_decisions(one_open=True)
        for mode, expected in (
            ("missing", "MISSING_COMPLETE_FIXED_180_DECISION_LEDGER"),
            ("duplicate", "MISSING_DUPLICATE_OR_SHIFTED_FIXED_DECISION"),
            ("shifted", "MISSING_DUPLICATE_OR_SHIFTED_FIXED_DECISION"),
            ("cash_with_open", "MISSING_OR_SELECTIVE_FIXED_DECISION_EXECUTION"),
            ("open_without_event", "MISSING_OR_SELECTIVE_FIXED_DECISION_EXECUTION"),
            ("open_without_positive_signal", "OPEN_WITHOUT_POSITIVE_FIXED_SIGNAL"),
            ("cash_wrong_reason", "UNJUSTIFIED_FIXED_CASH_DECISION"),
            ("open_signal_forged", "UNBOUND_OPEN_TO_FIXED_ORIGINAL_SIGNAL"),
        ):
            with self.subTest(mode=mode):
                doc = copy.deepcopy(original)
                if mode == "missing":
                    doc["decisions"].pop()
                elif mode == "duplicate":
                    doc["decisions"][1] = copy.deepcopy(doc["decisions"][0])
                elif mode == "shifted":
                    doc["decisions"][2]["decision_ms"] += 60_000
                elif mode == "cash_with_open":
                    doc["decisions"][0]["action"] = "CASH"
                    doc["decisions"][0]["reason"] = "RISK_VETO"
                elif mode == "open_without_event":
                    for scenario in SCENARIOS:
                        for row in doc["scenarios"][scenario]:
                            row["events"] = [event for event in row["events"]
                                             if event.get("kind") != "OPEN"]
                elif mode == "open_without_positive_signal":
                    doc["decisions"][0]["signal"] = "NO_PREMIUM"
                elif mode == "cash_wrong_reason":
                    doc["decisions"][1]["reason"] = "RISK_VETO"
                elif mode == "open_signal_forged":
                    for scenario in SCENARIOS:
                        for row in doc["scenarios"][scenario]:
                            for event in row["events"]:
                                if event.get("kind") == "OPEN":
                                    event["signal"]["signal"] = "NO_PREMIUM"
                with self.assertRaisesRegex(ValueError, expected):
                    replay(doc)

    def test_self_declared_cash_is_not_source_authentication(self):
        doc = flat_fixture()
        doc["fixture"] = False
        doc["decisions"] = complete_fixed_decisions()
        doc["decisions"][0]["signal"] = "POSITIVE_EX_ANTE_PREMIUM"
        doc["decisions"][0]["reason"] = "NO_ELIGIBLE_FIXED_VERTICAL"
        report = replay(doc)
        self.assertFalse(report["original_source_receipts_independently_authenticated"])
        with self.assertRaisesRegex(ValueError, "PROVENANCE_NOT_CERTIFIED"):
            evaluate(report)


if __name__ == "__main__":
    unittest.main()
