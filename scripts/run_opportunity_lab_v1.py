from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import load_data, point_in_time_liquid_view
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.opportunity import (
    OpportunityBudget,
    additive_opportunity_targets,
)
from cryptoai_v13.signals import StrategySpec, build_targets


START = "2021-01-01"
END = "2026-07-31 23:00"

SCENARIOS = (
    ("base", 0.0007, 0, 1.0, 1.0),
    ("severe_cost", 0.0012, 0, 1.0, 1.0),
    ("delay_3h", 0.0007, 2, 1.0, 1.0),
    ("delay_6h", 0.0007, 5, 1.0, 1.0),
    ("adverse_funding", 0.0007, 0, 2.0, 0.5),
    ("severe_cost_and_adverse_funding", 0.0012, 0, 2.0, 0.5),
)


def cap_gross(targets: pd.DataFrame, cap: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (cap / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    return targets.mul(scale, axis=0)


def distribution(values: pd.Series) -> dict:
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "count": int(len(values)),
        "positive_fraction": float((values > 0.0).mean()),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "p10": float(values.quantile(0.10)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "above_4pct_fraction": float((values >= 0.04).mean()),
        "above_8pct_fraction": float((values >= 0.08).mean()),
        "above_15pct_fraction": float((values >= 0.15).mean()),
        "above_20pct_fraction": float((values >= 0.20).mean()),
    }


def diagnostic(result) -> dict:
    base = slice_summary(
        result.equity,
        result.turnover,
        result.gross_exposure,
        START,
        END,
    )
    equity = result.equity.loc[START:END]
    daily = equity.resample("1D").last().dropna()
    base["terminal_wealth"] = float(equity.iloc[-1])
    base["windows"] = {
        f"{days}d": distribution(daily.pct_change(days, fill_method=None))
        for days in (2, 3, 7, 14, 30)
    }
    base["calendar_month"] = distribution(
        equity.resample("ME").last().pct_change(fill_method=None)
    )
    return base


def replay(data, targets, scenario, gross_guard_cap: float, guard: dict):
    _, cost, delay, debit, credit = scenario
    return exact_fast(
        data,
        targets.shift(delay).fillna(0.0),
        cost_per_side=cost,
        maintenance_equity_fraction=0.02,
        gross_guard_cap=gross_guard_cap,
        funding_debit_multiplier=debit,
        funding_credit_multiplier=credit,
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def wealth_ratio(candidate: dict, core: dict) -> float:
    return float(candidate["terminal_wealth"] / core["terminal_wealth"])


def load_core_targets(data, path: Path, target_cap: float) -> pd.DataFrame:
    targets = pd.read_csv(path, index_col=0, parse_dates=True)
    targets.index = pd.to_datetime(targets.index, utc=True)
    targets = targets.reindex(
        index=data.close.index,
        columns=data.close.columns,
    ).fillna(0.0)
    return cap_gross(targets, target_cap)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-project",
        type=Path,
        default=PROJECT,
        help="Project containing full canonical research data.",
    )
    parser.add_argument(
        "--core-targets",
        type=Path,
        default=None,
        help="Frozen V13 target CSV; defaults to the data project report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "reports" / "opportunity_lab_v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lab = json.loads((PROJECT / "config" / "opportunity_lab_v1.json").read_text())
    finalist = json.loads(
        (PROJECT / "config" / lab["frozen_core"]["config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data = load_data(args.data_project, base_config["data_config"])
    universe = base_config["point_in_time_universe"]
    signal_data, membership = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    core_path = args.core_targets or (
        args.data_project
        / "reports"
        / "candidate_v13_pit_carry_core_targets.csv"
    )
    core_targets = load_core_targets(data, core_path, finalist["target_cap"])
    guard = finalist["circuit_breaker"]

    report = {
        "status": "in_progress",
        "methodology_version": 1,
        "objective": lab["objective"],
        "historical_disclosure": (
            "All available history has participated in prior research. These "
            "results are adversarial diagnostics, not a pristine holdout."
        ),
        "execution": (
            "Signals use completed hourly data and execute at the next open. "
            "Delay scenarios add two or five further target shifts."
        ),
        "core_unchanged_when_opportunity_inactive": True,
        "universe_average_members": float(membership.sum(axis=1).mean()),
        "core": {"scenarios": {}},
        "screen": [],
        "exact_finalists": [],
        "selected_for_next_research_stage": None,
        "paper_promotion": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for scenario in SCENARIOS:
        name = scenario[0]
        print(f"core scenario {name}", flush=True)
        report["core"]["scenarios"][name] = diagnostic(
            replay(data, core_targets, scenario, finalist["gross_guard_cap"], guard)
        )
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    opportunity_targets = {
        candidate["name"]: build_targets(
            signal_data,
            StrategySpec(**candidate["spec"]),
        )
        for candidate in lab["seed_candidates"]
    }
    allocations = {}
    for candidate in lab["seed_candidates"]:
        name = candidate["name"]
        for budget_row in lab["paired_budget_grid"]:
            budget = OpportunityBudget(**budget_row)
            combined, allocated = additive_opportunity_targets(
                core_targets,
                opportunity_targets[name],
                budget,
            )
            key = (
                name,
                budget.maximum_overlay_gross,
                budget.maximum_portfolio_gross,
            )
            allocations[key] = (combined, allocated)
            screened = diagnostic(
                screen(data, combined, base_config["execution"]["base_cost_per_side"])
            )
            report["screen"].append({
                "candidate": name,
                "spec": candidate["spec"],
                "budget": budget_row,
                "allocated_opportunity_active_fraction": float(
                    (allocated.abs().sum(axis=1) > 1e-12).mean()
                ),
                "average_allocated_opportunity_gross": float(
                    allocated.abs().sum(axis=1).mean()
                ),
                "metric": screened,
            })

    viable_screen = [
        row for row in report["screen"]
        if not row["metric"]["ruin"]
        and row["metric"]["max_drawdown"] >= -0.40
    ]
    finalist_count = int(lab["exact_finalists_after_screen"])
    ranked = sorted(
        viable_screen,
        key=lambda row: (
            row["metric"]["terminal_wealth"],
            row["metric"]["max_drawdown"],
        ),
        reverse=True,
    )[:finalist_count]

    for number, screened in enumerate(ranked, 1):
        budget_row = screened["budget"]
        key = (
            screened["candidate"],
            budget_row["maximum_overlay_gross"],
            budget_row["maximum_portfolio_gross"],
        )
        combined, allocated = allocations[key]
        portfolio_guard = (
            budget_row["maximum_portfolio_gross"]
            + lab["gross_drift_allowance"]
        )
        opportunity_guard = (
            budget_row["maximum_overlay_gross"]
            + lab["gross_drift_allowance"]
        )
        row = {
            "candidate": screened["candidate"],
            "spec": screened["spec"],
            "budget": budget_row,
            "combined": {},
            "opportunity_only_at_allocated_size": {},
            "wealth_ratio_vs_core": {},
        }
        print(
            f"exact finalist {number}/{len(ranked)} {screened['candidate']} "
            f"overlay={budget_row['maximum_overlay_gross']}",
            flush=True,
        )
        for scenario in SCENARIOS:
            name = scenario[0]
            combined_metric = diagnostic(
                replay(data, combined, scenario, portfolio_guard, guard)
            )
            opportunity_metric = diagnostic(
                replay(data, allocated, scenario, opportunity_guard, guard)
            )
            row["combined"][name] = combined_metric
            row["opportunity_only_at_allocated_size"][name] = opportunity_metric
            row["wealth_ratio_vs_core"][name] = wealth_ratio(
                combined_metric,
                report["core"]["scenarios"][name],
            )

        risk = lab["risk_constraints"]
        drawdown_checks = {
            name: row["combined"][name]["max_drawdown"] >= max(
                risk["historical_max_drawdown_floor"],
                report["core"]["scenarios"][name]["max_drawdown"]
                - risk["maximum_drawdown_deterioration_vs_core"],
            )
            for name, *_ in SCENARIOS
        }
        row["preliminary_gates"] = {
            "beats_core_terminal_wealth_in_every_scenario": all(
                ratio > 1.0 for ratio in row["wealth_ratio_vs_core"].values()
            ),
            "no_exact_ruin": all(
                not metric["ruin"] for metric in row["combined"].values()
            ),
            "drawdown_constraints": all(drawdown_checks.values()),
            "parameter_neighborhood": False,
            "independent_forward_paper": False,
        }
        row["drawdown_checks"] = drawdown_checks
        row["robust_wealth_score"] = float(
            min(row["wealth_ratio_vs_core"].values())
        )
        row["eligible_for_next_research_stage"] = all((
            row["preliminary_gates"]["beats_core_terminal_wealth_in_every_scenario"],
            row["preliminary_gates"]["no_exact_ruin"],
            row["preliminary_gates"]["drawdown_constraints"],
        ))
        report["exact_finalists"].append(row)
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    eligible = [
        row for row in report["exact_finalists"]
        if row["eligible_for_next_research_stage"]
    ]
    if eligible:
        selected = max(
            eligible,
            key=lambda row: (
                row["robust_wealth_score"],
                row["combined"]["base"]["terminal_wealth"],
            ),
        )
        report["selected_for_next_research_stage"] = {
            "candidate": selected["candidate"],
            "budget": selected["budget"],
            "robust_wealth_score": selected["robust_wealth_score"],
            "not_paper_approved": True,
        }
    report["status"] = "completed"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "selected": report["selected_for_next_research_stage"],
        "paper_promotion": report["paper_promotion"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
