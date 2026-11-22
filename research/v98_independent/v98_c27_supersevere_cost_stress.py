"""C27 fixed-architecture supersevere execution-cost stress, training only.

No parameter search, candidate selection, future data, or holdout access.
Reuses the exact authenticated Clean-4 reader and causal C27 execution.
"""
import argparse
import json
import math
from pathlib import Path

from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_c27_authenticated_runner import replay

STRESS_SCALES = (8., 12.)

def evaluate(prices, manifest, funding):
    data = load(prices, manifest, funding)
    indexed = {asset: {} for asset in ASSETS}
    for asset in ASSETS:
        for stamp, rate in data["funding"][asset].items():
            offset = stamp - START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"] * HOUR_MS:
                raise ValueError("C27_STRESS_INVALID_FUNDING_STAMP")
            indexed[asset][offset // HOUR_MS] = rate
    results = {}
    for scale in STRESS_SCALES:
        summary, ledger = replay(data["bars"], indexed, scale)
        if len(ledger) != 27047 or summary["hours"] != 27048:
            raise ValueError("C27_STRESS_INCOMPLETE")
        if not all(math.isfinite(summary[k]) for k in ("final_equity", "max_drawdown", "total_turnover", "funding_return_sum")):
            raise ValueError("C27_STRESS_NONFINITE")
        if summary["final_equity"] <= 0 or summary["total_turnover"] <= 0:
            raise ValueError("C27_STRESS_INSOLVENT_OR_ZERO_TRADE")
        if any(row["hard_cap_breach_after_fill"] for row in ledger):
            raise ValueError("C27_STRESS_HARD_CAP_BREACH")
        results[f"{int(scale)}x"] = summary
    return {
        "status": "C27_TRAINING_ONLY_SUPERSEVERE_COST_STRESS_NOT_VALIDATION",
        "holdout_accessed": False,
        "source": "AUTHENTICATED_CLEAN4",
        "price_manifest_sha256": data["price_manifest_sha256"],
        "funding_manifest_sha256": data["funding_manifest_sha256"],
        "results": results,
        "limitations": "Stress scales 8x and 12x are fixed adverse transaction-cost scenarios, not independent validation or a deployability claim. Funding remains native and unscaled."
    }

def main():
    parser = argparse.ArgumentParser()
    for name in ("prices", "manifest", "funding", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = evaluate(args.prices, args.manifest, args.funding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))

if __name__ == "__main__":
    main()
