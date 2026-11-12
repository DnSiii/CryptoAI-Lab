"""Frozen C1 leave-one-sleeve-out full-system counterfactuals, training only.

No sleeve reallocation; recompute causal fills, funding and costs from scratch.
Protocol: v98_c1_frozen_ablation_prereg_20261112.md
"""
import argparse
import json
import math
from pathlib import Path
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_phase243_training_reader import load, START_MS
from .v98_composed_c1 import composed_c1_sleeves
from .v98_b0_next_open_execution import replay_next_open
from .v98_b0_independent_arithmetic_audit import reconcile
from .v98_b0_chronological_evidence import audit as chronological_audit

SLOTS = ("growth_core", "opportunity", "relative_value", "stress_recovery")

def removed_sleeve(slot):
    if slot not in SLOTS:
        raise ValueError("UNKNOWN_C1_SLOT")
    index = SLOTS.index(slot)
    base = composed_c1_sleeves()
    def compute(history):
        full = base(history)
        return {a: tuple(0. if j == index else float(v)
                         for j, v in enumerate(full[a])) for a in ASSETS}
    return compute

def run(prices, manifest, funding, baseline_path):
    data = load(prices, manifest, funding)
    baseline = json.loads(Path(baseline_path).read_text())
    if data["hours"] != 27048 or baseline.get("holdout_accessed") is not False:
        raise ValueError("C1_ABLATION_BOUNDARY")
    if baseline.get("price_manifest_sha256") != data["price_manifest_sha256"] or baseline.get("funding_manifest_sha256") != data["funding_manifest_sha256"]:
        raise ValueError("C1_ABLATION_SOURCE_MISMATCH")
    if set(baseline.get("results", {})) != {"1x", "2x", "4x"}:
        raise ValueError("C1_ABLATION_BASELINE_INCOMPLETE")
    indexed = {a: {} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"] * HOUR_MS:
                raise ValueError("C1_ABLATION_FUNDING_TIMESTAMP")
            indexed[a][offset // HOUR_MS] = rate
    output = {}
    for slot in SLOTS:
        output[slot] = {}
        for scale in (1., 2., 4.):
            label = f"{int(scale)}x"
            summary, ledger = replay_next_open(data["bars"], indexed, removed_sleeve(slot), cost_scale=scale)
            if summary["hours"] != 27048 or len(ledger) != 27047:
                raise ValueError("C1_ABLATION_INCOMPLETE")
            audit = reconcile(ledger, summary)
            if audit["status"] != "PASS" or audit["max_relative_residual"] > 1e-9:
                raise ValueError("C1_ABLATION_ACCOUNTING_FAILED")
            chronology = chronological_audit(ledger, summary["final_equity"])
            base_equity = float(baseline["results"][label]["final_equity"])
            if not all(math.isfinite(float(summary[k])) for k in ("final_equity", "max_drawdown", "total_turnover", "funding_return_sum")):
                raise ValueError("C1_ABLATION_NONFINITE")
            output[slot][label] = {
                "counterfactual_final_equity": summary["final_equity"],
                "full_c1_final_equity": base_equity,
                "marginal_final_equity": base_equity - summary["final_equity"],
                "counterfactual_max_drawdown": summary["max_drawdown"],
                "counterfactual_turnover": summary["total_turnover"],
                "counterfactual_funding_return_sum": summary["funding_return_sum"],
                "counterfactual_annual_returns": chronology["utc_annual_returns_including_warmup"],
                "arithmetic_status": audit["status"],
                "arithmetic_max_residual": audit["max_relative_residual"],
            }
    return {"status": "C1_FROZEN_TRAINING_ABLATION_NO_PROMOTION",
            "holdout_accessed": False,
            "price_manifest_sha256": data["price_manifest_sha256"],
            "funding_manifest_sha256": data["funding_manifest_sha256"],
            "results": output}

def main():
    parser = argparse.ArgumentParser()
    for key in ("prices", "manifest", "funding", "baseline", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    args = parser.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = run(args.prices, args.manifest, args.funding, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({slot: {scale: row["marginal_final_equity"] for scale, row in values.items()}
                      for slot, values in result["results"].items()}, sort_keys=True))

if __name__ == "__main__":
    main()
