from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import multihorizon_two_sleeve_targets
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.v99 import V99AsymmetricSpec, _cap_gross
from cryptoai_v13.v99_r4 import V99R4ControlSpec, _sparse_side_shock
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import calendar_year_summaries, horizon_summary, rolling_robustness, summary, tail_and_capture

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r11_adaptive_sleeve_study.json"

# Deliberately broad multi-horizon allocator. It is not keyed to 7/30/90/180/365
# approval windows; it averages votes across short, medium and long regimes.
ALLOCATOR_WINDOWS = (45, 60, 90, 120, 180, 240)
WEIGHT_FAMILY = [
    (0.65, 0.20),
    (0.75, 0.25),
    (0.85, 0.30),
]
FAST_POLICY = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6}


def replay(data, targets, execution, gross_cap, cost):
    return exact_fast(
        data, targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
    )


def evaluate(equity, parent_equity, required, anti):
    full = summary(equity)
    pfull = summary(parent_equity)
    requested = {str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)} for d in required}
    antih = {str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)} for d in anti}
    rolling = {str(d): rolling_robustness(parent_equity, equity, d) for d in anti}
    years = calendar_year_summaries(equity)
    pyears = calendar_year_summaries(parent_equity)
    common = sorted(set(years) & set(pyears))
    return {
        "full": full,
        "full_wealth_ratio_to_parent": (1 + full["return"]) / (1 + pfull["return"]),
        "full_drawdown_improvement_fraction": 1 - abs(full["max_drawdown"]) / abs(pfull["max_drawdown"]),
        "requested": requested,
        "anti_overfit": antih,
        "anti_overfit_beat_fraction": sum(antih[str(d)]["v99"]["return"] > antih[str(d)]["parent"]["return"] for d in anti) / len(anti),
        "rolling_average_parent_beat_fraction": sum(v["candidate_beats_parent_fraction"] for v in rolling.values()) / len(rolling),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(years[y]["return"] > pyears[y]["return"] for y in common) / max(1, len(common)),
        "tail": tail_and_capture(parent_equity, equity),
    }


def score(r):
    t = r["tail"]
    requested = r["requested"]
    # Selection does not reward requested-window return size. It only adds a
    # modest penalty for being materially worse in risk on a majority of them.
    dd_not_worse = sum(
        abs(v["v99"]["max_drawdown"]) <= abs(v["parent"]["max_drawdown"]) * 1.10
        for v in requested.values()
    ) / len(requested)
    return (
        2.5 * r["full_wealth_ratio_to_parent"]
        + 3.0 * r["full_drawdown_improvement_fraction"]
        + 1.25 * r["anti_overfit_beat_fraction"]
        + 1.25 * r["rolling_average_parent_beat_fraction"]
        + 1.25 * r["calendar_year_beat_fraction"]
        + max(-0.75, min(0.75, t["worst_day_improvement_fraction"]))
        + max(-0.75, min(0.75, t["bottom10_damage_improvement_fraction"]))
        + min(1.2, t["top_winner_capture"])
        + min(0.75, max(-0.75, r["severe_wealth_ratio_to_parent"] - 1.0))
        + 0.5 * dd_not_worse
    )


def main():
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R11 is paper-only research")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    spec = V99AsymmetricSpec(**candidate["asymmetric_overlay"])
    control = V99R4ControlSpec(**candidate["r4_control"])
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    r5_targets, diag = asymmetric_v99_targets_r5(data, parent_targets, proxy, spec, control)

    # R10's robust tail variant: four-hour routine persistence, current stress
    # and sparse synchronized portfolio-side damage act immediately.
    routine = r5_targets.shift(4).fillna(0.0)
    shock_long, shock_short, _ = _sparse_side_shock(data.close, parent_targets, control)
    long_now = pd.concat([diag["long_risk_factor"].astype(float), shock_long], axis=1).min(axis=1)
    short_now = pd.concat([diag["short_risk_factor"].astype(float), shock_short], axis=1).min(axis=1)
    persistent = routine.clip(lower=0.0).mul(long_now, axis=0) + routine.clip(upper=0.0).mul(short_now, axis=0)
    persistent = _cap_gross(persistent, spec.maximum_gross)

    base_cost = execution["base_cost_per_side"]
    parent_proxy = screen(data, parent_targets, base_cost).equity
    persistent_proxy = screen(data, persistent, base_cost).equity
    parent_returns = parent_proxy.pct_change(fill_method=None).fillna(0.0)
    persistent_returns = persistent_proxy.pct_change(fill_method=None).fillna(0.0)

    required = [int(v) for v in candidate["research_gate"]["required_horizons_days"]]
    anti = [int(v) for v in candidate["research_gate"]["anti_overfit_horizons_days"]]
    gross_cap = float(candidate["circuit_breaker"]["gross_drift_guard_cap"])
    parent_guard = parent["circuit_breaker"]
    parent_severe = exact_fast(
        data, parent_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=parent_guard["drawdown_threshold"],
        drawdown_guard_multiplier=parent_guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=parent_guard["cooldown_hours"],
    )
    parent_severe_summary = summary(parent_severe.equity)

    results = {}
    for leading, lagging in WEIGHT_FAMILY:
        mixed = multihorizon_two_sleeve_targets(
            parent_targets,
            persistent,
            parent_returns,
            persistent_returns,
            windows_days=ALLOCATOR_WINDOWS,
            funding_weight_when_leading=leading,
            funding_weight_when_lagging=lagging,
            rebalance_hours=24,
        )
        mixed = _cap_gross(mixed, spec.maximum_gross)
        base = replay(data, mixed, execution, gross_cap, base_cost)
        severe = replay(data, mixed, execution, gross_cap, execution["severe_cost_per_side"])
        r = evaluate(base.equity, parent_result.equity, required, anti)
        r["parent_weight_when_leading"] = leading
        r["parent_weight_when_lagging"] = lagging
        r["severe_cost"] = summary(severe.equity)
        r["severe_wealth_ratio_to_parent"] = (1 + r["severe_cost"]["return"]) / (1 + parent_severe_summary["return"])
        r["turnover_total"] = float(base.turnover.sum())
        r["no_ruin"] = not (base.ruin or severe.ruin)
        r["score"] = score(r)
        r["broad_eligible"] = bool(
            r["no_ruin"]
            and r["full_wealth_ratio_to_parent"] >= 1.10
            and r["full_drawdown_improvement_fraction"] >= 0.05
            and r["anti_overfit_beat_fraction"] >= 0.57
            and r["rolling_average_parent_beat_fraction"] >= 0.50
            and r["calendar_year_beat_fraction"] >= 0.57
            and r["tail"]["worst_day_improvement_fraction"] >= 0.0
            and r["tail"]["bottom10_damage_improvement_fraction"] >= 0.05
            and r["tail"]["top_winner_capture"] >= 0.95
            and r["severe_wealth_ratio_to_parent"] >= 1.0
        )
        results[f"lead_{leading:.2f}_lag_{lagging:.2f}"] = r

    ordered_keys = [f"lead_{a:.2f}_lag_{b:.2f}" for a, b in WEIGHT_FAMILY]
    for i, key in enumerate(ordered_keys):
        neighbors = []
        if i > 0:
            neighbors.append(results[ordered_keys[i - 1]])
        if i + 1 < len(ordered_keys):
            neighbors.append(results[ordered_keys[i + 1]])
        results[key]["neighbor_plateau"] = any(n["broad_eligible"] for n in neighbors)
        results[key]["eligible"] = bool(results[key]["broad_eligible"] and results[key]["neighbor_plateau"])

    ranking = sorted([k for k in ordered_keys if results[k]["eligible"]], key=lambda k: results[k]["score"], reverse=True)
    report = {
        "study": "V99 R11 causal adaptive allocation between V16 and persistent asymmetric challenger",
        "selection_rule": "Sleeve leadership is calculated only from closed historical returns across six horizons and rebalanced daily. Requested approval windows are reported but not rewarded by return size. A neighboring weight configuration must also pass the broad robustness gate.",
        "allocator_windows_days": list(ALLOCATOR_WINDOWS),
        "parent": summary(parent_result.equity),
        "parent_severe": parent_severe_summary,
        "selected": ranking[0] if ranking else None,
        "ranking": ranking,
        "results": results,
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
