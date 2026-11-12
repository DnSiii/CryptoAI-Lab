"""Descriptive B0 diagnostics from full chronological ledgers; never a promotion gate."""
import json
import math
from pathlib import Path

def diagnose(entries, initial_equity=10000., final_equity=None):
    if not entries:
        raise ValueError("EMPTY_LEDGER")
    if any(e["index"] != i + 1 for i, e in enumerate(entries)):
        raise ValueError("NONCONTIGUOUS_LEDGER")
    if any(not math.isfinite(e["equity"]) or e["equity"] <= 0 for e in entries):
        raise ValueError("INVALID_EQUITY")
    days = {}
    for e in entries:
        days[(e["index"] - 1) // 24] = e["equity"]
    prev = initial_equity
    daily_returns = []
    for _, equity in sorted(days.items()):
        daily_returns.append(equity / prev - 1)
        prev = equity
    # The final open-to-close mark is absent from the fill ledger: include it
    # in the final calendar bucket, never silently report a stale final day.
    if final_equity is not None:
        if not math.isfinite(final_equity) or final_equity <= 0:
            raise ValueError("INVALID_FINAL_EQUITY")
        last_day = (entries[-1]["index"] - 1) // 24
        days[last_day] = final_equity
        prev = initial_equity
        daily_returns = []
        for _, day_equity in sorted(days.items()):
            daily_returns.append(day_equity / prev - 1)
            prev = day_equity
    exposure = {a: sum(abs(e["weights_after_fill"][a]) for e in entries) / len(entries)
                for a in entries[0]["weights_after_fill"]}
    return {
        "observations": len(entries),
        "observed_days": len(daily_returns),
        "positive_days": sum(x > 0 for x in daily_returns),
        "daily_return_min": min(daily_returns),
        "daily_return_max": max(daily_returns),
        "daily_return_mean": sum(daily_returns) / len(daily_returns),
        "max_reported_drawdown_at_fills": max(e["drawdown"] for e in entries),
        "total_turnover": sum(e["turnover"] for e in entries),
        "total_cost_return_sum": sum(e["cost_return"] for e in entries),
        "mean_absolute_asset_exposure": exposure,
        "warning": "Descriptive only; not an independent audit or trade-level PF. Final-close mark included only when final_equity is supplied.",
    }

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--directory", type=Path, required=True)
    args = p.parse_args()
    summary = json.loads((args.directory / "b0_next_open_summary.json").read_text())
    for scenario in ("1x", "2x", "4x"):
        path = args.directory / ("b0_next_open_summary_" + scenario + "_ledger.jsonl")
        with path.open() as stream:
            entries = [json.loads(line) for line in stream]
        report = diagnose(entries, final_equity=summary["results"][scenario]["final_equity"])
        (args.directory / ("b0_" + scenario + "_diagnostics.json")).write_text(
            json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")

if __name__ == "__main__":
    main()
