"""Fixed I1 causal spread -> coin wallet, fixture-only; no historical ROI."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_i1_fixed_vertical_bridge import (
    select_fixed_vertical, fixture_open_fixed_vertical,
)
from research.tools.v99_r106_i1_native_coin_account_replay import (
    Quote, D, start_wallet,
)
from research.tools.v99_r106_i1_cost_bound_execution import costed_mark, charge_floor
from research.verification.independent_v99_r106_i1_fixed_vertical_oracle import (
    audit_fixture,
)

OPEN = int(datetime(2022, 1, 3, tzinfo=timezone.utc).timestamp()*1000)
EXPIRY = int(datetime(2022, 2, 4, 8, tzinfo=timezone.utc).timestamp()*1000)


def signal(value="POSITIVE_EX_ANTE_PREMIUM"):
    return {"decision_ms": OPEN, "asset": "BTC", "fold": 1,
            "signal": value, "regime": "fixture_only"}


def quote(strike, bid, ask, arrival_shift=0, index="50000"):
    return Quote("BTC", f"BTC-04FEB22-{strike}-P", EXPIRY, D(strike),
                 D(bid), D(ask), D("5"), D("5"),
                 OPEN-3000+arrival_shift, OPEN-2000+arrival_shift,
                 D(index))


def book():
    return [quote("45000", ".08", ".09"), quote("40000", ".04", ".05")]


class FixedI1VerticalBridge(unittest.TestCase):
    def test_fixed_selection_not_best_backtest_return(self):
        selected = select_fixed_vertical(signal(), book() + [
            quote("44900", ".50", ".51")])
        self.assertEqual((selected[0].symbol, selected[1].symbol),
                         ("BTC-04FEB22-45000-P", "BTC-04FEB22-40000-P"))

    def test_negative_and_warmup_stay_cash(self):
        for label in ("NO_PREMIUM", "NO_30D_HISTORY"):
            before = start_wallet("BTC", "severe", "100")
            after, decision = fixture_open_fixed_vertical(
                before, signal(label), book(), name="none",
                initial_margin_coin="4", maintenance_margin_coin="2",
                fixture=True)
            self.assertEqual(decision["decision"],
                             "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL")
            self.assertEqual(audit_fixture(signal(label), book(), decision,
                                           before, after)["independent_fixture"],
                             "CASH_MATCH")

    def test_missing_unsynced_or_wrong_strikes_stay_cash(self):
        for quotes in ([], [book()[0]],
                       [book()[0], quote("40000", ".04", ".05", -2000)],
                       [quote("47000", ".08", ".09"), book()[1]]):
            self.assertIsNone(select_fixed_vertical(signal(), quotes))

    def test_invalid_source_never_revives_previous_favorable_quote(self):
        for quotes in (
            book() + [book()[0]],
            [replace(book()[0], arrival_ms=OPEN+1), book()[1]],
            [replace(book()[0], venue_ms=OPEN-400000,
                     arrival_ms=OPEN-399000), book()[1]],
            [replace(book()[0], symbol="ETH-04FEB22-45000-P"), book()[1]],
        ):
            with self.subTest(quotes=quotes):
                with self.assertRaises(ValueError):
                    select_fixed_vertical(signal(), quotes)

    def test_severe_and_supersevere_integrated_coin_cash_independent(self):
        for scenario in ("severe", "supersevere"):
            before = start_wallet("BTC", scenario, "100")
            after, decision = fixture_open_fixed_vertical(
                before, signal(), book(), name="one",
                initial_margin_coin="4", maintenance_margin_coin="2",
                fixture=True)
            self.assertEqual(decision["decision"], "MODELED_FIXTURE_OPEN_ONLY")
            proof = audit_fixture(signal(), book(), decision, before, after,
                                  initial_margin_coin="4",
                                  maintenance_margin_coin="2")
            self.assertEqual(proof["independent_fixture"],
                             "SELECTOR_FULL_STATE_AND_COIN_CASH_MATCH")
            self.assertFalse(proof["historical_economic_train"])
            self.assertEqual(len(after.positions), 1)

    def test_solvency_veto_is_cash_not_hidden_loss(self):
        before = start_wallet("BTC", "severe", "100")
        after, decision = fixture_open_fixed_vertical(
            before, signal(), book(), name="unsafe",
            initial_margin_coin="100", maintenance_margin_coin="100",
            fixture=True)
        self.assertEqual(after.last_ms, OPEN)
        self.assertEqual(replace(after, last_ms=before.last_ms), before)
        self.assertEqual(decision["decision"], "CASH_RISK_VETO")
        self.assertEqual(audit_fixture(signal(), book(), decision, before,
                                       after, initial_margin_coin="100",
                                       maintenance_margin_coin="100")["independent_fixture"],
                         "INDEPENDENT_RISK_CASH_VETO_MATCH")

    def test_no_historical_certification_by_caller_flags(self):
        with self.assertRaisesRegex(
                ValueError, "HISTORICAL_SOURCE_RECEIPTS_REQUIRE_INDEPENDENT_ATTESTATION"):
            fixture_open_fixed_vertical(
                start_wallet("BTC", "severe", "100"), signal(), book(),
                name="forbidden", initial_margin_coin="4",
                maintenance_margin_coin="2", fixture=False)

    def test_rejects_wrong_asset_and_sealed_date(self):
        with self.assertRaisesRegex(ValueError, "CROSS_COIN_COLLATERAL"):
            fixture_open_fixed_vertical(
                start_wallet("ETH", "severe", "100"), signal(), book(),
                name="bad", initial_margin_coin="4",
                maintenance_margin_coin="2", fixture=True)
        later = dict(signal())
        later["decision_ms"] = int(datetime(
            2023, 9, 25, tzinfo=timezone.utc).timestamp()*1000)
        later["fold"] = 5  # Correct frozen fold, so the right-censor gate is tested.
        with self.assertRaisesRegex(ValueError, "SEALED_OR_RIGHT_CENSORED"):
            select_fixed_vertical(later, [])


    def test_independent_oracle_rejects_forged_cash_with_eligible_pair(self):
        before = start_wallet("BTC", "severe", "100")
        fake = {"decision": "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL",
                "fixture": True, "economic_train_executed": False,
                "promotion_authorized": False}
        with self.assertRaisesRegex(AssertionError, "REFERENCE_FORGED_CASH_WITH_VALID_PAIR"):
            audit_fixture(signal(), book(), fake, before, replace(before, last_ms=OPEN))

    def test_independent_oracle_rejects_forged_risk_cash(self):
        before = start_wallet("BTC", "severe", "100")
        fake = {"decision": "CASH_RISK_VETO",
                "reason": "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO",
                "fixture": True, "economic_train_executed": False,
                "promotion_authorized": False}
        with self.assertRaisesRegex(AssertionError, "REFERENCE_UNJUSTIFIED_RISK_CASH"):
            audit_fixture(signal(), book(), fake, before, replace(before, last_ms=OPEN),
                          initial_margin_coin="4", maintenance_margin_coin="2")

    def test_independent_risk_cash_scenario_floors(self):
        for scenario, maintenance in (("severe", ".973"),
                                      ("supersevere", ".965")):
            before = start_wallet("BTC", scenario, "1")
            after, decision = fixture_open_fixed_vertical(
                before, signal(), book(), name="thin",
                initial_margin_coin=maintenance,
                maintenance_margin_coin=maintenance, fixture=True)
            self.assertEqual(after.last_ms, OPEN)
            self.assertEqual(replace(after, last_ms=before.last_ms), before)
            self.assertEqual(decision["reason"],
                             "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO")
            proof = audit_fixture(signal(), book(), decision, before, after,
                                  initial_margin_coin=maintenance,
                                  maintenance_margin_coin=maintenance)
            self.assertEqual(proof["independent_fixture"],
                             "INDEPENDENT_RISK_CASH_VETO_MATCH")

    def test_independent_oracle_rejects_stale_quote_even_if_open_claimed(self):
        before = start_wallet("BTC", "severe", "100")
        after, decision = fixture_open_fixed_vertical(
            before, signal(), book(), name="good",
            initial_margin_coin="4", maintenance_margin_coin="2", fixture=True)
        stale = [replace(book()[0], venue_ms=OPEN-400000,
                         arrival_ms=OPEN-399000), book()[1]]
        with self.assertRaisesRegex(AssertionError, "REFERENCE_STALE_OR_FUTURE"):
            audit_fixture(signal(), stale, decision, before, after)

    def test_independent_open_requires_explicit_margin_terms(self):
        before = start_wallet("BTC", "severe", "100")
        after, decision = fixture_open_fixed_vertical(
            before, signal(), book(), name="one",
            initial_margin_coin="4", maintenance_margin_coin="2", fixture=True)
        with self.assertRaisesRegex(AssertionError, "OPEN_MARGIN_TERMS_REQUIRED"):
            audit_fixture(signal(), book(), decision, before, after)

    def test_independent_open_rejects_forged_full_wallet_and_contract(self):
        before = start_wallet("BTC", "severe", "100")
        after, decision = fixture_open_fixed_vertical(
            before, signal(), book(), name="one",
            initial_margin_coin="4", maintenance_margin_coin="2", fixture=True)
        p = after.positions[0]
        tampered = (
            replace(after, positions=(replace(p, expiry_ms=p.expiry_ms+86400000),)),
            replace(after, positions=(replace(p, high=Decimal("44999")),)),
            replace(after, positions=(replace(p, low=Decimal("39999")),)),
            replace(after, positions=(replace(p, maintenance_margin_coin=Decimal("3")),)),
            replace(after, positions=(replace(p, qty=Decimal("2")),)),
            replace(after, last_ms=OPEN-1),
            replace(after, initial_coin=Decimal("101")),
            replace(after, settled=("forged",)),
            replace(after, marks=(("one", Decimal("0.01"), OPEN, Decimal("50000")),)),
            replace(after, reserved_coin=Decimal("5")),
            replace(after, cash_coin=Decimal("1")),
        )
        for forged in tampered:
            with self.subTest(forged=forged):
                with self.assertRaises(AssertionError):
                    audit_fixture(signal(), book(), decision, before, forged,
                                  initial_margin_coin="4",
                                  maintenance_margin_coin="2")
        with self.assertRaisesRegex(AssertionError, "REFERENCE_UNVERIFIED_MARGIN_TERMS"):
            audit_fixture(signal(), book(), decision, before, after,
                          initial_margin_coin="4", maintenance_margin_coin="3")

    def test_forged_chronological_fold_fails_primary_and_independent(self):
        forged = dict(signal())
        forged["fold"] = 2  # January 2022 belongs to frozen fold 1.
        with self.assertRaisesRegex(ValueError, "SIGNAL_FOLD_TIME_MISMATCH"):
            select_fixed_vertical(forged, book())
        before = start_wallet("BTC", "severe", "100")
        fake_cash = {"decision": "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL",
                     "fixture": True, "economic_train_executed": False,
                     "promotion_authorized": False}
        with self.assertRaisesRegex(AssertionError, "REFERENCE_SIGNAL_FOLD_TIME_MISMATCH"):
            audit_fixture(forged, book(), fake_cash, before, before)
        valid_later = dict(signal("NO_PREMIUM"))
        valid_later["decision_ms"] = int(datetime(2022, 5, 2, tzinfo=timezone.utc).timestamp()*1000)
        valid_later["fold"] = 2
        self.assertIsNone(select_fixed_vertical(valid_later, []))

    def test_invalid_cash_wallet_rejected_even_without_eligible_signal(self):
        for changed in (
            {"cash_coin": Decimal("-1")},
            {"reserved_coin": Decimal("101")},
            {"initial_coin": Decimal("0")},
            {"reserved_coin": Decimal("1")},
        ):
            before = replace(start_wallet("BTC", "severe", "100"), **changed)
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    fixture_open_fixed_vertical(
                        before, signal("NO_PREMIUM"), [], name="none",
                        initial_margin_coin="4", maintenance_margin_coin="2",
                        fixture=True)
                fake_cash = {"decision": "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL",
                             "fixture": True, "economic_train_executed": False,
                             "promotion_authorized": False}
                with self.assertRaisesRegex(AssertionError, "REFERENCE_INVALID_BEFORE_WALLET"):
                    audit_fixture(signal("NO_PREMIUM"), [], fake_cash, before, before)

    def test_cash_clock_requires_marks_of_every_live_position(self):
        next_monday = OPEN + 7 * 86_400_000
        later = dict(signal("NO_PREMIUM"))
        later["decision_ms"] = next_monday
        fake_cash = {"decision": "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL",
                     "fixture": True, "economic_train_executed": False,
                     "promotion_authorized": False}
        for scenario in ("severe", "supersevere"):
            initial = start_wallet("BTC", scenario, "100")
            opened, _ = fixture_open_fixed_vertical(
                initial, signal(), book(), name="one",
                initial_margin_coin="4", maintenance_margin_coin="2",
                fixture=True)
            with self.subTest(scenario=scenario):
                with self.assertRaisesRegex(ValueError, "PREDECISION_ALL_POSITION_MARKS_REQUIRED"):
                    fixture_open_fixed_vertical(
                        opened, later, [], name="none",
                        initial_margin_coin="4", maintenance_margin_coin="2",
                        fixture=True)
                with self.assertRaisesRegex(AssertionError, "REFERENCE_UNMARKED_OPEN_WALLET"):
                    audit_fixture(later, [], fake_cash, opened, opened)
                short, long = [quote("45000", ".08", ".09", 7*86_400_000),
                               quote("40000", ".04", ".05", 7*86_400_000)]
                fee, slip = charge_floor(scenario, Decimal("1"))
                marked = costed_mark(opened, "one", short, long, next_monday,
                                     fee, slip, fixture=True)
                after, decision = fixture_open_fixed_vertical(
                    marked, later, [], name="none",
                    initial_margin_coin="4", maintenance_margin_coin="2",
                    fixture=True)
                self.assertEqual(after, marked)
                self.assertEqual(audit_fixture(later, [], decision, marked, after)[
                    "independent_fixture"], "CASH_MATCH")
                bad = replace(marked, marks=tuple(
                    (name, liability, next_monday-1, index)
                    for name, liability, _, index in marked.marks))
                with self.assertRaisesRegex(ValueError, "PREDECISION_ALL_POSITION_MARKS_REQUIRED"):
                    fixture_open_fixed_vertical(
                        bad, later, [], name="none",
                        initial_margin_coin="4", maintenance_margin_coin="2",
                        fixture=True)
                with self.assertRaisesRegex(AssertionError, "REFERENCE_STALE_OPEN_MARK"):
                    audit_fixture(later, [], fake_cash, bad, bad)

    def test_cash_decision_cannot_reverse_wallet_clock(self):
        before = replace(start_wallet("BTC", "severe", "100"), last_ms=OPEN+1)
        with self.assertRaisesRegex(ValueError, "DECISION_TIME_REVERSAL"):
            fixture_open_fixed_vertical(
                before, signal("NO_PREMIUM"), [], name="none",
                initial_margin_coin="4", maintenance_margin_coin="2",
                fixture=True)
        fake_cash = {"decision": "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL",
                     "fixture": True, "economic_train_executed": False,
                     "promotion_authorized": False}
        with self.assertRaisesRegex(AssertionError, "REFERENCE_DECISION_TIME_REVERSAL"):
            audit_fixture(signal("NO_PREMIUM"), [], fake_cash, before, before)


    def test_cash_no_trade_advances_clock_and_blocks_backdated_replay(self):
        later = dict(signal("NO_PREMIUM"))
        later["decision_ms"] = OPEN + 7 * 86_400_000
        for scenario in ("severe", "supersevere"):
            before = start_wallet("BTC", scenario, "100")
            after, decision = fixture_open_fixed_vertical(
                before, later, [], name="none",
                initial_margin_coin="4", maintenance_margin_coin="2",
                fixture=True)
            self.assertEqual(after.last_ms, later["decision_ms"])
            self.assertEqual(replace(after, last_ms=before.last_ms), before)
            self.assertEqual(audit_fixture(later, [], decision, before, after)[
                "independent_fixture"], "CASH_MATCH")
            with self.assertRaisesRegex(ValueError, "DECISION_TIME_REVERSAL"):
                fixture_open_fixed_vertical(
                    after, signal("NO_PREMIUM"), [], name="backdated",
                    initial_margin_coin="4", maintenance_margin_coin="2",
                    fixture=True)
            with self.assertRaisesRegex(AssertionError, "REFERENCE_CASH_CLOCK_NOT_ADVANCED"):
                audit_fixture(later, [], decision, before, before)

    def test_overlapping_index_mismatch_is_independently_vetoed_cash(self):
        # Existing position is marked at the new Monday, but the next two-leg
        # original-index snapshot differs. Do not silently net two indices.
        next_monday = OPEN + 7 * 86_400_000
        later = dict(signal())
        later["decision_ms"] = next_monday
        for scenario in ("severe", "supersevere"):
            with self.subTest(scenario=scenario):
                before = start_wallet("BTC", scenario, "100")
                opened, _ = fixture_open_fixed_vertical(
                    before, signal(), book(), name="first",
                    initial_margin_coin="4", maintenance_margin_coin="2",
                    fixture=True)
                old_index_book = [quote("45000", ".08", ".09", 7*86_400_000),
                                  quote("40000", ".04", ".05", 7*86_400_000)]
                fee, slip = charge_floor(scenario, Decimal("1"))
                marked = costed_mark(opened, "first", *old_index_book,
                                     next_monday, fee, slip, fixture=True)
                # The existing Feb-04 expiry is now only 25 days away;
                # a NEW entry must use a fresh 28-35d expiry (Feb-11).
                new_expiry = int(datetime(2022, 2, 11, 8,
                                          tzinfo=timezone.utc).timestamp()*1000)
                new_index_book = [replace(
                    q, symbol=q.symbol.replace("04FEB22", "11FEB22"),
                    expiry_ms=new_expiry, index_usd=Decimal("50001"))
                    for q in old_index_book]
                after, decision = fixture_open_fixed_vertical(
                    marked, later, new_index_book, name="second",
                    initial_margin_coin="4", maintenance_margin_coin="2",
                    fixture=True)
                self.assertEqual(decision["decision"], "CASH_RISK_VETO")
                self.assertEqual(decision["reason"], "POSTENTRY_UNBOUND_UNDERLYING_INDEX")
                self.assertEqual(after, marked)
                self.assertEqual(audit_fixture(
                    later, new_index_book, decision, marked, after,
                    initial_margin_coin="4", maintenance_margin_coin="2")[
                    "independent_fixture"],
                    "INDEPENDENT_OVERLAP_INDEX_RISK_CASH_VETO_MATCH")
                # A forged index veto must fail if the original marks and new
                # quotes actually share the same index.
                with self.assertRaisesRegex(
                        AssertionError, "REFERENCE_FORGED_INDEX_MISMATCH_VETO"):
                    audit_fixture(later, [replace(q, index_usd=Decimal("50000"))
                                          for q in new_index_book],
                                  decision, marked, after,
                                  initial_margin_coin="4",
                                  maintenance_margin_coin="2")
                # And an empty portfolio cannot justify this overlap veto.
                empty = replace(before, last_ms=next_monday)
                with self.assertRaisesRegex(
                        AssertionError, "REFERENCE_NO_OVERLAPPING_POSITION"):
                    audit_fixture(later, new_index_book, decision, empty, empty,
                                  initial_margin_coin="4",
                                  maintenance_margin_coin="2")

    def test_no_promotion_or_roi_fields(self):
        before = start_wallet("BTC", "severe", "100")
        _, decision = fixture_open_fixed_vertical(
            before, signal(), book(), name="one",
            initial_margin_coin="4", maintenance_margin_coin="2",
            fixture=True)
        self.assertEqual(decision["promotion_authorized"], False)
        self.assertEqual(decision["economic_train_executed"], False)
        self.assertNotIn("roi", decision)
        self.assertNotIn("pnl", decision)


if __name__ == "__main__":
    unittest.main()
