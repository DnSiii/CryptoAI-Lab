"""C8 training-ledger execution-frequency forensic audit; no strategy selection.

Separates daily decision refresh from hourly drift rebalancing. This diagnostic
does not modify historical trades or claim a counterfactual PnL.
"""
import argparse
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCENARIOS = ("1x", "2x", "4x")

def audit(directory):
    directory = Path(directory)
    if "v98_independent" not in directory.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary = json.loads((directory / "c8_composed_summary.json").read_text())
    if summary.get("source") != "AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("INVALID_PROVENANCE")
    if set(summary["results"]) != set(SCENARIOS):
        raise ValueError("INCOMPLETE_SCENARIOS")
    result = {"status": "TRAINING_EXECUTION_FORENSIC_ONLY_NO_PROMOTION",
              "holdout_accessed": False, "scenarios": {}}
    for scenario in SCENARIOS:
        path = directory / f"c8_composed_summary_{scenario}_ledger.jsonl"
        sums = {"daily_decision_turnover": 0., "interdecision_turnover": 0.,
                "daily_decision_fills": 0, "interdecision_fills": 0,
                "daily_decision_cost_return_sum": 0., "interdecision_cost_return_sum": 0.,
                "interdecision_target_changes": 0}
        previous = None
        count = 0
        for line in path.open():
            e = json.loads(line)
            i = e["index"]
            if i != count+1:
                raise ValueError("NONCONTIGUOUS_LEDGER")
            for key in ("turnover", "cost_return", "equity"):
                if not math.isfinite(float(e[key])):
                    raise ValueError("NONFINITE_LEDGER")
            if e["turnover"] < 0 or e["cost_return"] < 0 or e["equity"] <= 0:
                raise ValueError("INVALID_LEDGER")
            before = e["weights_before_fill"]
            after = e["weights_after_fill"]
            if set(before) != set(ASSETS) or set(after) != set(ASSETS):
                raise ValueError("INVALID_ASSETS")
            if not math.isclose(sum(abs(after[a]-before[a]) for a in ASSETS),
                                e["turnover"], rel_tol=1e-9, abs_tol=1e-10):
                raise ValueError("TURNOVER_MISMATCH")
            if previous is not None and i % 24 != 0:
                if any(abs(after[a]-previous[a]) > 1e-10 for a in ASSETS):
                    sums["interdecision_target_changes"] += 1
            bucket = "daily_decision" if i % 24 == 0 else "interdecision"
            sums[bucket+"_turnover"] += e["turnover"]
            sums[bucket+"_cost_return_sum"] += e["cost_return"]
            sums[bucket+"_fills"] += int(e["turnover"] > 1e-12)
            previous = after
            count += 1
        if count != 27047 or summary["results"][scenario]["hours"] != 27048:
            raise ValueError("INCOMPLETE_HISTORY")
        total = sums["daily_decision_turnover"] + sums["interdecision_turnover"]
        if not math.isclose(total, summary["results"][scenario]["total_turnover"],
                            rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError("SUMMARY_TURNOVER_MISMATCH")
        sums["interdecision_turnover_fraction"] = sums["interdecision_turnover"]/total if total else 0.
        result["scenarios"][scenario] = sums
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.directory)
    output = args.directory / "c8_execution_frequency_forensic.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
