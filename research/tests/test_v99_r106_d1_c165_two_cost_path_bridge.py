"""C165 216h synthetic two-scenario warmup + independently re-executed ledger.

NO actual exchange receipts, ROI, paper, order submission or sealed data.
"""
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision
from research.tools.v99_r106_d1_c140_hourly_journal import build_journal
from research.verification.independent_d1_c165_two_cost_path_bridge import (
    verify_two_cost_path_bridge,
)

START = datetime(2023, 9, 20, tzinfo=timezone.utc)
HOURS = 216
SCENARIOS = ("severe_model_only", "supersevere_model_only")
ASSETS = ("BTC", "ETH")


def synthetic_inputs():
    rows = []
    funding_times = {a: [] for a in ASSETS}
    for i in range(HOURS):
        t = START + timedelta(hours=i)
        b = Decimal(i)
        marks = {
            "BTC": {"spot": str(Decimal("100") + b / 1000),
                    "perp": str(Decimal("101") + b / 1000)},
            "ETH": {"spot": str(Decimal("50") + b / 2000),
                    "perp": str(Decimal("51") + b / 2000)},
        }
        funding = []
        if t.hour in (0, 8, 16):
            for a in ASSETS:
                funding_times[a].append(t)
                funding.append({"asset": a, "time": t, "rate": "0.0002",
                                "source": "OKX", "instrument": a + "-USDT-SWAP"})
        rows.append({"time": t, "marks": marks, "funding": funding})
    decisions = {}
    for i in (168, 192):
        t = START + timedelta(hours=i)
        decisions[t] = Decision(
            t, 0.20, 0.20 if i == 168 else 0.0,
            "SIDEWAYS__LOW_VOLATILITY", t - timedelta(hours=1),
            t - timedelta(hours=1), "C136_FEE_VETO_MODEL_ONLY_NO_ROI",
        )
    native_fee_schedule = {
        a: [{
            "start": datetime(2021, 12, 9, tzinfo=timezone.utc),
            "end": datetime(2023, 10, 1, tzinfo=timezone.utc),
            "spot_taker": "0.001", "perp_taker": "0.0005",
            "spot_fee_currency": "BASE" if a == "BTC" else "QUOTE",
            "account_tier": "SYNTHETIC_NOT_AUTHENTICATED",
            "observed_at": datetime(2021, 12, 8, tzinfo=timezone.utc),
        }] for a in ASSETS
    }
    return {
        "rows": rows,
        "initial_state": {"cash_quote": "1000",
                          "spot_base": {a: "0" for a in ASSETS},
                          "perp_base": {a: "0" for a in ASSETS}},
        "initial_marks": {"BTC": {"spot": "100", "perp": "101"},
                          "ETH": {"spot": "50", "perp": "51"}},
        "initial_marks_time": START - timedelta(hours=1),
        "native_fee_schedule": native_fee_schedule,
        "decisions": decisions,
        "expected_funding_schedule": funding_times,
    }


def build_case():
    inp = synthetic_inputs()
    journals = {
        s: build_journal(scenario=s, **deepcopy(inp)) for s in SCENARIOS
    }
    decisions_by_scenario = {s: deepcopy(inp["decisions"]) for s in SCENARIOS}
    return {
        "journals": journals,
        "decisions_by_scenario": decisions_by_scenario,
        "initial_marks": deepcopy(inp["initial_marks"]),
        "initial_marks_time": inp["initial_marks_time"],
    }


class C165IndependentBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = build_case()

    def fresh(self):
        return deepcopy(self.fixture)

    def test_216h_both_paths_168h_flat_and_independent_accounting(self):
        p = verify_two_cost_path_bridge(**self.fresh())
        self.assertEqual(p["hours_per_scenario"], 216)
        self.assertEqual(p["warmup_hours"], 168)
        self.assertEqual(p["decision_hours"], 2)
        for s in SCENARIOS:
            self.assertEqual(p["scenario_results"][s]["hours_independently_replayed"], 216)
            self.assertEqual(p["scenario_results"][s]["modeled_funding_events"], 54)
            self.assertGreater(p["scenario_results"][s]["modeled_fills"], 0)
            self.assertEqual(p["scenario_results"][s]["max_accounting_residual"], "0")
        for k in ("first_party_okx_authenticated",
                  "native_lot_and_fee_tier_authenticated",
                  "settled_funding_and_fills_authenticated",
                  "historical_economics_authorized", "validation_opened",
                  "holdout_opened", "promotion_authorized", "orders_enabled"):
            self.assertIs(p[k], False)

    def test_initial_capital_tamper_rejected(self):
        x = self.fresh()
        x["journals"][SCENARIOS[1]]["frames"][0]["before"]["cash_quote"] = "1001"
        with self.assertRaises(ValueError):
            verify_two_cost_path_bridge(**x)

    def test_cost_path_price_divergence_rejected(self):
        x = self.fresh()
        x["journals"][SCENARIOS[1]]["frames"][20]["marks"]["BTC"]["spot"] = "900"
        with self.assertRaisesRegex(ValueError, "EXOGENOUS"):
            verify_two_cost_path_bridge(**x)

    def test_cost_path_funding_divergence_rejected(self):
        x = self.fresh()
        x["journals"][SCENARIOS[1]]["frames"][8]["funding"][0]["rate"] = "0.5"
        with self.assertRaisesRegex(ValueError, "EXOGENOUS"):
            verify_two_cost_path_bridge(**x)

    def test_warmup_trade_rejected(self):
        x = self.fresh()
        x["journals"][SCENARIOS[0]]["frames"][100]["fills"].append({"fake": True})
        with self.assertRaisesRegex(ValueError, "PREDECISION"):
            verify_two_cost_path_bridge(**x)

    def test_accounting_mutation_rejected_independently(self):
        x = self.fresh()
        x["journals"][SCENARIOS[0]]["frames"][170]["after_mark"]["cash_quote"] = "99999"
        with self.assertRaisesRegex(ValueError, "C149_"):
            verify_two_cost_path_bridge(**x)

    def test_missing_cost_path_rejected(self):
        x = self.fresh()
        del x["journals"][SCENARIOS[1]]
        with self.assertRaisesRegex(ValueError, "TWO_COST_PATHS"):
            verify_two_cost_path_bridge(**x)

    def test_missing_decision_rejected(self):
        x = self.fresh()
        x["decisions_by_scenario"][SCENARIOS[1]].pop(START + timedelta(hours=168))
        with self.assertRaisesRegex(ValueError, "DECISION_GRID"):
            verify_two_cost_path_bridge(**x)

    def test_future_market_partition_rejected(self):
        x = self.fresh()
        x["initial_marks_time"] = datetime(2023, 9, 27, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "SEALED"):
            verify_two_cost_path_bridge(**x)

    def test_claimed_economics_permission_rejected(self):
        x = self.fresh()
        x["journals"][SCENARIOS[0]]["economic_roi_authorized"] = True
        with self.assertRaisesRegex(ValueError, "FALSE_ECONOMIC_PERMISSION"):
            verify_two_cost_path_bridge(**x)


if __name__ == "__main__":
    unittest.main()
