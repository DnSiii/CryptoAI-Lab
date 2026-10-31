"""Independent risk arithmetic from original-ZIP-derived funding oracle; no primary import."""
from __future__ import annotations
import json
import sys
from decimal import Decimal
from pathlib import Path

FEES = {"severe": Decimal("0.0028"), "supersevere": Decimal("0.0056")}


def verify(root):
    root = Path(root)
    base = json.loads((root/"static_funding_budget_independent_oracle.json").read_text())
    result = json.loads((root/"static_funding_leverage_source_only.json").read_text())
    if (base.get("status") != "INDEPENDENT_44_ORIGINAL_PUBLISHER_ZIPS_FIVEFOLD_BUDGET_REEXECUTED"
        or base.get("original_files") != 44 or base.get("events_per_asset") != 1983
        or len(base.get("fold_signed_rate_budgets_NOT_ROI", [])) != 5
        or result.get("status") != "SOURCE_ONLY_NOTIONAL_RISK_SENSITIVITY_NOT_AN_ECONOMIC_ENGINE"
        or result.get("source_original_archives") != 44):
        raise ValueError("UNVERIFIED_SOURCE_CHAIN")
    rates = [Decimal(str(x)) for x in base["fold_signed_rate_budgets_NOT_ROI"]]
    for name, fee in FEES.items():
        values = [rate-fee for rate in rates]
        total = sum(values, Decimal(0))
        if total <= 0:
            raise ValueError("NO_POSITIVE_NOMINAL_BUDGET")
        multiple = Decimal(1)/total
        expected = {
            "nominal_funding_budget_per_unit_notional_NOT_ROI": total,
            "illustrative_notional_to_initial_equity_multiple_NOT_NAV": multiple,
            "residual_adverse_basis_shock_for_35pp_equity_erosion_NOT_LIQUIDATION": Decimal("0.35")/multiple,
            "residual_adverse_basis_shock_for_100pp_equity_erosion_NOT_LIQUIDATION": Decimal(1)/multiple,
            "weakest_fold_nominal_budget_per_unit_notional_NOT_ROI": min(values),
            "weakest_fold_at_illustrative_multiple_NOT_NAV": min(values)*multiple,
        }
        observed = result["scenarios"][name]
        for key, value in expected.items():
            if abs(Decimal(observed[key])-value) > Decimal("1e-10"):
                raise ValueError("INDEPENDENT_RISK_SENSITIVITY_MISMATCH:"+name+":"+key)
        if observed["positive_folds_nominal_budget_NOT_NAV"] != sum(v>0 for v in values):
            raise ValueError("INDEPENDENT_FIVEFOLD_SIGN_MISMATCH")
    for k in ("economic_train_executed","promotion_authorized","validation_opened",
              "holdout_opened","orders_enabled","paper_modified","frozen_modified"):
        if result.get(k) is not False:
            raise ValueError("UNAUTHORIZED_ECONOMIC_OR_PUBLICATION_CLAIM")
    for k in ("budget_is_not_nav_roi_or_realized_funding",
              "shock_is_not_liquidation_or_historical_var",
              "native_fees_basis_fills_margin_not_certified"):
        if result.get(k) is not True:
            raise ValueError("MISSING_SOURCE_ONLY_DISCLAIMER")
    verdict = {
        "status": "INDEPENDENT_SOURCE_ORACLE_TO_NOTIONAL_RISK_ARITHMETIC_PASS",
        "original_files_replayed_upstream": 44,
        "source_only": True,
        "economic_train_executed": False,
        "promotion_authorized": False,
    }
    (root/"static_funding_leverage_independent_oracle.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True)+"\n")
    print(json.dumps(verdict, sort_keys=True))
    return verdict


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_static_funding_leverage_oracle OUTDIR")
    verify(sys.argv[1])
