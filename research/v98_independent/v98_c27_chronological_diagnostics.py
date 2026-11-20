"""Independent chronological C27 diagnostics, training only; never a holdout gate."""
import argparse
import json
import math
from pathlib import Path

SCENARIOS = ("1x", "2x", "4x")
# 2022-12-01 00:00 UTC through 2025-12-31 23:00 UTC: 27048 hours.
# The 2022 warmup is not an economic validation fold.
START_HOUR = 0
YEAR_HOURS = {"2023": (744, 9504), "2024": (9504, 18288), "2025": (18288, 27048)}

def evaluate(summary):
    summary = Path(summary)
    result = json.loads(summary.read_text())
    if result["holdout_accessed"] is not False or result["source"] != "AUTHENTICATED_CLEAN4":
        raise ValueError("C27_WRONG_SOURCE_OR_HOLDOUT")
    out = {"status": "C27_RETROSPECTIVE_CHRONOLOGICAL_DIAGNOSTIC_NOT_VALIDATION",
           "folds": {}, "gate": "NOT_PRE_REGISTERED_NO_PROMOTION"}
    for scenario in SCENARIOS:
        ledger = summary.with_name(summary.stem + "_" + scenario + "_ledger.jsonl")
        rows = [json.loads(line) for line in ledger.open()]
        if len(rows) != 27047 or [r["index"] for r in rows] != list(range(1, 27048)):
            raise ValueError("C27_INCOMPLETE_OR_NONCHRONOLOGICAL_LEDGER")
        folds = {}
        for year, (start, end) in YEAR_HOURS.items():
            # Opening marks at start/end use post-cost equity. This is a diagnostic
            # convention, not an independent strategy selection criterion.
            lo = rows[start - 1]["equity"]
            hi = rows[end - 2]["equity"]
            hourly = [rows[i - 1]["equity"] / rows[i - 2]["equity"] - 1
                      for i in range(start + 1, end)]
            positive = sum(x > 0 for x in hourly)
            peak = lo
            dd = 0.
            for i in range(start, end):
                equity = rows[i - 1]["equity"]
                peak = max(peak, equity)
                dd = max(dd, 1 - equity / peak)
            folds[year] = {"return": hi / lo - 1, "max_drawdown": dd,
                           "positive_hours": positive, "observed_hours": end - start,
                           "fees_return_sum": sum(rows[i - 1]["cost_return"] for i in range(start, end)),
                           "funding_return_sum": sum(rows[i - 1]["funding_return"] for i in range(start, end))}
            if not all(math.isfinite(v) for v in folds[year].values()):
                raise ValueError("C27_NONFINITE_FOLD")
        out["folds"][scenario] = folds
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = evaluate(args.summary)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
