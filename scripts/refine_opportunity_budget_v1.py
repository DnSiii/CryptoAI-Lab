from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.data import load_data, point_in_time_liquid_view
from cryptoai_v13.opportunity import (
    OpportunityBudget,
    additive_opportunity_targets,
)
from cryptoai_v13.signals import StrategySpec, build_targets
from run_opportunity_lab_v1 import (
    SCENARIOS,
    diagnostic,
    load_core_targets,
    replay,
    wealth_ratio,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-project", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument(
        "--candidate",
        default="impulse_18_trend_336",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "reports" / "opportunity_budget_refinement_v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lab = json.loads((PROJECT / "config" / "opportunity_lab_v1.json").read_text())
    baseline = json.loads(args.baseline_report.read_text())
    finalist = json.loads(
        (PROJECT / "config" / lab["frozen_core"]["config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    candidate = next(
        row for row in lab["seed_candidates"] if row["name"] == args.candidate
    )
    data = load_data(args.data_project, base_config["data_config"])
    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    core_targets = load_core_targets(
        data,
        args.data_project
        / "reports"
        / "candidate_v13_pit_carry_core_targets.csv",
        finalist["target_cap"],
    )
    opportunity = build_targets(signal_data, StrategySpec(**candidate["spec"]))
    guard = finalist["circuit_breaker"]
    risk = lab["risk_constraints"]
    report = {
        "status": "in_progress",
        "candidate": candidate,
        "purpose": (
            "Find the smallest additive opportunity budget that preserves a "
            "robust wealth improvement without breaching the drawdown constraint."
        ),
        "core": baseline["core"],
        "rows": [],
        "selected_for_parameter_neighborhood": None,
        "paper_promotion": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for budget_row in lab["refinement_budget_grid"]:
        budget = OpportunityBudget(**budget_row)
        combined, allocated = additive_opportunity_targets(
            core_targets,
            opportunity,
            budget,
        )
        row = {
            "budget": budget_row,
            "active_fraction": float(
                (allocated.abs().sum(axis=1) > 1e-12).mean()
            ),
            "average_overlay_gross": float(allocated.abs().sum(axis=1).mean()),
            "combined": {},
            "wealth_ratio_vs_core": {},
        }
        portfolio_guard = (
            budget.maximum_portfolio_gross + lab["gross_drift_allowance"]
        )
        print(f"refining overlay={budget.maximum_overlay_gross}", flush=True)
        for scenario in SCENARIOS:
            name = scenario[0]
            metric = diagnostic(
                replay(data, combined, scenario, portfolio_guard, guard)
            )
            row["combined"][name] = metric
            row["wealth_ratio_vs_core"][name] = wealth_ratio(
                metric,
                baseline["core"]["scenarios"][name],
            )
        row["drawdown_checks"] = {
            name: row["combined"][name]["max_drawdown"] >= max(
                risk["historical_max_drawdown_floor"],
                baseline["core"]["scenarios"][name]["max_drawdown"]
                - risk["maximum_drawdown_deterioration_vs_core"],
            )
            for name, *_ in SCENARIOS
        }
        row["gates"] = {
            "beats_core_in_every_scenario": all(
                value > 1.0 for value in row["wealth_ratio_vs_core"].values()
            ),
            "no_exact_ruin": all(
                not value["ruin"] for value in row["combined"].values()
            ),
            "drawdown_constraints": all(row["drawdown_checks"].values()),
        }
        row["passes_preliminary_gate"] = all(row["gates"].values())
        row["robust_wealth_score"] = min(row["wealth_ratio_vs_core"].values())
        report["rows"].append(row)
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    passing = [row for row in report["rows"] if row["passes_preliminary_gate"]]
    if passing:
        selected = max(
            passing,
            key=lambda row: (
                row["combined"]["base"]["terminal_wealth"],
                row["robust_wealth_score"],
            ),
        )
        report["selected_for_parameter_neighborhood"] = {
            "budget": selected["budget"],
            "base_cagr": selected["combined"]["base"]["cagr"],
            "base_max_drawdown": selected["combined"]["base"]["max_drawdown"],
            "robust_wealth_score": selected["robust_wealth_score"],
            "not_paper_approved": True,
        }
    report["status"] = "completed"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "selected": report["selected_for_parameter_neighborhood"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
