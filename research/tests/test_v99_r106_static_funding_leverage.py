"""Adversarial non-PnL leverage budget tests. Synthetic values never used as economics."""
import copy
import unittest

from research.tools.v99_r106_static_funding_leverage_feasibility import evaluate


def synthetic():
    folds = []
    for i in range(5):
        g = 0.01 if i != 2 else -0.001
        folds.append({
            "fold": i+1, "events_per_asset": 397 if i in (0,1,3) else 396,
            "btc_signed_rate_sum": g, "eth_signed_rate_sum": g,
            "static_50_50_signed_funding_rate_budget_NOT_ROI": g,
            "illustrative_budget_minus_four_side_cost_NOT_ROI": {
                "severe": g-.0028, "supersevere": g-.0056},
        })
    p = {
        "original_archives":44,"original_events_per_asset":1983,
        "folds":folds,"positive_budget_folds":{"severe":4,"supersevere":4},
        "rate_budget_is_not_nav_or_roi":True,
        "public_funding_is_not_account_settlement":True,
        "economic_train_executed":False,"promotion_authorized":False,
        "validation_opened":False,"holdout_opened":False,"orders_enabled":False,
        "paper_modified":False,"frozen_modified":False,
    }
    o = {
        "status":"INDEPENDENT_44_ORIGINAL_PUBLISHER_ZIPS_FIVEFOLD_BUDGET_REEXECUTED",
        "original_files":44,"events_per_asset":1983,
        "fold_signed_rate_budgets_NOT_ROI":[f["static_50_50_signed_funding_rate_budget_NOT_ROI"] for f in folds],
    }
    return p,o


class Tests(unittest.TestCase):
    def test_synthetic_source_only_sensitivity(self):
        p,o=synthetic()
        r=evaluate(p,o)
        self.assertFalse(r["economic_train_executed"])
        self.assertFalse(r["promotion_authorized"])
        self.assertGreater(float(r["scenarios"]["supersevere"]["illustrative_notional_to_initial_equity_multiple_NOT_NAV"]), 1)
        self.assertLess(float(r["scenarios"]["supersevere"]["weakest_fold_at_illustrative_multiple_NOT_NAV"]), 0)

    def test_reject_source_oracle_disagreement(self):
        p,o=synthetic()
        o["fold_signed_rate_budgets_NOT_ROI"][1]+=0.001
        with self.assertRaisesRegex(ValueError,"INDEPENDENT_ORIGINAL_FOLD_MISMATCH"):
            evaluate(p,o)

    def test_reject_promotion_claim(self):
        p,o=synthetic()
        p["promotion_authorized"]=True
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_OR_UNSAFE_ORIGINAL_SOURCE"):
            evaluate(p,o)

    def test_reject_cost_tamper(self):
        p,o=synthetic()
        p["folds"][0]["illustrative_budget_minus_four_side_cost_NOT_ROI"]["severe"]=0.3
        with self.assertRaisesRegex(ValueError,"ORIGINAL_COST_BUDGET_MISMATCH"):
            evaluate(p,o)

    def test_reject_fold_omission(self):
        p,o=synthetic()
        p["folds"].pop()
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_OR_UNSAFE_ORIGINAL_SOURCE"):
            evaluate(p,o)

    def test_reject_false_positive_folds(self):
        p,o=synthetic()
        p["positive_budget_folds"]["severe"]=5
        with self.assertRaisesRegex(ValueError,"FIVEFOLD_SOURCE_STATUS_MISMATCH"):
            evaluate(p,o)


if __name__ == "__main__":
    unittest.main()
