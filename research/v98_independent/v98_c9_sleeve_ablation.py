"""C9 preregistered leave-one-sleeve-out marginal test; training only.

No parameter search, benchmark, or holdout. Compares identical chronological
Clean-4 replays under native funding and each cost scale.
"""
import argparse
import json
import math
from pathlib import Path
from .v98_composed_c9_authenticated_runner import run
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_composed_c9 import composed_c9_sleeves
from .v98_b0_next_open_execution import replay_next_open

SLOTS = ("growth_core", "opportunity", "relative_value", "stress_recovery")

def masked_sleeves(disabled):
    original = composed_c9_sleeves()
    index = SLOTS.index(disabled)
    def compute(history):
        result = original(history)
        return {asset: tuple(0. if j == index else weight
                             for j, weight in enumerate(result[asset]))
                for asset in ASSETS}
    return compute

def evaluate(prices, manifest, funding):
    baseline = run(prices, manifest, funding)
    data = load(prices, manifest, funding)
    indexed = {a:{} for a in ASSETS}
    for asset in ASSETS:
        for stamp, rate in data["funding"][asset].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"] * HOUR_MS:
                raise ValueError("C9_INVALID_FUNDING_TIMESTAMP")
            indexed[asset][offset // HOUR_MS] = rate
    output = {}
    for slot in SLOTS:
        scenarios = {}
        for scale in (1., 2., 4.):
            key = str(int(scale)) + "x"
            ablated, entries = replay_next_open(
                data["bars"], indexed, masked_sleeves(slot), cost_scale=scale)
            if ablated["hours"] != data["hours"] or len(entries) != data["hours"] - 1:
                raise ValueError("C9_INCOMPLETE_ABLATION")
            base = baseline["results"][key]
            contribution = base["final_equity"] - ablated["final_equity"]
            if not all(math.isfinite(v) for v in (contribution, ablated["final_equity"])):
                raise ValueError("C9_NONFINITE_ABLATION")
            scenarios[key] = dict(full_equity=base["final_equity"],
                                  without_equity=ablated["final_equity"],
                                  marginal_equity=contribution,
                                  without_max_drawdown=ablated["max_drawdown"])
        output[slot] = scenarios
    passed = all(output[slot][key]["marginal_equity"] > 0
                 for slot in SLOTS for key in ("1x", "2x", "4x"))
    return dict(status="C9_TRAINING_ABLATION_ONLY_NO_PROMOTION",
                source="AUTHENTICATED_CLEAN4", holdout_accessed=False,
                price_manifest_sha256=baseline["price_manifest_sha256"],
                funding_manifest_sha256=baseline["funding_manifest_sha256"],
                slots=output, all_four_sleeves_positive_all_costs=passed,
                decision="TRAINING_SLEEVE_GATE_PASS_NOT_VALIDATED" if passed
                         else "REJECT_C9_SLEEVE_GATE")

def main():
    parser = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = evaluate(args.prices, args.manifest, args.funding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True))
if __name__ == "__main__":
    main()
