#!/usr/bin/env python3
"""Read-only predeclared chronological A2 gate; never claims untouched validation.
A2 was already observed on the complete 2023-25 history. All slices are
retrospective diagnostics, not independent out-of-sample evidence.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from research.v98_independent.v98_a0_economic_diagnostics import evaluate

FOLDS = (("development", "2023-01-01", "2023-12-31"),
         ("retrospective_check", "2024-01-01", "2024-12-31"),
         ("retrospective_stress", "2025-01-01", "2025-12-31"))
SCENARIOS = ("1.0", "2.0", "4.0")

def run(directory, output):
    if any("v98_independent" not in p.absolute().parts for p in (directory, output)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result = {"status": "RETROSPECTIVE_ONLY_NOT_INDEPENDENT_VALIDATION",
              "holdout_accessed": False,
              "reason": "A2 complete-history results were observed before this gate existed",
              "folds": {}, "gates": {}}
    for scenario in SCENARIOS:
        rows = json.loads((directory / ("compound_ledger_" + scenario + ".json")).read_text())
        if len(rows) != 27048:
            raise ValueError("INCOMPLETE_HISTORY")
        stamps = [int(r["hour_open_ms"]) for r in rows]
        if len(set(stamps)) != len(stamps) or any(b-a != 3600000 for a,b in zip(stamps,stamps[1:])):
            raise ValueError("INVALID_CHRONOLOGY")
        slices = {}
        for label, first, last in FOLDS:
            subset = [r for r in rows if first <= datetime.fromtimestamp(
                int(r["hour_open_ms"])/1000,timezone.utc).date().isoformat() <= last]
            if len(subset) < 24*300:
                raise ValueError("INCOMPLETE_FOLD_" + label)
            slices[label] = evaluate(subset)
        result["folds"][scenario] = slices
    normal = result["folds"]["1.0"]
    result["gates"] = {
        "2023_positive": normal["development"]["total_return"] > 0,
        "2024_positive": normal["retrospective_check"]["total_return"] > 0,
        "2025_positive": normal["retrospective_stress"]["total_return"] > 0,
        "all_folds_positive_4x": all(v["total_return"] > 0 for v in result["folds"]["4.0"].values()),
        "independent_validation": False,
    }
    result["promotion_eligible"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--replay", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.replay,args.output), sort_keys=True))
