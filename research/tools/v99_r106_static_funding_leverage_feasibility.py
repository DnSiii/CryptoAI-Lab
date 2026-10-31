"""Preregistered first-order static funding notional/risk feasibility. NOT ROI or strategy."""
from __future__ import annotations
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

COST = {"severe": Decimal("0.0028"), "supersevere": Decimal("0.0056")}
TARGET = Decimal("1")
DD_BUDGET = Decimal("0.35")
SCHEMA = "V99_STATIC_FUNDING_NOTIONAL_RISK_SOURCE_ONLY_V1"


def decimal(value):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_RATE")
    try:
        v = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise ValueError("INVALID_RATE") from exc
    if not v.is_finite():
        raise ValueError("NONFINITE_RATE")
    return v


def evaluate(primary, source_oracle):
    if (primary.get("original_archives") != 44 or
        primary.get("original_events_per_asset") != 1983 or
        len(primary.get("folds", [])) != 5 or
        source_oracle.get("status") !=
            "INDEPENDENT_44_ORIGINAL_PUBLISHER_ZIPS_FIVEFOLD_BUDGET_REEXECUTED" or
        source_oracle.get("original_files") != 44 or
        source_oracle.get("events_per_asset") != 1983 or
        len(source_oracle.get("fold_signed_rate_budgets_NOT_ROI", [])) != 5 or
        primary.get("rate_budget_is_not_nav_or_roi") is not True or
        primary.get("public_funding_is_not_account_settlement") is not True or
        any(primary.get(k) is not False for k in (
            "economic_train_executed", "promotion_authorized",
            "validation_opened", "holdout_opened", "orders_enabled",
            "paper_modified", "frozen_modified"))):
        raise ValueError("UNVERIFIED_OR_UNSAFE_ORIGINAL_SOURCE")
    gross = []
    for index, row in enumerate(primary["folds"], 1):
        if row.get("fold") != index or row.get("events_per_asset") not in (396, 397):
            raise ValueError("INVALID_CHRONOLOGICAL_FOLD")
        btc = decimal(row["btc_signed_rate_sum"])
        eth = decimal(row["eth_signed_rate_sum"])
        g = (btc + eth) / 2
        if abs(g - decimal(row["static_50_50_signed_funding_rate_budget_NOT_ROI"])) > Decimal("1e-10"):
            raise ValueError("SOURCE_FOLD_BUDGET_MISMATCH")
        if abs(g - decimal(source_oracle["fold_signed_rate_budgets_NOT_ROI"][index-1])) > Decimal("1e-10"):
            raise ValueError("INDEPENDENT_ORIGINAL_FOLD_MISMATCH")
        gross.append(g)
    scenarios = {}
    for name, cost in COST.items():
        adjusted = [g-cost for g in gross]
        budget = sum(adjusted, Decimal(0))
        if budget <= 0:
            raise ValueError("NONPOSITIVE_STATIC_NOMINAL_BUDGET")
        multiple = TARGET / budget
        if primary["positive_budget_folds"].get(name) != sum(v>0 for v in adjusted):
            raise ValueError("FIVEFOLD_SOURCE_STATUS_MISMATCH")
        for index, v in enumerate(adjusted):
            reported = primary["folds"][index]["illustrative_budget_minus_four_side_cost_NOT_ROI"][name]
            if abs(v-decimal(reported)) > Decimal("1e-10"):
                raise ValueError("ORIGINAL_COST_BUDGET_MISMATCH")
        scenarios[name] = {
            "nominal_funding_budget_per_unit_notional_NOT_ROI": str(budget),
            "illustrative_notional_to_initial_equity_multiple_NOT_NAV": str(multiple),
            "residual_adverse_basis_shock_for_35pp_equity_erosion_NOT_LIQUIDATION": str(DD_BUDGET/multiple),
            "residual_adverse_basis_shock_for_100pp_equity_erosion_NOT_LIQUIDATION": str(TARGET/multiple),
            "positive_folds_nominal_budget_NOT_NAV": sum(v>0 for v in adjusted),
            "weakest_fold_nominal_budget_per_unit_notional_NOT_ROI": str(min(adjusted)),
            "weakest_fold_at_illustrative_multiple_NOT_NAV": str(min(adjusted)*multiple),
        }
    return {
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_NOTIONAL_RISK_SENSITIVITY_NOT_AN_ECONOMIC_ENGINE",
        "source_original_archives": 44,
        "source_original_events_per_asset": 1983,
        "target_nominal_budget_equity_points_NOT_ROI": "1",
        "scenarios": scenarios,
        "budget_is_not_nav_roi_or_realized_funding": True,
        "shock_is_not_liquidation_or_historical_var": True,
        "native_fees_basis_fills_margin_not_certified": True,
        "economic_train_executed": False,
        "promotion_authorized": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "paper_modified": False,
        "frozen_modified": False,
    }


def run(root):
    root = Path(root)
    primary = json.loads((root/"static_funding_budget_source_only.json").read_text())
    oracle = json.loads((root/"static_funding_budget_independent_oracle.json").read_text())
    result = evaluate(primary, oracle)
    (root/"static_funding_leverage_source_only.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_static_funding_leverage_feasibility OUTDIR")
    run(sys.argv[1])
