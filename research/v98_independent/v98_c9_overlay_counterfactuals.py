"""C9 causal system-overlay counterfactuals; training diagnostics, never promotion.

Compare unchanged C9 sleeves with independently disabled router, allocator caps,
or drawdown governor. This is NOT a performance-selection grid: the no-cap
counterfactual deliberately violates risk limits and is never deployable.
"""
import argparse
import json
import math
from pathlib import Path
from unittest.mock import patch

from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_composed_c9 import composed_c9_sleeves
from .v98_b0_next_open_execution import replay_next_open
from .v98_b0_causal_overlay import compose_weights


def evaluate(prices, manifest, funding):
    data = load(prices, manifest, funding)
    indexed = {a: {} for a in ASSETS}
    for asset in ASSETS:
        for stamp, rate in data["funding"][asset].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"] * HOUR_MS:
                raise ValueError("INVALID_FUNDING_TIMESTAMP")
            indexed[asset][offset // HOUR_MS] = rate

    def no_router(_history):
        return 1.0

    def no_governor(_equity, _peak):
        return 1.0

    def no_allocator_caps(sleeves, routers, governor):
        return compose_weights(sleeves, routers, governor, gross_cap=1.0, asset_cap=1.0)

    cases = ("baseline", "without_regime_router",
             "without_dynamic_allocator_caps", "without_risk_governor")
    results = {}
    for case in cases:
        scenarios = {}
        for scale in (1., 2., 4.):
            overrides = {}
            if case == "without_regime_router":
                overrides["regime_multiplier"] = no_router
            elif case == "without_dynamic_allocator_caps":
                overrides["compose_weights"] = no_allocator_caps
            elif case == "without_risk_governor":
                overrides["governor_multiplier"] = no_governor
            # Patch only the execution module's references, restore on exit.
            from . import v98_b0_next_open_execution as execution
            from contextlib import ExitStack
            with ExitStack() as stack:
                for key, fn in overrides.items():
                    stack.enter_context(patch.object(execution, key, fn))
                summary, ledger = replay_next_open(
                    data["bars"], indexed, composed_c9_sleeves(), cost_scale=scale)
            if summary["hours"] != data["hours"] or len(ledger) != data["hours"] - 1:
                raise ValueError("INCOMPLETE_COUNTERFACTUAL")
            if not all(math.isfinite(float(summary[k])) for k in
                       ("final_equity", "max_drawdown", "total_turnover", "funding_return_sum")):
                raise ValueError("NONFINITE_COUNTERFACTUAL")
            max_gross = max(sum(abs(v) for v in row["weights_after_fill"].values())
                            for row in ledger)
            scenarios[str(int(scale)) + "x"] = {
                "final_equity": summary["final_equity"],
                "max_drawdown": summary["max_drawdown"],
                "max_gross_exposure": max_gross,
                "turnover": summary["total_turnover"]}
        results[case] = scenarios
    for case in cases[1:]:
        for key in ("1x", "2x", "4x"):
            results[case][key]["baseline_minus_counterfactual_equity"] = (
                results["baseline"][key]["final_equity"] - results[case][key]["final_equity"])
    return {
        "status": "TRAINING_OVERLAY_DIAGNOSTICS_NO_PROMOTION",
        "holdout_accessed": False,
        "source": "AUTHENTICATED_CLEAN4",
        "price_manifest_sha256": data["price_manifest_sha256"],
        "funding_manifest_sha256": data["funding_manifest_sha256"],
        "interpretation": "Governor is a survival constraint, not an alpha sleeve; no-cap case is nondeployable. No overlay is selected by these diagnostics.",
        "results": results}


def main():
    p = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = evaluate(args.prices, args.manifest, args.funding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
