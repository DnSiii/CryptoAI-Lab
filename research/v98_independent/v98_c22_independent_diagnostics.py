"""V98 C22 independent diagnostic supplement. Training-only; never promotes candidates.

Reads the exact C22 authenticated ledgers and summary, reports profit factor,
payoff, daily win rate, exposure, turnover and yearly breakdown. No optimization.
"""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
SCALES = ("1x", "2x", "4x")
START = datetime(2022, 12, 1, tzinfo=timezone.utc)

def diagnose(summary_path):
    summary_path = Path(summary_path)
    summary = json.loads(summary_path.read_text())
    if summary.get("source") != "AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("SOURCE_HOLDOUT_CONTRACT")
    if set(summary["results"]) != set(SCALES):
        raise ValueError("MISSING_SCENARIOS")
    report = {}
    for scenario in SCALES:
        path = summary_path.with_name(summary_path.stem + "_" + scenario + "_ledger.jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if len(rows) != 27047 or summary["results"][scenario]["hours"] != 27048:
            raise ValueError("INCOMPLETE_LEDGER")
        by_year = defaultdict(list)
        day_end = {}
        exposures = []
        turnovers = []
        for i, row in enumerate(rows, 1):
            if row["index"] != i or set(row["weights_after_fill"]) != set(ASSETS):
                raise ValueError("INVALID_LEDGER_SEQUENCE")
            exposure = sum(abs(float(v)) for v in row["weights_after_fill"].values())
            if not math.isfinite(exposure) or exposure > .900000001:
                raise ValueError("INVALID_EXPOSURE")
            exposures.append(exposure)
            turnovers.append(float(row["turnover"]))
            stamp = START + timedelta(hours=i)
            by_year[str(stamp.year)].append(row)
            day_end[stamp.date().isoformat()] = float(row["equity"])
        daily = [10000.] + [day_end[d] for d in sorted(day_end)]
        daily[-1] = float(summary["results"][scenario]["final_equity"])
        rets = [daily[i] / daily[i-1] - 1 for i in range(1, len(daily))]
        wins = [r for r in rets if r > 0]
        losses = [-r for r in rets if r < 0]
        pf = sum(wins)/sum(losses) if losses else None
        payoff = (sum(wins)/len(wins))/(sum(losses)/len(losses)) if wins and losses else None
        report[scenario] = {
            "daily_profit_factor_simple_returns": pf,
            "daily_payoff": payoff,
            "positive_days": len(wins),
            "negative_days": len(losses),
            "flat_days": len(rets)-len(wins)-len(losses),
            "win_rate_nonflat_days": len(wins)/(len(wins)+len(losses)) if wins or losses else None,
            "mean_gross_exposure": sum(exposures)/len(exposures),
            "fraction_hours_exposed": sum(x>0 for x in exposures)/len(exposures),
            "total_turnover": sum(turnovers),
            "yearly": {year: {
                "hours": len(entries),
                "mean_gross_exposure": sum(sum(abs(float(v)) for v in r["weights_after_fill"].values()) for r in entries)/len(entries),
                "total_turnover": sum(float(r["turnover"]) for r in entries),
                "cost_return_sum": sum(float(r["cost_return"]) for r in entries),
                "funding_return_sum": sum(float(r["funding_return"]) for r in entries),
                "gross_return_sum": sum(float(r["gross_return"]) for r in entries),
            } for year, entries in sorted(by_year.items())}
        }
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    if "v98_independent" not in args.summary.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    print(json.dumps(diagnose(args.summary), sort_keys=True, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
