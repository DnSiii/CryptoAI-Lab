"""No historical ROI: cost floor + native wallet + independent arithmetic."""
import unittest
from datetime import datetime, timezone

from research.tools.v99_r106_i1_native_coin_account_replay import (
    D, Quote, start_wallet, account_nav,
)
from research.tools.v99_r106_i1_cost_bound_execution import (
    charge_floor, costed_open, costed_mark, verify_charges,
)
from research.verification.independent_v99_r106_i1_cost_bound_oracle import audit_open, audit_postentry


def ms(s):
    return int(datetime.fromisoformat(s).timestamp()*1000)


AT = ms("2022-01-03T00:00:00+00:00")
MARK = ms("2022-01-10T00:00:00+00:00")
EXP = ms("2022-02-04T08:00:00+00:00")


def q(strike, bid, ask, at):
    return Quote("BTC", f"BTC-04FEB22-{strike}-P", EXP, D(strike),
                 D(bid), D(ask), D("10"), D("10"),
                 at-2000, at-1000, D("46000"))


class CostBindingTests(unittest.TestCase):
    def test_two_scenarios_wallet_and_independent_oracle(self):
        for scenario in ("severe", "supersevere"):
            with self.subTest(scenario=scenario):
                w = start_wallet("BTC", scenario, "100")
                s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
                fee, slip = charge_floor(scenario, "1")
                w = costed_open(w, "p1", s, l, AT, "1", fee, slip,
                                "4", "2", fixture=True)
                journal = dict(fixture=True, historical_economic_train=False,
                    scenario=scenario, qty="1", initial_coin="100",
                    short_bid_coin=".08", long_ask_coin=".05",
                    entry_fee_coin=str(fee), entry_slippage_coin=str(slip))
                proof = audit_open(journal, w.cash_coin)
                self.assertEqual(proof["independent_cost_binding"], "MATCH")
                self.assertFalse(proof["promotion_authorized"])
                sm, lm = q("50000",".08",".09",MARK), q("45000",".04",".05",MARK)
                w = costed_mark(w, "p1", sm, lm, MARK, fee, slip, fixture=True)
                nav = account_nav(w, MARK)
                self.assertFalse(nav["historical_economic_train"])
                self.assertLess(D(nav["nav_coin"]), D("100"))

    def test_zero_fee_and_wrong_scenario_fails(self):
        for scenario in ("severe", "supersevere"):
            w = start_wallet("BTC", scenario, "100")
            s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
            fee, slip = charge_floor(scenario, "1")
            for f, sl in (("0", slip), (fee, "0")):
                with self.assertRaisesRegex(ValueError, "FRICTION_UNDERPAYMENT"):
                    costed_open(w, "p", s, l, AT, "1", f, sl, "4", "2", fixture=True)
            with self.assertRaisesRegex(AssertionError, "REFERENCE_SCENARIO_FRICTION_UNDERPAYMENT"):
                audit_open(dict(fixture=True, historical_economic_train=False,
                    scenario=scenario, qty="1", initial_coin="100",
                    short_bid_coin=".08", long_ask_coin=".05",
                    entry_fee_coin="0", entry_slippage_coin=str(slip)), "100.03")

    def test_nonfixture_refuses_even_boolean_claims(self):
        w = start_wallet("BTC", "severe", "100")
        s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
        fee, slip = charge_floor("severe", "1")
        with self.assertRaisesRegex(ValueError, "REQUIRE_INDEPENDENT_ATTESTATION"):
            costed_open(w,"p",s,l,AT,"1",fee,slip,"4","2")
        with self.assertRaisesRegex(ValueError, "REQUIRE_INDEPENDENT_ATTESTATION"):
            costed_open(w,"p",s,l,AT,"1",fee,slip,"4","2",
                        original_fee_verified=True, native_contract_verified=True,
                        margin_rules_verified=True, original_quote_verified=True)
        with self.assertRaisesRegex(ValueError, "FIXTURE_CANNOT_CLAIM"):
            costed_open(w,"p",s,l,AT,"1",fee,slip,"4","2",
                        fixture=True, original_fee_verified=True)

    def test_bad_numbers_and_scenario(self):
        for qty in ("0", "-1", "NaN", True):
            with self.assertRaises(ValueError):
                charge_floor("severe", qty)
        with self.assertRaisesRegex(ValueError, "UNKNOWN_COST_SCENARIO"):
            verify_charges("unknown", "1", "1", "1")

    def test_mark_cannot_erase_stressed_exit_fees(self):
        w = start_wallet("BTC", "supersevere", "100")
        s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
        fee, slip = charge_floor("supersevere", "1")
        w = costed_open(w, "p", s, l, AT, "1", fee, slip, "4", "2", fixture=True)
        sm, lm = q("50000",".08",".09",MARK), q("45000",".04",".05",MARK)
        with self.assertRaisesRegex(ValueError, "FRICTION_UNDERPAYMENT"):
            costed_mark(w, "p", sm, lm, MARK, "0", slip, fixture=True)
        with self.assertRaisesRegex(ValueError, "FRICTION_UNDERPAYMENT"):
            costed_mark(w, "p", sm, lm, MARK, fee, "0", fixture=True)


    def test_postentry_scenario_exit_cost_veto_and_independent_oracle(self):
        # The underlying wallet's weak check would pass at these margins.
        # The severe/supersevere *closing* fee+slippage makes NAV insolvent.
        for scenario, maintenance in (("severe", ".973"), ("supersevere", ".965")):
            with self.subTest(scenario=scenario):
                w = start_wallet("BTC", scenario, "1")
                s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
                fee, slip = charge_floor(scenario, "1")
                cash = D("1") + D(".03") - fee - slip
                weak_nav = cash - D(".05")
                self.assertGreaterEqual(weak_nav, D(maintenance))
                journal = dict(fixture=True, historical_economic_train=False,
                    scenario=scenario, qty="1", cash_after_open_coin=str(cash),
                    short_ask_coin=".09", long_bid_coin=".04",
                    existing_exit_liabilities_coin="0",
                    total_maintenance_coin=maintenance)
                with self.assertRaisesRegex(AssertionError, "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO"):
                    audit_postentry(journal)
                with self.assertRaisesRegex(ValueError, "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO"):
                    costed_open(w, "p", s, l, AT, "1", fee, slip,
                                maintenance, maintenance, fixture=True)
                # An adequately capitalized wallet still passes independently.
                healthy = dict(journal, cash_after_open_coin=str(cash + D("1")))
                self.assertEqual(audit_postentry(healthy)["independent_postentry_solvency"], "PASS")

    def test_full_mark_immediate_maintenance_veto(self):
        w = start_wallet("BTC", "severe", "1")
        s, l = q("50000", ".08", ".09", AT), q("45000", ".04", ".05", AT)
        fee, slip = charge_floor("severe", "1")
        w = costed_open(w, "p", s, l, AT, "1", fee, slip, ".96", ".96", fixture=True)
        sm = q("50000", ".19", ".20", MARK)
        lm = q("45000", ".01", ".02", MARK)
        with self.assertRaisesRegex(ValueError, "MAINTENANCE_BREACH_REQUIRES_AUTHENTICATED_LIQUIDATION_MODEL"):
            costed_mark(w, "p", sm, lm, MARK, fee, slip, fixture=True)



if __name__ == "__main__":
    unittest.main()
