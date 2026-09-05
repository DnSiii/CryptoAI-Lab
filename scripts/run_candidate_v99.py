from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_r2 import V99R2ControlSpec, asymmetric_v99_targets_r2
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16


CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_asymmetric_validation.json"
DIAGNOSTICS_PATH = PROJECT / "reports" / "candidate_v99_asymmetric_diagnostics.csv"


def summary(equity: pd.Series) -> dict[str, float]:
    values = equity.dropna()
    if len(values) < 2:
        return {"return": 0.0, "cagr": 0.0, "max_drawdown": 0.0}
    total_return = float(values.iloc[-1] / values.iloc[0] - 1.0)
    elapsed_years = max(
        (values.index[-1] - values.index[0]).total_seconds() / (365.25 * 24 * 3600),
        1.0 / 365.25,
    )
    cagr = float((values.iloc[-1] / values.iloc[0]) ** (1.0 / elapsed_years) - 1.0)
    drawdown = values.div(values.cummax()).sub(1.0)
    return {
        "return": total_return,
        "cagr": cagr,
        "max_drawdown": float(drawdown.min()),
    }


def horizon_summary(equity: pd.Series, days: int) -> dict[str, float]:
    values = equity.dropna()
    cutoff = values.index[-1] - pd.Timedelta(days=days)
    window = values.loc[values.index >= cutoff]
    if len(window) < 2:
        return {"return": 0.0, "max_drawdown": 0.0}
    drawdown = window.div(window.cummax()).sub(1.0)
    return {
        "return": float(window.iloc[-1] / window.iloc[0] - 1.0),
        "max_drawdown": float(drawdown.min()),
    }


def daily_returns(equity: pd.Series) -> pd.Series:
    return equity.resample("1D").last().pct_change(fill_method=None).dropna()


def tail_and_capture(parent_equity: pd.Series, candidate_equity: pd.Series) -> dict[str, float]:
    parent = daily_returns(parent_equity)
    candidate = daily_returns(candidate_equity)
    aligned = pd.concat(
        [parent.rename("parent"), candidate.rename("candidate")],
        axis=1,
        join="inner",
    ).dropna()
    if aligned.empty:
        return {
            "parent_worst_day": 0.0,
            "candidate_worst_day": 0.0,
            "worst_day_improvement_fraction": 0.0,
            "parent_bottom10_mean": 0.0,
            "candidate_on_parent_bottom10_mean": 0.0,
            "bottom10_damage_improvement_fraction": 0.0,
            "top_winner_capture": 0.0,
        }
    parent_worst = float(aligned["parent"].min())
    candidate_worst = float(aligned["candidate"].min())
    if parent_worst < 0.0:
        improvement = 1.0 - abs(candidate_worst) / abs(parent_worst)
    else:
        improvement = 0.0

    bottom = aligned.nsmallest(min(10, len(aligned)), "parent")
    parent_bottom_mean = float(bottom["parent"].mean())
    candidate_bottom_mean = float(bottom["candidate"].mean())
    bottom_improvement = (
        1.0 - abs(candidate_bottom_mean) / abs(parent_bottom_mean)
        if parent_bottom_mean < 0.0
        else 0.0
    )
    winners = aligned.loc[aligned["parent"] > 0.0].nlargest(
        min(10, int((aligned["parent"] > 0.0).sum())),
        "parent",
    )
    winner_denominator = float(winners["parent"].sum()) if not winners.empty else 0.0
    winner_capture = (
        float(winners["candidate"].sum()) / winner_denominator
        if winner_denominator > 0.0
        else 0.0
    )
    return {
        "parent_worst_day": parent_worst,
        "candidate_worst_day": candidate_worst,
        "worst_day_improvement_fraction": float(improvement),
        "parent_bottom10_mean": parent_bottom_mean,
        "candidate_on_parent_bottom10_mean": candidate_bottom_mean,
        "bottom10_damage_improvement_fraction": float(bottom_improvement),
        "top_winner_capture": float(winner_capture),
    }


def control_activity(diagnostics: pd.DataFrame) -> dict[str, float]:
    rows = max(len(diagnostics), 1)
    elapsed_days = max(rows / 24.0, 1.0 / 24.0)
    risk = diagnostics["risk_factor"].astype(float)
    return {
        "stress_active_fraction": float((diagnostics["stress_factor"] < 0.999).mean()),
        "chop_active_fraction": float(diagnostics["chop_active"].astype(bool).mean()),
        "damage_active_fraction": float((diagnostics["damage_factor"] < 0.999).mean()),
        "risk_reduced_fraction": float((risk < 0.999).mean()),
        "risk_factor_changes_per_day": float(risk.ne(risk.shift(1)).sum() / elapsed_days),
        "chop_growth_blocks_total": float(diagnostics["chop_blocked_count"].sum()),
        "extension_growth_blocks_total": float(diagnostics["extension_blocked_count"].sum()),
        "clean_trend_fraction": float(diagnostics["clean_trend"].astype(bool).mean()),
    }


def daily_autopsy(
    parent_equity: pd.Series,
    candidate_equity: pd.Series,
    diagnostics: pd.DataFrame,
    limit: int = 15,
) -> dict[str, list[dict[str, object]]]:
    returns = pd.concat(
        [
            daily_returns(parent_equity).rename("parent_return"),
            daily_returns(candidate_equity).rename("candidate_return"),
        ],
        axis=1,
        join="inner",
    ).dropna()

    daily = pd.DataFrame(index=returns.index)
    daily["min_risk_factor"] = diagnostics["risk_factor"].resample("1D").min()
    daily["mean_risk_factor"] = diagnostics["risk_factor"].resample("1D").mean()
    daily["stress_hours"] = (
        diagnostics["stress_factor"].lt(0.999).astype(int).resample("1D").sum()
    )
    daily["damage_hours"] = (
        diagnostics["damage_factor"].lt(0.999).astype(int).resample("1D").sum()
    )
    daily["chop_hours"] = diagnostics["chop_active"].astype(int).resample("1D").sum()
    daily["clean_trend_hours"] = (
        diagnostics["clean_trend"].astype(int).resample("1D").sum()
    )
    daily["boost_hours"] = diagnostics["boost_ready"].astype(int).resample("1D").sum()
    daily["chop_blocks"] = diagnostics["chop_blocked_count"].resample("1D").sum()
    daily["extension_blocks"] = (
        diagnostics["extension_blocked_count"].resample("1D").sum()
    )
    daily["max_stress_score"] = diagnostics["stress_score"].resample("1D").max()
    daily["max_loss_fraction"] = diagnostics["smoothed_loss_fraction"].resample("1D").max()

    combined = returns.join(daily, how="left").fillna(0.0)

    def rows(frame: pd.DataFrame) -> list[dict[str, object]]:
        output: list[dict[str, object]] = []
        for timestamp, row in frame.iterrows():
            output.append(
                {
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "parent_return": float(row["parent_return"]),
                    "candidate_return": float(row["candidate_return"]),
                    "min_risk_factor": float(row["min_risk_factor"]),
                    "mean_risk_factor": float(row["mean_risk_factor"]),
                    "stress_hours": int(row["stress_hours"]),
                    "damage_hours": int(row["damage_hours"]),
                    "chop_hours": int(row["chop_hours"]),
                    "clean_trend_hours": int(row["clean_trend_hours"]),
                    "boost_hours": int(row["boost_hours"]),
                    "chop_blocks": int(row["chop_blocks"]),
                    "extension_blocks": int(row["extension_blocks"]),
                    "max_stress_score": int(row["max_stress_score"]),
                    "max_loss_fraction": float(row["max_loss_fraction"]),
                }
            )
        return output

    return {
        "candidate_worst_days": rows(combined.nsmallest(limit, "candidate_return")),
        "parent_worst_days": rows(combined.nsmallest(limit, "parent_return")),
        "parent_best_days": rows(combined.nlargest(limit, "parent_return")),
    }


def run_exact(data, targets, execution: dict, guard: dict, cost: float):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=guard["gross_drift_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads(
        (PROJECT / "config" / candidate["parent_candidate_config"]).read_text(
            encoding="utf-8"
        )
    )
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V99 validation must remain orderless")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    targets, diagnostics = asymmetric_v99_targets_r2(
        data,
        parent_targets,
        proxy,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R2ControlSpec(**candidate["r2_control"]),
    )
    guard = candidate["circuit_breaker"]
    base = run_exact(
        data,
        targets,
        execution,
        guard,
        execution["base_cost_per_side"],
    )
    severe = run_exact(
        data,
        targets,
        execution,
        guard,
        execution["severe_cost_per_side"],
    )
    delayed = run_exact(
        data,
        targets.shift(3).fillna(0.0),
        execution,
        guard,
        execution["base_cost_per_side"],
    )

    required_days = [int(value) for value in candidate["research_gate"]["required_horizons_days"]]
    horizons = {
        str(days): {
            "v99": horizon_summary(base.equity, days),
            "parent": horizon_summary(parent_result.equity, days),
        }
        for days in required_days
    }
    base_summary = summary(base.equity)
    parent_summary = summary(parent_result.equity)
    severe_summary = summary(severe.equity)
    delayed_summary = summary(delayed.equity)
    tail = tail_and_capture(parent_result.equity, base.equity)
    activity = control_activity(diagnostics)
    autopsy = daily_autopsy(parent_result.equity, base.equity, diagnostics)

    gate_config = candidate["research_gate"]
    parent_drawdown = abs(parent_summary["max_drawdown"])
    v99_drawdown = abs(base_summary["max_drawdown"])
    drawdown_improvement = (
        1.0 - v99_drawdown / parent_drawdown
        if parent_drawdown > 0.0
        else 0.0
    )
    gate = {
        "all_required_horizons_positive": all(
            horizons[str(days)]["v99"]["return"] > 0.0 for days in required_days
        ),
        "full_return_beats_parent": base_summary["return"] > parent_summary["return"],
        "drawdown_improves_by_required_fraction": drawdown_improvement
        >= float(gate_config["max_drawdown_improvement_fraction"]),
        "worst_day_improves_by_required_fraction": tail[
            "worst_day_improvement_fraction"
        ]
        >= float(gate_config["worst_day_loss_improvement_fraction"]),
        "top_winner_capture_preserved": tail["top_winner_capture"]
        >= float(gate_config["top_winner_capture_minimum"]),
        "severe_cost_positive": severe_summary["return"] > 0.0,
        "delay_3h_positive": delayed_summary["return"] > 0.0,
        "no_exact_ruin": not (base.ruin or severe.ruin or delayed.ruin),
    }

    report = {
        "candidate": candidate,
        "parent": parent["name"],
        "historical_validation_disclosure": (
            "The historical interval has been used iteratively for CryptoAI research. "
            "V99 is therefore judged as a challenger, not as a pristine holdout. "
            "Its independent forward paper boundary remains mandatory."
        ),
        "v99": base_summary,
        "parent_summary": parent_summary,
        "severe_cost": severe_summary,
        "delay_3h": delayed_summary,
        "horizons": horizons,
        "tail_and_winner_capture": tail,
        "control_activity": activity,
        "daily_autopsy": autopsy,
        "drawdown_improvement_fraction": float(drawdown_improvement),
        "funding_quarantined_symbols": quarantined,
        "gate": gate,
        "strict_research_gate_passed": all(gate.values()),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    diagnostics.to_csv(DIAGNOSTICS_PATH, index_label="timestamp")
    print(
        json.dumps(
            {
                "v99": base_summary,
                "parent": parent_summary,
                "tail": tail,
                "control_activity": activity,
                "candidate_worst_days": autopsy["candidate_worst_days"][:5],
                "drawdown_improvement_fraction": drawdown_improvement,
                "gate": gate,
                "passed": all(gate.values()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
