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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-project", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--refinement-report", type=Path, required=True)
    parser.add_argument("--ensemble-report", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "reports" / "opportunity_ensemble_neighborhood_v1.json",
    )
    return parser.parse_args()


def neighborhood(base: StrategySpec) -> list[tuple[str, StrategySpec]]:
    return [
        ("center", base),
        ("trend_240h", replace(base, trend_filter_hours=240)),
        ("trend_432h", replace(base, trend_filter_hours=432)),
        ("cooldown_12h", replace(base, cooldown_hours=12)),
        ("cooldown_36h", replace(base, cooldown_hours=36)),
        ("threshold_1_5pct", replace(base, threshold=0.015)),
        ("threshold_2_5pct", replace(base, threshold=0.025)),
        ("holding_120h", replace(base, max_holding=120)),
        ("holding_216h", replace(base, max_holding=216)),
    ]


def main() -> None:
    args = parse_args()
    lab = json.loads((PROJECT / "config" / "opportunity_lab_v1.json").read_text())
    baseline = json.loads(args.baseline_report.read_text())
    refinement = json.loads(args.refinement_report.read_text())
    ensemble = json.loads(args.ensemble_report.read_text())
    selected = ensemble["selected_for_full_neighborhood"]
    if selected is None:
        raise RuntimeError("phase ensemble did not select a candidate")
    phases = tuple(selected["phases"])
    budget = OpportunityBudget(
        **refinement["selected_for_parameter_neighborhood"]["budget"]
    )
    finalist = json.loads(
        (PROJECT / "config" / lab["frozen_core"]["config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    seed = StrategySpec(**refinement["candidate"]["spec"])
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
    risk = lab["risk_constraints"]
    guard = finalist["circuit_breaker"]
    portfolio_guard = (
        budget.maximum_portfolio_gross + lab["gross_drift_allowance"]
    )
    report = {
        "status": "in_progress",
        "center_spec": seed.to_dict(),
        "phases": list(phases),
        "budget": refinement["selected_for_parameter_neighborhood"]["budget"],
        "method": (
            "One-factor-at-a-time neighborhood of the equal-weight phase "
            "ensemble. Every version receives every mandatory exact scenario."
        ),
        "rows": [],
        "gate": None,
        "eligible_for_separate_forward_paper_proposal": False,
        "paper_promotion": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for number, (name, spec) in enumerate(neighborhood(seed), 1):
        print(f"ensemble neighborhood {number}/9 {name}", flush=True)
        opportunity = sum(
            build_targets(signal_data, replace(spec, rebalance_phase=phase))
            for phase in phases
        ) / len(phases)
        combined, allocated = additive_opportunity_targets(
            core_targets,
            opportunity,
            budget,
        )
        row = {
            "name": name,
            "spec": spec.to_dict(),
            "active_fraction": float(
                (allocated.abs().sum(axis=1) > 1e-12).mean()
            ),
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

    passing_fraction = sum(row["passes_all"] for row in report["rows"]) / len(
        report["rows"]
    )
    worst_score = min(row["robust_wealth_score"] for row in report["rows"])
    no_ruin = all(row["gates"]["no_exact_ruin"] for row in report["rows"])
    report["gate"] = {
        "passing_fraction": passing_fraction,
        "minimum_required_passing_fraction": 0.70,
        "worst_robust_wealth_score": worst_score,
        "minimum_required_worst_robust_wealth_score": 0.90,
        "no_exact_ruin_anywhere": no_ruin,
        "passes": (
            passing_fraction >= 0.70
            and worst_score >= 0.90
            and no_ruin
        ),
    }
    report["eligible_for_separate_forward_paper_proposal"] = report["gate"][
        "passes"
    ]
    report["status"] = "completed"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["gate"], indent=2), flush=True)


if __name__ == "__main__":
    main()
