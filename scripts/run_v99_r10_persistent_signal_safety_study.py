from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.v99 import V99AsymmetricSpec, _cap_gross
from cryptoai_v13.v99_r4 import V99R4ControlSpec, _sparse_side_shock
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import calendar_year_summaries, horizon_summary, rolling_robustness, summary, tail_and_capture

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r10_persistent_signal_safety_study.json"

# Small structural family: preserve the R7 persistence effect, but current-hour
# emergency protection is never delayed. The family is intentionally small.
HOURS = [2, 3, 4]
MODES = ["current_stress", "current_stress_plus_sparse_shock"]
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


def broad_score(r):
    t = r["tail"]
    return (
        2.5 * r["full_wealth_ratio_to_parent"]
        + 3.0 * r["full_drawdown_improvement_fraction"]
        + r["anti_overfit_beat_fraction"]
        + r["rolling_average_parent_beat_fraction"]
        + r["calendar_year_beat_fraction"]
        + max(-0.75, min(0.75, t["worst_day_improvement_fraction"]))
        + max(-0.75, min(0.75, t["bottom10_damage_improvement_fraction"]))
        + min(1.2, t["top_winner_capture"])
        + min(0.75, max(-0.75, r["severe_wealth_ratio_to_parent"] - 1.0))
    )


def main():
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R10 is paper-only research")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    spec = V99AsymmetricSpec(**candidate["asymmetric_overlay"])
    control = V99R4ControlSpec(**candidate["r4_control"])
    r5_targets, diag = asymmetric_v99_targets_r5(data, parent_targets, proxy, spec, control)
    shock_long, shock_short, shock_diag = _sparse_side_shock(data.close, parent_targets, control)

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
    for hours in HOURS:
        routine = r5_targets.shift(hours).fillna(0.0)
        for mode in MODES:
            long_now = diag["long_risk_factor"].astype(float)
            short_now = diag["short_risk_factor"].astype(float)
            if mode == "current_stress_plus_sparse_shock":
                long_now = pd.concat([long_now, shock_long], axis=1).min(axis=1)
                short_now = pd.concat([short_now, shock_short], axis=1).min(axis=1)
            protected = (
                routine.clip(lower=0.0).mul(long_now, axis=0)
                + routine.clip(upper=0.0).mul(short_now, axis=0)
            )
            protected = _cap_gross(protected, spec.maximum_gross)
            base = replay(data, protected, execution, gross_cap, execution["base_cost_per_side"])
            severe = replay(data, protected, execution, gross_cap, execution["severe_cost_per_side"])
            r = evaluate(base.equity, parent_result.equity, required, anti)
            r["hours"] = hours
            r["mode"] = mode
            r["turnover_total"] = float(base.turnover.sum())
            r["severe_cost"] = summary(severe.equity)
            r["severe_wealth_ratio_to_parent"] = (1 + r["severe_cost"]["return"]) / (1 + parent_severe_summary["return"])
            r["current_emergency_fraction"] = float(((long_now < 0.999) | (short_now < 0.999)).mean())
            r["sparse_shock_fraction"] = float((shock_diag["damage_factor"] < 0.999).mean())
            r["no_ruin"] = not (base.ruin or severe.ruin)
            r["broad_score"] = broad_score(r)
            r["broad_eligible"] = bool(
                r["no_ruin"]
                and r["full_wealth_ratio_to_parent"] >= 1.10
                and r["full_drawdown_improvement_fraction"] >= 0.05
                and r["tail"]["top_winner_capture"] >= 0.95
                and r["anti_overfit_beat_fraction"] >= 0.50
                and r["calendar_year_beat_fraction"] >= 0.50
                and r["severe_wealth_ratio_to_parent"] >= 1.0
            )
            results[f"{hours}h_{mode}"] = r

    # Robustness requires the same safety mode to be broadly eligible at a
    # neighboring persistence horizon; isolated timing spikes are rejected.
    for key, r in results.items():
        h, mode = r["hours"], r["mode"]
        neighbors = [results.get(f"{n}h_{mode}") for n in (h - 1, h + 1)]
        r["neighbor_plateau"] = any(x is not None and x["broad_eligible"] for x in neighbors)
        r["eligible"] = bool(r["broad_eligible"] and r["neighbor_plateau"])

    ranking = sorted([k for k, r in results.items() if r["eligible"]], key=lambda k: results[k]["broad_score"], reverse=True)
    report = {
        "study": "V99 R10 persistent signal with immediate safety override",
        "selection_rule": "Routine signal changes use the predeclared 2/3/4h persistence family, while current-hour directional stress (and optionally sparse synchronized side shock) is immediate. Requested-window magnitudes are excluded from selection and adjacent timing robustness is mandatory.",
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
