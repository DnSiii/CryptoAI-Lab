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
from cryptoai_v13.v99_r4 import V99R4ControlSpec
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import (
    calendar_year_summaries,
    horizon_summary,
    rolling_robustness,
    summary,
    tail_and_capture,
)

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r6_breaker_study.json"

# Predeclared before seeing the R6 results. These are structural hypotheses,
# not a dense parameter grid. Legacy is included as the control; no_breaker is
# a diagnostic sensitivity, not automatically eligible for promotion.
POLICIES = {
    "legacy_72h_10pct": {
        "threshold": 0.058,
        "multiplier": 0.10,
        "cooldown": 72,
        "recovery": None,
        "eligible": False,
    },
    "fast_12h_40pct": {
        "threshold": 0.058,
        "multiplier": 0.40,
        "cooldown": 12,
        "recovery": None,
        "eligible": True,
    },
    "fast_6h_55pct": {
        "threshold": 0.058,
        "multiplier": 0.55,
        "cooldown": 6,
        "recovery": None,
        "eligible": True,
    },
    "adaptive_45pct_recover_2p5": {
        "threshold": 0.058,
        "multiplier": 0.45,
        "cooldown": None,
        "recovery": 0.025,
        "eligible": True,
    },
    "no_breaker_sensitivity": {
        "threshold": None,
        "multiplier": 1.0,
        "cooldown": None,
        "recovery": None,
        "eligible": False,
    },
}


def run_exact(data, targets, execution, gross_cap, policy, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=policy["threshold"],
        drawdown_guard_multiplier=policy["multiplier"],
        drawdown_guard_recovery=policy["recovery"],
        drawdown_guard_cooldown_hours=policy["cooldown"],
    )


def evaluate(equity, parent_equity, required_days, anti_days):
    full = summary(equity)
    parent_full = summary(parent_equity)
    requested = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in required_days
    }
    anti = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in anti_days
    }
    rolling = {str(d): rolling_robustness(parent_equity, equity, d) for d in anti_days}
    years = calendar_year_summaries(equity)
    parent_years = calendar_year_summaries(parent_equity)
    common = sorted(set(years) & set(parent_years))
    year_beats = sum(years[y]["return"] > parent_years[y]["return"] for y in common)
    anti_beats = sum(anti[str(d)]["v99"]["return"] > anti[str(d)]["parent"]["return"] for d in anti_days)
    requested_return_beats = sum(requested[str(d)]["v99"]["return"] > requested[str(d)]["parent"]["return"] for d in required_days)
    requested_dd_beats = sum(abs(requested[str(d)]["v99"]["max_drawdown"]) <= abs(requested[str(d)]["parent"]["max_drawdown"]) + 1e-12 for d in required_days)
    rolling_beat = sum(v["candidate_beats_parent_fraction"] for v in rolling.values()) / max(len(rolling), 1)
    return {
        "full": full,
        "full_return_ratio_to_parent": (1.0 + full["return"]) / (1.0 + parent_full["return"]),
        "full_drawdown_improvement_fraction": 1.0 - abs(full["max_drawdown"]) / abs(parent_full["max_drawdown"]),
        "requested": requested,
        "requested_return_beat_fraction": requested_return_beats / len(required_days),
        "requested_drawdown_beat_fraction": requested_dd_beats / len(required_days),
        "anti_overfit": anti,
        "anti_overfit_beat_fraction": anti_beats / len(anti_days),
        "rolling_average_parent_beat_fraction": rolling_beat,
        "calendar_years": years,
        "calendar_year_beat_fraction": year_beats / max(len(common), 1),
        "tail": tail_and_capture(parent_equity, equity),
    }


def dominance_score(result):
    # Broad score deliberately excludes exact requested-window return magnitudes.
    # It rewards full-history capital, drawdown, rolling robustness, calendar
    # diversity, non-target horizons and tail behavior.
    full = result["full"]
    tail = result["tail"]
    return (
        2.0 * result["full_return_ratio_to_parent"]
        + 2.0 * result["full_drawdown_improvement_fraction"]
        + result["anti_overfit_beat_fraction"]
        + result["rolling_average_parent_beat_fraction"]
        + result["calendar_year_beat_fraction"]
        + max(-0.5, min(0.5, tail["bottom10_damage_improvement_fraction"]))
        + max(-0.5, min(0.5, tail["worst_day_improvement_fraction"]))
        + min(1.2, tail["top_winner_capture"])
        + (0.2 if full["return"] > 0 else -1.0)
    )


def main():
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R6 study must remain orderless")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    targets, diagnostics = asymmetric_v99_targets_r5(
        data,
        parent_targets,
        proxy,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R4ControlSpec(**candidate["r3_control"]),
    )
    gate = candidate["research_gate"]
    required_days = [int(v) for v in gate["required_horizons_days"]]
    anti_days = [int(v) for v in gate["anti_overfit_horizons_days"]]
    gross_cap = float(candidate["circuit_breaker"]["gross_drift_guard_cap"])

    parent_guard = parent["circuit_breaker"]
    parent_policy = {
        "threshold": parent_guard["drawdown_threshold"],
        "multiplier": parent_guard["exposure_multiplier"],
        "cooldown": parent_guard["cooldown_hours"],
        "recovery": None,
    }
    parent_severe = run_exact(data, parent_targets, execution, gross_cap, parent_policy, execution["severe_cost_per_side"])
    parent_delay = run_exact(data, parent_targets.shift(3).fillna(0.0), execution, gross_cap, parent_policy, execution["base_cost_per_side"])

    results = {}
    for name, policy in POLICIES.items():
        base = run_exact(data, targets, execution, gross_cap, policy, execution["base_cost_per_side"])
        severe = run_exact(data, targets, execution, gross_cap, policy, execution["severe_cost_per_side"])
        delay = run_exact(data, targets.shift(3).fillna(0.0), execution, gross_cap, policy, execution["base_cost_per_side"])
        result = evaluate(base.equity, parent_result.equity, required_days, anti_days)
        result["policy"] = policy
        result["severe_cost"] = {"v99": summary(severe.equity), "parent": summary(parent_severe.equity)}
        result["delay_3h"] = {"v99": summary(delay.equity), "parent": summary(parent_delay.equity)}
        result["no_ruin"] = not (base.ruin or severe.ruin or delay.ruin)
        result["broad_score"] = dominance_score(result)
        results[name] = result

    eligible = {k: v for k, v in results.items() if POLICIES[k]["eligible"] and v["no_ruin"]}
    ranked = sorted(eligible, key=lambda k: results[k]["broad_score"], reverse=True)
    selected = ranked[0] if ranked else None

    report = {
        "study": "V99 R6 predeclared breaker robustness study",
        "selection_rule": "Rank only predeclared eligible breaker policies by broad history/anti-overfit/risk/tail score; requested-window magnitudes are reported but excluded from the selection score.",
        "parent": summary(parent_result.equity),
        "parent_policy": parent_policy,
        "selected_policy": selected,
        "ranking": ranked,
        "results": results,
        "funding_quarantined_symbols": quarantined,
        "diagnostics": {
            "stress_active_fraction": float((diagnostics["stress_factor"] < 0.999).mean()),
            "clean_trend_fraction": float(diagnostics["clean_trend"].astype(bool).mean()),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": selected,
        "ranking": ranked,
        "parent": report["parent"],
        "results": {
            k: {
                "full": v["full"],
                "requested": v["requested"],
                "anti_beat": v["anti_overfit_beat_fraction"],
                "rolling_beat": v["rolling_average_parent_beat_fraction"],
                "year_beat": v["calendar_year_beat_fraction"],
                "tail": v["tail"],
                "severe_cost": v["severe_cost"],
                "delay_3h": v["delay_3h"],
                "score": v["broad_score"],
            }
            for k, v in results.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
