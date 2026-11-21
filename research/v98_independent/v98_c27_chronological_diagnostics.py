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
        # Validate the full economic ledger before deriving any annual statistic.
        # JSON permits NaN/Infinity by default; never allow either into a gate.
        for expected_index, row in enumerate(rows, 1):
            if row["index"] != expected_index:
                raise ValueError("C27_LEDGER_INDEX_DISCONTINUITY")
            for field in ("equity", "cost_return", "funding_return"):
                value = row[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError("C27_NONFINITE_LEDGER_" + field.upper())
            if row["equity"] <= 0:
                raise ValueError("C27_NONPOSITIVE_LEDGER_EQUITY")
        folds = {}
        for year, (start, end) in YEAR_HOURS.items():
            # Year starts at the previous hour close; year ends at the last
            # hour of that year. Never import the next year opening mark.
            lo = rows[start - 2]["equity"]
            # The final 2025 close is stored in the authenticated summary.
            hi = (rows[end - 2]["equity"] if end < 27048
                  else result["results"][scenario]["final_equity"])
            hourly = [rows[i - 1]["equity"] / rows[i - 2]["equity"] - 1
                      for i in range(start, min(end - 1, 27047) + 1)]
            positive = sum(x > 0 for x in hourly)
            peak = lo
            dd = 0.
            for i in range(start, min(end - 1, 27047) + 1):
                equity = rows[i - 1]["equity"]
                peak = max(peak, equity)
                dd = max(dd, 1 - equity / peak)
            if end == 27048:
                peak = max(peak, hi)
                dd = max(dd, 1 - hi / peak)
            folds[year] = {"return": hi / lo - 1, "max_drawdown": dd,
                           "positive_hours": positive, "observed_hours": end - start,
                           "fees_return_sum": sum(rows[i - 1]["cost_return"] for i in range(start, min(end, 27047))),
                           "funding_return_sum": sum(rows[i - 1]["funding_return"] for i in range(start, min(end, 27047)))}
            if not all(math.isfinite(v) for v in folds[year].values()):
                raise ValueError("C27_NONFINITE_FOLD")
        # Fail closed if annual boundary marks do not form a contiguous,
        # self-financing equity chain. This checks accounting only, not OOS.
        opening = rows[YEAR_HOURS["2023"][0] - 2]["equity"]
        if not math.isfinite(opening) or opening <= 0:
            raise ValueError("C27_INVALID_TRAINING_OPENING_EQUITY")
        compounded = opening
        for year in YEAR_HOURS:
            compounded *= 1.0 + folds[year]["return"]
        terminal = result["results"][scenario]["final_equity"]
        if not math.isfinite(terminal) or not math.isclose(
                compounded, terminal, rel_tol=1e-10, abs_tol=1e-7):
            raise ValueError("C27_ANNUAL_BOUNDARY_RECONCILIATION_FAILED")
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
