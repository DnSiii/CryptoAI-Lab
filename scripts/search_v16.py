from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v16 import (
    ConvexCaptureSpec,
    combine_convex_with_core,
    convex_capture_targets,
)
from paper_once_v13 import cap_targets
from run_final_candidate import build_candidate


REPORT_PATH = PROJECT / "reports" / "v16_research_gate.json"
START = "2021-01-01"


def maximum_drawdown(equity: pd.Series) -> float:
    equity = equity.dropna()
    return float(equity.div(equity.cummax()).sub(1.0).min()) if len(equity) else 0.0


def period_metrics(equity: pd.Series, start: str, end: str | None = None) -> dict:
    selected = equity.loc[start:end].dropna()
    if len(selected) < 2:
        return {"return": 0.0, "cagr": 0.0, "max_drawdown": 0.0}
    selected = selected / selected.iloc[0]
    hours = max((selected.index[-1] - selected.index[0]).total_seconds() / 3600, 1.0)
    total = float(selected.iloc[-1] - 1.0)
    cagr = float(selected.iloc[-1] ** ((365.25 * 24) / hours) - 1.0)
    daily = selected.resample("D").last().pct_change().dropna()
    monthly = selected.resample("ME").last().pct_change().dropna()
    positive = daily.clip(lower=0.0)
    best = daily.nlargest(min(3, len(daily)))
    without_best = daily.drop(index=best.index[:1])
    rolling_90 = selected.resample("ME").last().pct_change(3).dropna()
    return {
        "return": total,
        "cagr": cagr,
        "max_drawdown": maximum_drawdown(selected),
        "positive_month_ratio": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
        "positive_rolling_90d_ratio": float((rolling_90 > 0.0).mean()) if len(rolling_90) else 0.0,
        "without_best_day_return": float((1.0 + without_best).prod() - 1.0),
        "top3_positive_day_share": (
            float(best.clip(lower=0.0).sum() / positive.sum())
            if positive.sum() > 0.0 else 1.0
        ),
        "days_over_3pct": int((daily >= 0.03).sum()),
        "days_over_5pct": int((daily >= 0.05).sum()),
        "days_over_8pct": int((daily >= 0.08).sum()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "days": int(len(daily)),
    }


def profile(equity: pd.Series, latest: pd.Timestamp) -> dict:
    end = latest.isoformat()
    return {
        "full": period_metrics(equity, START, end),
        "old": period_metrics(equity, "2021-01-01", "2023-12-31 23:00"),
        "validation": period_metrics(equity, "2024-01-01", "2024-12-31 23:00"),
        "recent": period_metrics(equity, "2025-01-01", end),
        "current": period_metrics(equity, "2026-01-01", end),
    }


def robustness_gate(row: dict, benchmark_recent_cagr: float) -> dict[str, bool]:
    p = row["profile"]
    return {
        "positive_old_market_regimes": p["old"]["return"] > 0.0,
        "positive_2024_validation": p["validation"]["return"] > 0.0,
        "positive_2025_plus_recent": p["recent"]["return"] > 0.0,
        "positive_2026_recent": p["current"]["return"] > 0.0,
        "recent_cagr_beats_existing_benchmark": p["recent"]["cagr"] > benchmark_recent_cagr,
        "full_drawdown_no_worse_than_30pct": p["full"]["max_drawdown"] >= -0.30,
        "recent_drawdown_no_worse_than_20pct": p["recent"]["max_drawdown"] >= -0.20,
        "current_drawdown_no_worse_than_15pct": p["current"]["max_drawdown"] >= -0.15,
        "recent_profitable_without_best_day": p["recent"]["without_best_day_return"] > 0.0,
        "current_profitable_without_best_day": p["current"]["without_best_day_return"] > 0.0,
        "recent_top3_days_below_55pct_of_positive_pnl": p["recent"]["top3_positive_day_share"] < 0.55,
        "recent_majority_positive_rolling_90d": p["recent"]["positive_rolling_90d_ratio"] >= 0.55,
        "recent_majority_positive_months": p["recent"]["positive_month_ratio"] >= 0.55,
    }


def score_row(row: dict) -> float:
    p = row["profile"]
    recent, current, full = p["recent"], p["current"], p["full"]
    large_day_score = (
        current["days_over_3pct"]
        + 2.0 * current["days_over_5pct"]
        + 4.0 * current["days_over_8pct"]
    ) / max(current["days"], 1)
    return float(
        0.42 * recent["cagr"]
        + 0.38 * current["cagr"]
        + 0.20 * full["cagr"]
        + 2.0 * large_day_score
        - 0.30 * abs(recent["max_drawdown"])
        - 0.20 * recent["top3_positive_day_share"]
    )


def main() -> None:
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data, core_targets, _, _ = build_candidate(base_config)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    execution = base_config["execution"]
    latest = data.close.index[-1]

    core_result = screen(data, core_targets, execution["base_cost_per_side"])
    v14_config = json.loads(
        (PROJECT / "config" / "candidate_v14_max_capture.json").read_text()
    )
    v14_raw = build_targets(
        signal_data, StrategySpec(**v14_config["opportunity"]["spec"])
    )
    v14_targets, _ = additive_opportunity_targets(
        core_targets,
        v14_raw,
        OpportunityBudget(
            v14_config["allocation"]["maximum_overlay_gross"],
            v14_config["allocation"]["maximum_portfolio_gross"],
        ),
    )
    v14_result = screen(data, v14_targets, execution["base_cost_per_side"])
    benchmarks = {
        "v13_core": profile(core_result.equity, latest),
        "v14": profile(v14_result.equity, latest),
    }
    benchmark_recent_cagr = max(
        benchmarks["v13_core"]["recent"]["cagr"],
        benchmarks["v14"]["recent"]["cagr"],
    )

    center = ConvexCaptureSpec()
    specs = {
        "balanced": center,
        "fast_selective": replace(
            center,
            fast_lookback=12,
            slow_lookback=48,
            top_n=1,
            fast_threshold=0.010,
            slow_threshold=0.020,
            fast_volume_multiple=1.75,
            slow_volume_multiple=1.40,
            fast_weight=0.55,
            slow_weight=0.30,
            trend_weight=0.15,
            fast_max_holding_hours=72,
            slow_max_holding_hours=168,
        ),
        "trend_convex": replace(
            center,
            fast_lookback=24,
            slow_lookback=168,
            fast_threshold=0.015,
            slow_threshold=0.035,
            fast_volume_multiple=1.35,
            slow_volume_multiple=1.15,
            fast_weight=0.35,
            slow_weight=0.30,
            trend_weight=0.35,
            trailing_stop=0.18,
            slow_max_holding_hours=336,
        ),
        "high_conviction": replace(
            center,
            top_n=1,
            fast_threshold=0.018,
            slow_threshold=0.035,
            fast_volume_multiple=2.0,
            slow_volume_multiple=1.5,
            aligned_multiplier=1.50,
            countertrend_multiplier=0.20,
            minimum_conviction=0.45,
            maximum_conviction=1.60,
        ),
    }
    generated = {
        name: convex_capture_targets(signal_data, spec)[0]
        for name, spec in specs.items()
    }
    rows: list[dict[str, object]] = []
    for name, spec in specs.items():
        for core_fraction in (0.15, 0.30, 0.45):
            for maximum_gross in (1.35, 1.60, 1.85):
                targets, allocated = combine_convex_with_core(
                    core_targets,
                    generated[name],
                    core_fraction=core_fraction,
                    maximum_portfolio_gross=maximum_gross,
                )
                result = screen(data, targets, execution["base_cost_per_side"])
                row = {
                    "name": name,
                    "spec": spec.to_dict(),
                    "core_fraction": core_fraction,
                    "maximum_portfolio_gross": maximum_gross,
                    "allocated_opportunity_average_gross": float(
                        allocated.abs().sum(axis=1).mean()
                    ),
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    ranked = sorted(rows, key=lambda item: item["score"], reverse=True)
    exact_rows: list[dict[str, object]] = []
    for row in ranked[:6]:
        spec = ConvexCaptureSpec(**row["spec"])
        opportunity, _, _ = convex_capture_targets(signal_data, spec)
        targets, _ = combine_convex_with_core(
            core_targets,
            opportunity,
            core_fraction=float(row["core_fraction"]),
            maximum_portfolio_gross=float(row["maximum_portfolio_gross"]),
        )
        exact_base = exact_fast(
            data,
            targets,
            cost_per_side=execution["base_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=0.12,
            drawdown_guard_multiplier=0.35,
            drawdown_guard_cooldown_hours=168,
        )
        severe = exact_fast(
            data,
            targets,
            cost_per_side=execution["severe_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=0.12,
            drawdown_guard_multiplier=0.35,
            drawdown_guard_cooldown_hours=168,
        )
        delayed = exact_fast(
            data,
            targets.shift(2).fillna(0.0),
            cost_per_side=execution["base_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=0.12,
            drawdown_guard_multiplier=0.35,
            drawdown_guard_cooldown_hours=168,
        )
        checked = {**row, "profile": profile(exact_base.equity, latest)}
        checked["gate"] = robustness_gate(checked, benchmark_recent_cagr)
        checked["stress"] = {
            "severe_cost": profile(severe.equity, latest),
            "delay_3h": profile(delayed.equity, latest),
        }
        checked["exact_gate"] = {
            **checked["gate"],
            "severe_cost_recent_positive": checked["stress"]["severe_cost"]["recent"]["return"] > 0.0,
            "severe_cost_current_positive": checked["stress"]["severe_cost"]["current"]["return"] > 0.0,
            "delay_3h_recent_positive": checked["stress"]["delay_3h"]["recent"]["return"] > 0.0,
            "delay_3h_current_positive": checked["stress"]["delay_3h"]["current"]["return"] > 0.0,
            "no_ruin": not (exact_base.ruin or severe.ruin or delayed.ruin),
        }
        checked["exact_gate_passed"] = all(checked["exact_gate"].values())
        checked["score"] = score_row(checked)
        exact_rows.append(checked)

    exact_ranked = sorted(exact_rows, key=lambda item: item["score"], reverse=True)
    promoted = next((row for row in exact_ranked if row["exact_gate_passed"]), None)
    report = {
        "status": "promoted" if promoted else "rejected",
        "objective": "maximize recent-weighted compounded ROI and frequency of large days without dependence on the best day",
        "latest_data_timestamp": latest.isoformat(),
        "data_priority": "2025+ and 2026 receive the largest score weight; 2021-2024 are robustness regimes",
        "anti_overfit_rule": "paper promotion is forbidden unless exact, cost-stress and delay gates pass and recent returns remain positive after deleting the best day",
        "benchmarks": benchmarks,
        "tested_configurations": len(rows),
        "screen_passed": sum(bool(row["screen_gate_passed"]) for row in rows),
        "promoted": promoted,
        "exact_finalists": exact_ranked,
        "screen_leaderboard": ranked[:12],
        "real_orders": False,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "latest_data_timestamp": report["latest_data_timestamp"],
        "tested_configurations": report["tested_configurations"],
        "screen_passed": report["screen_passed"],
        "promoted": promoted,
    }, indent=2))


if __name__ == "__main__":
    main()
