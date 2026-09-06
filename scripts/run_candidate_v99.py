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
from cryptoai_v13.v99_r3 import V99R3ControlSpec, asymmetric_v99_targets_r3
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
    return {"return": total_return, "cagr": cagr, "max_drawdown": float(drawdown.min())}


def window_summary(values: pd.Series) -> dict[str, float]:
    values = values.dropna()
    if len(values) < 2:
        return {"return": 0.0, "max_drawdown": 0.0}
    drawdown = values.div(values.cummax()).sub(1.0)
    return {
        "return": float(values.iloc[-1] / values.iloc[0] - 1.0),
        "max_drawdown": float(drawdown.min()),
    }


def horizon_summary(equity: pd.Series, days: int) -> dict[str, float]:
    values = equity.dropna()
    cutoff = values.index[-1] - pd.Timedelta(days=days)
    return window_summary(values.loc[values.index >= cutoff])


def calendar_year_summaries(equity: pd.Series) -> dict[str, dict[str, float]]:
    values = equity.dropna()
    output: dict[str, dict[str, float]] = {}
    for year, frame in values.groupby(values.index.year):
        if len(frame) >= 2:
            output[str(int(year))] = window_summary(frame)
    return output


def daily_returns(equity: pd.Series) -> pd.Series:
    return equity.resample("1D").last().pct_change(fill_method=None).dropna()


def rolling_robustness(
    parent_equity: pd.Series,
    candidate_equity: pd.Series,
    days: int,
) -> dict[str, float]:
    parent = parent_equity.resample("1D").last().dropna()
    candidate = candidate_equity.resample("1D").last().dropna()
    aligned = pd.concat([parent.rename("parent"), candidate.rename("candidate")], axis=1).dropna()
    if len(aligned) <= days:
        return {"samples": 0.0, "candidate_positive_fraction": 0.0, "candidate_beats_parent_fraction": 0.0}
    parent_return = aligned["parent"].div(aligned["parent"].shift(days)).sub(1.0)
    candidate_return = aligned["candidate"].div(aligned["candidate"].shift(days)).sub(1.0)
    frame = pd.concat([parent_return.rename("parent"), candidate_return.rename("candidate")], axis=1).dropna()
    return {
        "samples": float(len(frame)),
        "candidate_positive_fraction": float(frame["candidate"].gt(0.0).mean()),
        "parent_positive_fraction": float(frame["parent"].gt(0.0).mean()),
        "candidate_beats_parent_fraction": float(frame["candidate"].gt(frame["parent"]).mean()),
        "median_candidate_return": float(frame["candidate"].median()),
        "median_parent_return": float(frame["parent"].median()),
    }


def tail_and_capture(parent_equity: pd.Series, candidate_equity: pd.Series) -> dict[str, float]:
    parent = daily_returns(parent_equity)
    candidate = daily_returns(candidate_equity)
    aligned = pd.concat([parent.rename("parent"), candidate.rename("candidate")], axis=1, join="inner").dropna()
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
    worst_improvement = 1.0 - abs(candidate_worst) / abs(parent_worst) if parent_worst < 0.0 else 0.0
    bottom = aligned.nsmallest(min(10, len(aligned)), "parent")
    parent_bottom_mean = float(bottom["parent"].mean())
    candidate_bottom_mean = float(bottom["candidate"].mean())
    bottom_improvement = (
        1.0 - abs(candidate_bottom_mean) / abs(parent_bottom_mean)
        if parent_bottom_mean < 0.0
        else 0.0
    )
    winners = aligned.loc[aligned["parent"] > 0.0].nlargest(
        min(10, int((aligned["parent"] > 0.0).sum())), "parent"
    )
    denominator = float(winners["parent"].sum()) if not winners.empty else 0.0
    capture = float(winners["candidate"].sum()) / denominator if denominator > 0.0 else 0.0
    return {
        "parent_worst_day": parent_worst,
        "candidate_worst_day": candidate_worst,
        "worst_day_improvement_fraction": float(worst_improvement),
        "parent_bottom10_mean": parent_bottom_mean,
        "candidate_on_parent_bottom10_mean": candidate_bottom_mean,
        "bottom10_damage_improvement_fraction": float(bottom_improvement),
        "top_winner_capture": float(capture),
    }


def control_activity(diagnostics: pd.DataFrame) -> dict[str, float]:
    rows = max(len(diagnostics), 1)
    elapsed_days = max(rows / 24.0, 1.0 / 24.0)
    risk = diagnostics["risk_factor"].astype(float)
    return {
        "stress_active_fraction": float((diagnostics["stress_factor"] < 0.999).mean()),
        "long_stress_fraction": float((diagnostics["long_stress_factor"] < 0.999).mean()),
        "short_stress_fraction": float((diagnostics["short_stress_factor"] < 0.999).mean()),
        "chop_active_fraction": float(diagnostics["chop_active"].astype(bool).mean()),
        "damage_active_fraction": float((diagnostics["damage_factor"] < 0.999).mean()),
        "risk_reduced_fraction": float((risk < 0.999).mean()),
        "risk_factor_changes_per_day": float(risk.ne(risk.shift(1)).sum() / elapsed_days),
        "chop_growth_blocks_total": float(diagnostics["chop_blocked_count"].sum()),
        "extension_growth_blocks_total": float(diagnostics["extension_blocked_count"].sum()),
        "clean_trend_fraction": float(diagnostics["clean_trend"].astype(bool).mean()),
    }


def daily_autopsy(parent_equity: pd.Series, candidate_equity: pd.Series, diagnostics: pd.DataFrame, limit: int = 15):
    returns = pd.concat(
        [daily_returns(parent_equity).rename("parent_return"), daily_returns(candidate_equity).rename("candidate_return")],
        axis=1,
        join="inner",
    ).dropna()
    daily = pd.DataFrame(index=returns.index)
    daily["min_risk_factor"] = diagnostics["risk_factor"].resample("1D").min()
    daily["mean_risk_factor"] = diagnostics["risk_factor"].resample("1D").mean()
    daily["stress_hours"] = diagnostics["stress_factor"].lt(0.999).astype(int).resample("1D").sum()
    daily["long_stress_hours"] = diagnostics["long_stress_factor"].lt(0.999).astype(int).resample("1D").sum()
    daily["short_stress_hours"] = diagnostics["short_stress_factor"].lt(0.999).astype(int).resample("1D").sum()
    daily["damage_hours"] = diagnostics["damage_factor"].lt(0.999).astype(int).resample("1D").sum()
    daily["chop_hours"] = diagnostics["chop_active"].astype(int).resample("1D").sum()
    daily["clean_trend_hours"] = diagnostics["clean_trend"].astype(int).resample("1D").sum()
    daily["boost_hours"] = diagnostics["boost_ready"].astype(int).resample("1D").sum()
    daily["chop_blocks"] = diagnostics["chop_blocked_count"].resample("1D").sum()
    daily["extension_blocks"] = diagnostics["extension_blocked_count"].resample("1D").sum()
    daily["max_stress_score"] = diagnostics["stress_score"].resample("1D").max()
    daily["max_loss_fraction"] = diagnostics["smoothed_loss_fraction"].resample("1D").max()
    combined = returns.join(daily, how="left").fillna(0.0)

    def rows(frame: pd.DataFrame):
        return [
            {
                "date": timestamp.strftime("%Y-%m-%d"),
                **{key: (int(value) if key.endswith("hours") or key.endswith("blocks") or key == "max_stress_score" else float(value)) for key, value in row.items()},
            }
            for timestamp, row in frame.iterrows()
        ]

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


def relative_margin(candidate_return: float, parent_return: float) -> float:
    if parent_return > 0.0:
        return candidate_return / parent_return - 1.0
    return candidate_return - parent_return


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V99 validation must remain orderless")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    targets, diagnostics = asymmetric_v99_targets_r3(
        data,
        parent_targets,
        proxy,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R3ControlSpec(**candidate["r3_control"]),
    )
    guard = candidate["circuit_breaker"]
    base = run_exact(data, targets, execution, guard, execution["base_cost_per_side"])
    severe = run_exact(data, targets, execution, guard, execution["severe_cost_per_side"])
    delayed = run_exact(data, targets.shift(3).fillna(0.0), execution, guard, execution["base_cost_per_side"])
    parent_severe = run_exact(data, parent_targets, execution, guard, execution["severe_cost_per_side"])
    parent_delayed = run_exact(data, parent_targets.shift(3).fillna(0.0), execution, guard, execution["base_cost_per_side"])

    gate_config = candidate["research_gate"]
    required_days = [int(value) for value in gate_config["required_horizons_days"]]
    anti_days = [int(value) for value in gate_config["anti_overfit_horizons_days"]]
    horizons = {
        str(days): {"v99": horizon_summary(base.equity, days), "parent": horizon_summary(parent_result.equity, days)}
        for days in required_days
    }
    anti_horizons = {
        str(days): {"v99": horizon_summary(base.equity, days), "parent": horizon_summary(parent_result.equity, days)}
        for days in anti_days
    }
    rolling = {
        str(days): rolling_robustness(parent_result.equity, base.equity, days)
        for days in anti_days
    }

    base_summary = summary(base.equity)
    parent_summary = summary(parent_result.equity)
    severe_summary = summary(severe.equity)
    parent_severe_summary = summary(parent_severe.equity)
    delayed_summary = summary(delayed.equity)
    parent_delayed_summary = summary(parent_delayed.equity)
    tail = tail_and_capture(parent_result.equity, base.equity)
    activity = control_activity(diagnostics)
    autopsy = daily_autopsy(parent_result.equity, base.equity, diagnostics)
    candidate_years = calendar_year_summaries(base.equity)
    parent_years = calendar_year_summaries(parent_result.equity)
    common_years = sorted(set(candidate_years) & set(parent_years))
    year_beats = [candidate_years[y]["return"] > parent_years[y]["return"] for y in common_years]
    year_beat_fraction = float(sum(year_beats) / len(year_beats)) if year_beats else 0.0

    parent_drawdown = abs(parent_summary["max_drawdown"])
    v99_drawdown = abs(base_summary["max_drawdown"])
    drawdown_improvement = 1.0 - v99_drawdown / parent_drawdown if parent_drawdown > 0.0 else 0.0
    required_margin = float(gate_config["required_horizon_return_margin"])
    required_dd_ratio = float(gate_config["required_horizon_drawdown_ratio_max"])
    required_return_beats = {
        str(days): relative_margin(horizons[str(days)]["v99"]["return"], horizons[str(days)]["parent"]["return"]) >= required_margin
        for days in required_days
    }
    required_dd_beats = {
        str(days): abs(horizons[str(days)]["v99"]["max_drawdown"]) <= abs(horizons[str(days)]["parent"]["max_drawdown"]) * required_dd_ratio + 1e-12
        for days in required_days
    }
    anti_recent_beats = [anti_horizons[str(days)]["v99"]["return"] > anti_horizons[str(days)]["parent"]["return"] for days in anti_days]
    anti_recent_beat_fraction = float(sum(anti_recent_beats) / len(anti_recent_beats)) if anti_recent_beats else 0.0
    rolling_beat_fraction = float(sum(value["candidate_beats_parent_fraction"] for value in rolling.values()) / len(rolling)) if rolling else 0.0

    gate = {
        "all_required_horizons_positive": all(horizons[str(days)]["v99"]["return"] > 0.0 for days in required_days),
        "all_required_horizons_beat_parent_with_margin": all(required_return_beats.values()),
        "all_required_horizons_drawdown_no_worse": all(required_dd_beats.values()),
        "full_return_beats_parent_with_margin": relative_margin(base_summary["return"], parent_summary["return"]) >= float(gate_config["full_return_margin"]),
        "drawdown_improves_by_required_fraction": drawdown_improvement >= float(gate_config["max_drawdown_improvement_fraction"]),
        "worst_day_improves_by_required_fraction": tail["worst_day_improvement_fraction"] >= float(gate_config["worst_day_loss_improvement_fraction"]),
        "bottom10_improves_by_required_fraction": tail["bottom10_damage_improvement_fraction"] >= float(gate_config["bottom10_damage_improvement_fraction"]),
        "top_winner_capture_preserved": tail["top_winner_capture"] >= float(gate_config["top_winner_capture_minimum"]),
        "anti_overfit_recent_horizons_broadly_beat_parent": anti_recent_beat_fraction >= float(gate_config["anti_overfit_parent_beat_fraction_minimum"]),
        "rolling_windows_broadly_beat_parent": rolling_beat_fraction >= float(gate_config["anti_overfit_parent_beat_fraction_minimum"]),
        "calendar_years_broadly_beat_parent": year_beat_fraction >= float(gate_config["calendar_year_parent_beat_fraction_minimum"]),
        "severe_cost_beats_parent": severe_summary["return"] > parent_severe_summary["return"],
        "delay_3h_beats_parent": delayed_summary["return"] > parent_delayed_summary["return"],
        "no_exact_ruin": not (base.ruin or severe.ruin or delayed.ruin),
    }

    report = {
        "candidate": candidate,
        "parent": parent["name"],
        "historical_validation_disclosure": (
            "The requested recent horizons and much of the historical interval have been seen during iterative CryptoAI research. "
            "R3 therefore adds deliberately non-target horizons, rolling windows and calendar-year slices; these reduce but do not eliminate overfitting risk. Independent forward paper remains mandatory."
        ),
        "v99": base_summary,
        "parent_summary": parent_summary,
        "severe_cost": {"v99": severe_summary, "parent": parent_severe_summary},
        "delay_3h": {"v99": delayed_summary, "parent": parent_delayed_summary},
        "horizons": horizons,
        "required_horizon_return_beats": required_return_beats,
        "required_horizon_drawdown_beats": required_dd_beats,
        "anti_overfit_horizons": anti_horizons,
        "anti_overfit_recent_beat_fraction": anti_recent_beat_fraction,
        "rolling_robustness": rolling,
        "rolling_average_parent_beat_fraction": rolling_beat_fraction,
        "calendar_years": {"v99": candidate_years, "parent": parent_years, "parent_beat_fraction": year_beat_fraction},
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
    print(json.dumps({
        "v99": base_summary,
        "parent": parent_summary,
        "horizons": horizons,
        "anti_overfit_recent_beat_fraction": anti_recent_beat_fraction,
        "rolling_average_parent_beat_fraction": rolling_beat_fraction,
        "calendar_year_parent_beat_fraction": year_beat_fraction,
        "tail": tail,
        "severe_cost": {"v99": severe_summary, "parent": parent_severe_summary},
        "delay_3h": {"v99": delayed_summary, "parent": parent_delayed_summary},
        "candidate_worst_days": autopsy["candidate_worst_days"][:5],
        "drawdown_improvement_fraction": drawdown_improvement,
        "gate": gate,
        "passed": all(gate.values()),
    }, indent=2))


if __name__ == "__main__":
    main()
