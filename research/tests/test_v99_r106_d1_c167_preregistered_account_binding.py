"""C167 adversarial end-to-end synthetic D1 decision -> native fees -> ledger.

Funding at 0.3% per 8h is deliberately ARTIFICIAL to exercise a nonzero
trade; never infer exchange economics, ROI, or historical alpha.
"""
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research.tools.v99_r106_d1_basis_carry_preregistered import (
    PairedBar, FundingFix, FeeEvidence, Decision,
)
from research.tools.v99_r106_d1_native_fee_veto_cycle136 import (
    CausalFeeTier, fee_bound_intent,
)
from research.tools.v99_r106_d1_c140_hourly_journal import build_journal
from research.verification.independent_d1_c167_preregistered_account_binding import (
    verify_c167_preregistered_account_binding,
)

START = datetime(2023, 9, 20, tzinfo=timezone.utc)
END = datetime(2023, 10, 1, tzinfo=timezone.utc)
SCENARIOS = ("severe_model_only", "supersevere_model_only")
ASSETS = ("BTC", "ETH")


def fixture():
    rows, schedule, bars, fixes = [], {a: [] for a in ASSETS}, {a: [] for a in ASSETS}, {a: [] for a in ASSETS}
    for i in range(216):
        t = START + timedelta(hours=i)
        marks = {
            "BTC": {"spot": str(Decimal("100") + Decimal(i)/1000),
                    "perp": str(Decimal("100.1") + Decimal(i)/1000)},
            "ETH": {"spot": str(Decimal("50") + Decimal(i)/2000),
                    "perp": str(Decimal("50.1") + Decimal(i)/2000)},
        }
        funding = []
        for a in ASSETS:
            bars[a].append(PairedBar(t, a, float(marks[a]["spot"]),
                                     float(marks[a]["perp"]), "OKX", "OKX", t))
            if t.hour in (0, 8, 16):
                rate = "0.003" if i < 176 else "-0.0001"
                funding.append({"asset": a, "time": t, "rate": rate,
                                "source": "OKX", "instrument": a + "-USDT-SWAP"})
                fixes[a].append(FundingFix(a, t, t, float(rate),
                                            "OKX", a + "-USDT-SWAP"))
                schedule[a].append(t)
        rows.append({"time": t, "marks": marks, "funding": funding})
    fee_schedule = {a: [{
        "start": datetime(2021, 12, 9, tzinfo=timezone.utc),
        "end": END, "spot_taker": "0.0002", "perp_taker": "0.0002",
        "spot_fee_currency": "QUOTE", "account_tier": "SYNTHETIC_ONLY",
        "observed_at": datetime(2021, 12, 8, tzinfo=timezone.utc),
    }] for a in ASSETS}
    evidence, decisions = {}, {s: {} for s in SCENARIOS}
    for i in (168, 192):
        t = rows[i]["time"]
        tiers = {a: CausalFeeTier(FeeEvidence(
            "OKX", 0.0002, 0.0002,
            fee_schedule[a][0]["start"], fee_schedule[a][0]["end"],
            "SYNTHETIC_ONLY",
        ), fee_schedule[a][0]["observed_at"]) for a in ASSETS}
        evidence[t] = {
            "bars": {a: bars[a][i-168:i] for a in ASSETS},
            "funding": {a: [f for f in fixes[a] if f.settled_at < t][-3:]
                        for a in ASSETS},
            "fee_tiers": tiers,
        }
        for scenario in SCENARIOS:
            decisions[scenario][t] = fee_bound_intent(
                time=t, scenario=scenario, **evidence[t],
            )["decision"]
    initial_marks = {"BTC": {"spot": "100", "perp": "100.1"},
                     "ETH": {"spot": "50", "perp": "50.1"}}
    initial_state = {"cash_quote": "1000",
                     "spot_base": {a: "0" for a in ASSETS},
                     "perp_base": {a: "0" for a in ASSETS}}
    journals = {
        s: build_journal(
            scenario=s, rows=deepcopy(rows), initial_state=deepcopy(initial_state),
            initial_marks=deepcopy(initial_marks),
            initial_marks_time=START-timedelta(hours=1),
            native_fee_schedule=deepcopy(fee_schedule),
            decisions=deepcopy(decisions[s]),
            expected_funding_schedule=deepcopy(schedule),
        ) for s in SCENARIOS
    }
    return {
        "journals": journals, "decisions_by_scenario": decisions,
        "evidence_by_decision": evidence, "native_fee_schedule": fee_schedule,
        "initial_marks": initial_marks,
        "initial_marks_time": START-timedelta(hours=1),
    }


class C167CompleteDecisionToAccount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = fixture()

    def fresh(self):
        return deepcopy(self.good)

    def test_original_exante_decisions_and_two_accounts_replayed(self):
        result = verify_c167_preregistered_account_binding(**self.fresh())
        self.assertEqual(result["daily_decision_hours"], 2)
        self.assertEqual(result["scenario_decisions_recomputed"], 4)
        self.assertEqual(result["feature_asset_hours_verified"], 672)
        self.assertEqual(result["historical_funding_fix_identities_verified"], 12)
        self.assertEqual(result["positive_pair_decisions_by_scenario_synthetic"]["severe_model_only"], 2)
        self.assertEqual(result["positive_pair_decisions_by_scenario_synthetic"]["supersevere_model_only"], 0)
        self.assertEqual(result["independent_c165_account_replay"]["hours_per_scenario"], 216)
        self.assertFalse(result["historical_economics_authorized"])

    def test_posthoc_cash_override_rejected_even_if_journal_consistent(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        old = x["decisions_by_scenario"][SCENARIOS[0]][t]
        x["decisions_by_scenario"][SCENARIOS[0]][t] = Decision(
            t, 0, 0, old.regime, old.feature_max_time,
            old.funding_asof, old.status)
        with self.assertRaisesRegex(ValueError, "POSTHOC"):
            verify_c167_preregistered_account_binding(**x)

    def test_forged_early_open_rejected(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        bar = x["evidence_by_decision"][t]["bars"]["BTC"][0]
        x["evidence_by_decision"][t]["bars"]["BTC"][0] = PairedBar(
            bar.time, "BTC", bar.spot_open + 1, bar.perp_open,
            "OKX", "OKX", bar.time)
        with self.assertRaisesRegex(ValueError, "FEATURE_MARK"):
            verify_c167_preregistered_account_binding(**x)

    def test_forged_settled_funding_rejected(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        old = x["evidence_by_decision"][t]["funding"]["ETH"][-1]
        x["evidence_by_decision"][t]["funding"]["ETH"][-1] = FundingFix(
            "ETH", old.announced_at, old.settled_at, .002,
            "OKX", old.instrument)
        with self.assertRaisesRegex(ValueError, "FUNDING_FIX_IDENTITY"):
            verify_c167_preregistered_account_binding(**x)

    def test_fee_tier_drift_rejected(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        old = x["evidence_by_decision"][t]["fee_tiers"]["BTC"]
        fee = old.evidence
        x["evidence_by_decision"][t]["fee_tiers"]["BTC"] = CausalFeeTier(
            FeeEvidence("OKX", .0003, fee.perp_taker, fee.valid_from,
                        fee.valid_until, fee.tier_reference),
            old.observed_at)
        with self.assertRaisesRegex(ValueError, "NATIVE_TIER_JOURNAL"):
            verify_c167_preregistered_account_binding(**x)

    def test_missing_decision_day_rejected(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        del x["evidence_by_decision"][t]
        with self.assertRaisesRegex(ValueError, "EXACT_DAILY_DECISION_GRID"):
            verify_c167_preregistered_account_binding(**x)

    def test_scenario_fee_veto_incorrectly_overridden_rejected(self):
        x = self.fresh()
        t = min(x["evidence_by_decision"])
        good = x["decisions_by_scenario"][SCENARIOS[0]][t]
        x["decisions_by_scenario"][SCENARIOS[1]][t] = good
        with self.assertRaisesRegex(ValueError, "POSTHOC"):
            verify_c167_preregistered_account_binding(**x)

    def test_ledger_mutation_still_rejected_by_independent_replay(self):
        x = self.fresh()
        x["journals"][SCENARIOS[0]]["frames"][200]["after_mark"]["cash_quote"] = "99999"
        with self.assertRaises(ValueError):
            verify_c167_preregistered_account_binding(**x)


if __name__ == "__main__":
    unittest.main()
