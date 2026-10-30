from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
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


PHASE_SETS = ((0, 1), (0, 2), (1, 2), (0, 1, 2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-project", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--refinement-report", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "reports" / "opportunity_phase_ensemble_v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lab = json.loads((PROJECT / "config" / "opportunity_lab_v1.json").read_text())
    baseline = json.loads(args.baseline_report.read_text())
    refinement = json.loads(args.refinement_report.read_text())
    selected = refinement["selected_for_parameter_neighborhood"]
    finalist = json.loads(
        (PROJECT / "config" / lab["frozen_core"]["config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    seed = StrategySpec(**refinement["candidate"]["spec"])
    budget = OpportunityBudget(**selected["budget"])
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
    phase_targets = {
        phase: build_targets(signal_data, replace(seed, rebalance_phase=phase))
        for phase in (0, 1, 2)
    }
    risk = lab["risk_constraints"]
    guard = finalist["circuit_breaker"]
    portfolio_guard = (
        budget.maximum_portfolio_gross + lab["gross_drift_allowance"]
    )
    report = {
        "status": "in_progress",
        "seed": seed.to_dict(),
        "budget": selected["budget"],
        "method": (
            "Equal-weight ensembles of independently causal rebalance phases. "
            "The portfolio budget is unchanged."
        ),
        "rows": [],
        "selected_for_full_neighborhood": None,
        "paper_promotion": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for phases in PHASE_SETS:
        name = "phases_" + "_".join(str(phase) for phase in phases)
        print(f"phase ensemble {name}", flush=True)
        opportunity = sum(phase_targets[phase] for phase in phases) / len(phases)
        combined, allocated = additive_opportunity_targets(
            core_targets,
            opportunity,
            budget,
        )
        row = {
            "name": name,
            "phases": list(phases),
            "active_fraction": float(
                (allocated.abs().sum(axis=1) > 1e-12).mean()
            ),
            "average_overlay_gross": float(allocated.abs().sum(axis=1).mean()),
            "combined": {},
            "wealth_ratio_vs_core": {},
        }
        for scenario in SCENARIOS:
            scenario_name = scenario[0]
            metric = diagnostic(
                replay(data, combined, scenario, portfolio_guard, guard)
            )
            row["combined"][scenario_name] = metric
            row["wealth_ratio_vs_core"][scenario_name] = wealth_ratio(
                metric,
                baseline["core"]["scenarios"][scenario_name],
            )
        row["drawdown_checks"] = {
            scenario_name: row["combined"][scenario_name]["max_drawdown"] >= max(
                risk["historical_max_drawdown_floor"],
                baseline["core"]["scenarios"][scenario_name]["max_drawdown"]
                - risk["maximum_drawdown_deterioration_vs_core"],
            )
            for scenario_name, *_ in SCENARIOS
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
        row["passes_all"] = all(row["gates"].values())
        row["robust_wealth_score"] = min(row["wealth_ratio_vs_core"].values())
        report["rows"].append(row)
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    passing = [row for row in report["rows"] if row["passes_all"]]
    if passing:
        selected_row = max(
            passing,
            key=lambda row: (
                row["robust_wealth_score"],
                row["combined"]["base"]["terminal_wealth"],
            ),
        )
        report["selected_for_full_neighborhood"] = {
            "name": selected_row["name"],
            "phases": selected_row["phases"],
            "robust_wealth_score": selected_row["robust_wealth_score"],
            "base_cagr": selected_row["combined"]["base"]["cagr"],
            "base_max_drawdown": selected_row["combined"]["base"]["max_drawdown"],
            "not_paper_approved": True,
        }
    report["status"] = "completed"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "selected": report["selected_for_full_neighborhood"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
