from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from run_opportunity_lab_v1 import cap_gross, load_core_targets


START = "2021-01-01"
END = "2026-07-31 23:00"
THRESHOLDS = (0.04, 0.08, 0.15, 0.20, 0.30, 0.40)


def maximum_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def merge_short_gaps(active: pd.Series, hours: int = 24) -> pd.Series:
    values = active.astype(bool).to_numpy(copy=True)
    indexes = np.flatnonzero(values)
    for left, right in zip(indexes[:-1], indexes[1:]):
        if 1 < right - left <= hours + 1:
            values[left : right + 1] = True
    return pd.Series(values, index=active.index)


def independent_episodes(
    equity: pd.Series,
    allocated: pd.DataFrame,
    merge_gap_hours: int = 24,
) -> list[dict[str, object]]:
    active = merge_short_gaps(allocated.abs().sum(axis=1) > 1e-10, merge_gap_hours)
    starts = active & ~active.shift(1, fill_value=False)
    ends = active & ~active.shift(-1, fill_value=False)
    start_times = list(active.index[starts])
    end_times = list(active.index[ends])
    rows: list[dict[str, object]] = []
    for number, (start, end) in enumerate(zip(start_times, end_times), 1):
        start_at = max(equity.index[0], start - pd.Timedelta(hours=1))
        window = equity.loc[start_at:end]
        if len(window) < 2 or float(window.iloc[0]) <= 0.0:
            continue
        realized = float(window.iloc[-1] / window.iloc[0] - 1.0)
        peak = float(window.max() / window.iloc[0] - 1.0)
        trough = float(window.min() / window.iloc[0] - 1.0)
        rows.append({
            "id": number,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": round((end - start).total_seconds() / 86400.0, 2),
            "return": realized,
            "peak_return": peak,
            "worst_during_episode": trough,
        })
    return rows


def episode_summary(episodes: list[dict[str, object]]) -> dict[str, object]:
    returns = pd.Series([float(row["return"]) for row in episodes], dtype=float)
    peaks = pd.Series([float(row["peak_return"]) for row in episodes], dtype=float)
    return {
        "definition": (
            "One episode begins when the opportunity sleeve becomes active and ends "
            "when it becomes inactive; gaps up to 24h are merged. Episodes never overlap."
        ),
        "count": len(episodes),
        "positive_fraction": float((returns > 0).mean()) if len(returns) else 0.0,
        "median_return": float(returns.median()) if len(returns) else 0.0,
        "mean_return": float(returns.mean()) if len(returns) else 0.0,
        "best_realized_return": float(returns.max()) if len(returns) else 0.0,
        "worst_realized_return": float(returns.min()) if len(returns) else 0.0,
        "best_peak_return": float(peaks.max()) if len(peaks) else 0.0,
        "realized_counts": {
            f"{int(threshold * 100)}pct": int((returns >= threshold).sum())
            for threshold in THRESHOLDS
        },
        "peak_hit_counts": {
            f"{int(threshold * 100)}pct": int((peaks >= threshold).sum())
            for threshold in THRESHOLDS
        },
        "top_episodes": sorted(
            episodes, key=lambda row: float(row["return"]), reverse=True
        )[:20],
    }


def metric(result, allocated: pd.DataFrame) -> dict[str, object]:
    equity = result.equity.loc[START:END]
    episodes = independent_episodes(equity, allocated.loc[equity.index])
    return {
        "terminal_wealth": float(equity.iloc[-1]),
        "total_return": float(equity.iloc[-1] - 1.0),
        "max_drawdown": maximum_drawdown(equity),
        "ruin": bool(result.ruin),
        "episodes": episode_summary(episodes),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-project", type=Path, default=PROJECT)
    parser.add_argument(
        "--output", type=Path, default=PROJECT / "reports" / "v14_max_capture_search.json"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lab = json.loads((PROJECT / "config" / "opportunity_lab_v1.json").read_text())
    finalist = json.loads((PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text())
    base_config = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
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
        args.data_project / "reports" / "candidate_v13_pit_carry_core_targets.csv",
        finalist["target_cap"],
    )
    seed = StrategySpec(**next(
        row["spec"] for row in lab["seed_candidates"]
        if row["name"] == "impulse_18_trend_336"
    ))
    specs = {
        "center": seed,
        "trend_432h": replace(seed, trend_filter_hours=432),
        "threshold_1_5pct": replace(seed, threshold=0.015),
        "holding_120h": replace(seed, max_holding=120),
    }
    guards = {
        "defensive": {"threshold": 0.12, "multiplier": 0.40, "cooldown": 168},
        "v13": {"threshold": 0.15, "multiplier": 0.50, "cooldown": 336},
        "growth": {"threshold": 0.18, "multiplier": 0.60, "cooldown": 168},
    }
    budgets = (0.15, 0.225, 0.30, 0.375, 0.45, 0.525, 0.60)
    raw_targets = {name: build_targets(signal_data, spec) for name, spec in specs.items()}
    rows: list[dict[str, object]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for spec_name, spec in specs.items():
        for overlay in budgets:
            budget = OpportunityBudget(overlay, 1.35 + overlay)
            combined, allocated = additive_opportunity_targets(
                core_targets, raw_targets[spec_name], budget
            )
            for guard_name, guard in guards.items():
                print(f"{spec_name} overlay={overlay:.3f} guard={guard_name}", flush=True)
                result = exact_fast(
                    data,
                    combined,
                    cost_per_side=base_config["execution"]["base_cost_per_side"],
                    maintenance_equity_fraction=base_config["execution"]["maintenance_equity_fraction"],
                    gross_guard_cap=1.50 + overlay,
                    drawdown_guard_threshold=guard["threshold"],
                    drawdown_guard_multiplier=guard["multiplier"],
                    drawdown_guard_cooldown_hours=guard["cooldown"],
                )
                row = {
                    "spec_name": spec_name,
                    "spec": spec.to_dict(),
                    "overlay_gross": overlay,
                    "maximum_portfolio_gross": 1.35 + overlay,
                    "gross_guard_cap": 1.50 + overlay,
                    "guard_name": guard_name,
                    "guard": guard,
                    "base": metric(result, allocated),
                }
                rows.append(row)
                args.output.write_text(json.dumps({"status": "running", "rows": rows}, indent=2) + "\n")

    eligible = [
        row for row in rows
        if not row["base"]["ruin"] and row["base"]["max_drawdown"] >= -0.35
    ]
    ranked = sorted(
        eligible,
        key=lambda row: (
            row["base"]["terminal_wealth"],
            row["base"]["episodes"]["realized_counts"]["20pct"],
            row["base"]["episodes"]["realized_counts"]["8pct"],
        ),
        reverse=True,
    )
    selected = ranked[0]
    spec = StrategySpec(**selected["spec"])
    budget = OpportunityBudget(
        selected["overlay_gross"], selected["maximum_portfolio_gross"]
    )
    combined, allocated = additive_opportunity_targets(
        core_targets, raw_targets[selected["spec_name"]], budget
    )
    stress_scenarios = {
        "severe_cost": {"cost": 0.0012, "delay": 0, "debit": 1.0, "credit": 1.0},
        "delay_3h": {"cost": 0.0007, "delay": 2, "debit": 1.0, "credit": 1.0},
        "delay_6h": {"cost": 0.0007, "delay": 5, "debit": 1.0, "credit": 1.0},
        "adverse_funding": {"cost": 0.0007, "delay": 0, "debit": 2.0, "credit": 0.5},
        "severe_all": {"cost": 0.0012, "delay": 5, "debit": 2.0, "credit": 0.5},
    }
    selected["stress"] = {}
    guard = selected["guard"]
    for name, scenario in stress_scenarios.items():
        print(f"selected stress {name}", flush=True)
        result = exact_fast(
            data,
            combined.shift(scenario["delay"]).fillna(0.0),
            cost_per_side=scenario["cost"],
            maintenance_equity_fraction=base_config["execution"]["maintenance_equity_fraction"],
            gross_guard_cap=selected["gross_guard_cap"],
            funding_debit_multiplier=scenario["debit"],
            funding_credit_multiplier=scenario["credit"],
            drawdown_guard_threshold=guard["threshold"],
            drawdown_guard_multiplier=guard["multiplier"],
            drawdown_guard_cooldown_hours=guard["cooldown"],
        )
        selected["stress"][name] = metric(result, allocated)

    report = {
        "status": "completed",
        "objective": "maximum terminal compounded wealth; no monthly target or return ceiling",
        "selection_constraint": "base historical drawdown no worse than -35%; no exact ruin",
        "disclosure": "researched historical replay, not a pristine holdout and not a profit promise",
        "tested_count": len(rows),
        "eligible_count": len(eligible),
        "selected": selected,
        "leaderboard": ranked[:12],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "selected": {
            "spec": selected["spec_name"],
            "overlay": selected["overlay_gross"],
            "guard": selected["guard_name"],
            "terminal_wealth": selected["base"]["terminal_wealth"],
            "max_drawdown": selected["base"]["max_drawdown"],
            "episodes": selected["base"]["episodes"],
        }
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
