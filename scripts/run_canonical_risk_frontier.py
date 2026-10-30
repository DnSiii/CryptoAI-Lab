from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from run_canonical_risk_stress import bootstrap, cap_targets


START = "2021-01-01"
END = "2026-07-31 23:00"
REPORT_PATH = PROJECT / "reports" / "candidate_v13_risk_frontier.json"
EQUITY_PATH = PROJECT / "reports" / "candidate_v13_risk_frontier_selected_equity.csv"


def checkpoint(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v13_pit_carry_core.json").read_text()
    )
    data = load_data(PROJECT, config["data_config"])
    targets = pd.read_csv(
        PROJECT / "reports" / "candidate_v13_pit_carry_core_targets.csv",
        index_col=0,
        parse_dates=True,
    )
    targets.index = pd.to_datetime(targets.index, utc=True)
    targets = targets.reindex(
        index=data.close.index, columns=data.close.columns
    ).fillna(0.0)
    execution = config["execution"]

    report = {
        "status": "in_progress",
        "candidate": config["name"],
        "objective": (
            "Find the highest-growth target cap that keeps conservative bootstrap "
            "ruin probability below 1%, without exceeding 35% historical drawdown."
        ),
        "bootstrap_paths_per_design": 4_000,
        "rows": [],
    }
    prior = json.loads(
        (PROJECT / "reports" / "candidate_v13_canonical_risk_stress.json").read_text()
    )
    prior_metric = prior["scenarios"]["controlled_base"]
    prior_risk = prior["bootstrap"]
    prior_row = {
        "target_cap": float(prior["selected_target_cap"]),
        "metric": prior_metric,
        "bootstrap_worst_ruin_probability": prior_risk[
            "worst_estimated_ruin_probability"
        ],
        "bootstrap_probability_terminal_below_start_worst": max(
            item["probability_terminal_below_start"]
            for item in prior_risk["designs"].values()
        ),
        "passes": {
            "ruin_below_1pct": (
                prior_risk["worst_estimated_ruin_probability"] < 0.01
            ),
            "drawdown_no_worse_than_35pct": (
                prior_metric["max_drawdown"] >= -0.35
            ),
            "cagr_at_least_50pct": prior_metric["cagr"] >= 0.50,
            "gross_exposure_within_1_5x": (
                prior_metric["max_gross_exposure"] <= 1.505
            ),
        },
        "source": "30,000-path canonical stress run",
    }
    prior_row["passes_all"] = all(prior_row["passes"].values())
    report["rows"].append(prior_row)
    checkpoint(report)

    results = {}
    for cap in (1.20, 1.05, 0.90, 0.75, 0.60):
        print(f"starting target cap {cap:.2f}", flush=True)
        controlled_targets = cap_targets(targets, cap)
        result = exact(
            data,
            controlled_targets,
            execution["base_cost_per_side"],
            execution["maintenance_equity_fraction"],
            gross_guard_cap=1.5,
        )
        metric = slice_summary(
            result.equity,
            result.turnover,
            result.gross_exposure,
            START,
            END,
        )
        risk = bootstrap(result.equity, paths=4_000)
        row = {
            "target_cap": cap,
            "metric": metric,
            "bootstrap_worst_ruin_probability": risk[
                "worst_estimated_ruin_probability"
            ],
            "bootstrap_probability_terminal_below_start_worst": max(
                item["probability_terminal_below_start"]
                for item in risk["designs"].values()
            ),
            "passes": {
                "ruin_below_1pct": (
                    risk["worst_estimated_ruin_probability"] < 0.01
                ),
                "drawdown_no_worse_than_35pct": (
                    metric["max_drawdown"] >= -0.35
                ),
                "cagr_at_least_50pct": metric["cagr"] >= 0.50,
                "gross_exposure_within_1_5x": (
                    metric["max_gross_exposure"] <= 1.505
                ),
            },
        }
        row["passes_all"] = all(row["passes"].values())
        report["rows"].append(row)
        results[cap] = result
        checkpoint(report)
        print(
            f"completed {cap:.2f}: CAGR={metric['cagr']:.4f} "
            f"DD={metric['max_drawdown']:.4f} "
            f"ruin={risk['worst_estimated_ruin_probability']:.4f}",
            flush=True,
        )

    eligible = [row for row in report["rows"] if row["passes_all"]]
    if eligible:
        selected = max(eligible, key=lambda row: row["metric"]["cagr"])
        selected_cap = selected["target_cap"]
        equity = results[selected_cap].equity.rename("equity")
        equity.rename_axis("timestamp").to_csv(EQUITY_PATH)
        report["selected"] = selected
        report["selected_equity_path"] = str(EQUITY_PATH.relative_to(PROJECT))
    else:
        report["selected"] = None
        report["selected_equity_path"] = None
    report["status"] = "completed"
    checkpoint(report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
