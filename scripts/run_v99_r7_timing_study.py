from __future__ import annotations

import json
import sys
from pathlib import Path

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
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r7_timing_study.json"

# Predeclared timing sensitivity. The goal is explicitly NOT to find a magic
# delay. Promotion requires a stable neighboring plateau, so an isolated best
# result is rejected as timing overfit.
SHIFTS_HOURS = [0, 1, 2, 3, 4, 6]
FAST_POLICY = {
    "threshold": 0.058,
    "multiplier": 0.55,
    "cooldown": 6,
    "recovery": None,
}


def run_exact(data, targets, execution, gross_cap, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_recovery=FAST_POLICY["recovery"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
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
    return {
        "full": full,
        "full_wealth_ratio_to_parent": (1.0 + full["return"]) / (1.0 + parent_full["return"]),
        "full_drawdown_improvement_fraction": 1.0 - abs(full["max_drawdown"]) / abs(parent_full["max_drawdown"]),
        "requested": requested,
        "anti_overfit": anti,
        "anti_overfit_beat_fraction": sum(
            anti[str(d)]["v99"]["return"] > anti[str(d)]["parent"]["return"] for d in anti_days
        ) / len(anti_days),
        "rolling_average_parent_beat_fraction": sum(
            item["candidate_beats_parent_fraction"] for item in rolling.values()
        ) / len(rolling),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(
            years[y]["return"] > parent_years[y]["return"] for y in common
        ) / max(len(common), 1),
        "tail": tail_and_capture(parent_equity, equity),
    }


def broad_score(result):
    tail = result["tail"]
    return (
        2.5 * result["full_wealth_ratio_to_parent"]
        + 2.5 * result["full_drawdown_improvement_fraction"]
        + result["anti_overfit_beat_fraction"]
        + result["rolling_average_parent_beat_fraction"]
        + result["calendar_year_beat_fraction"]
        + max(-0.5, min(0.5, tail["worst_day_improvement_fraction"]))
        + max(-0.5, min(0.5, tail["bottom10_damage_improvement_fraction"]))
        + min(1.2, tail["top_winner_capture"])
    )


def main():
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R7 timing study must remain paper-only and orderless")

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

    # Parent is always evaluated at its native timing. We are designing a new
    # candidate, not retroactively improving V16.
    parent_guard = parent["circuit_breaker"]
    parent_severe = exact_fast(
        data,
        parent_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=parent_guard["drawdown_threshold"],
        drawdown_guard_multiplier=parent_guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=parent_guard["cooldown_hours"],
    )

    results = {}
    for shift in SHIFTS_HOURS:
        delayed = targets.shift(shift).fillna(0.0) if shift else targets
        base = run_exact(data, delayed, execution, gross_cap, execution["base_cost_per_side"])
        severe = run_exact(data, delayed, execution, gross_cap, execution["severe_cost_per_side"])
        result = evaluate(base.equity, parent_result.equity, required_days, anti_days)
        result["shift_hours"] = shift
        result["severe_cost"] = {
            "v99": summary(severe.equity),
            "parent": summary(parent_severe.equity),
        }
        result["no_ruin"] = not (base.ruin or severe.ruin)
        result["broad_score"] = broad_score(result)
        # Broad eligibility excludes requested-window magnitudes.
        result["broad_eligible"] = bool(
            result["no_ruin"]
            and result["full_wealth_ratio_to_parent"] >= 1.05
            and result["full_drawdown_improvement_fraction"] >= 0.0
            and result["tail"]["top_winner_capture"] >= 0.95
            and result["anti_overfit_beat_fraction"] >= 0.50
        )
        results[str(shift)] = result

    # A candidate timing is robust only if a neighboring tested timing is also
    # broadly eligible. This rejects a lone spike at exactly 2h/3h/etc.
    tested = set(SHIFTS_HOURS)
    for shift in SHIFTS_HOURS:
        result = results[str(shift)]
        neighbors = [n for n in (shift - 1, shift + 1) if n in tested]
        result["neighbor_plateau"] = any(results[str(n)]["broad_eligible"] for n in neighbors)
        result["timing_eligible"] = bool(result["broad_eligible"] and result["neighbor_plateau"])

    eligible = [
        shift for shift in SHIFTS_HOURS
        if results[str(shift)]["timing_eligible"]
    ]
    ranking = sorted(eligible, key=lambda s: results[str(s)]["broad_score"], reverse=True)
    selected = ranking[0] if ranking else None

    report = {
        "study": "V99 R7 predeclared timing robustness study",
        "selection_rule": "Requested 7/30/90/180/365-day return magnitudes are reported but excluded from timing selection. A timing can be selected only if broad history/risk/anti-overfit criteria pass and at least one adjacent timing also passes.",
        "parent": summary(parent_result.equity),
        "policy": FAST_POLICY,
        "selected_shift_hours": selected,
        "ranking": ranking,
        "results": results,
        "funding_quarantined_symbols": quarantined,
        "diagnostics": {
            "stress_active_fraction": float((diagnostics["stress_factor"] < 0.999).mean()),
            "clean_trend_fraction": float(diagnostics["clean_trend"].astype(bool).mean()),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_shift_hours": selected,
        "ranking": ranking,
        "parent": report["parent"],
        "results": {
            k: {
                "full": v["full"],
                "tail": v["tail"],
                "anti": v["anti_overfit_beat_fraction"],
                "rolling": v["rolling_average_parent_beat_fraction"],
                "years": v["calendar_year_beat_fraction"],
                "severe_cost": v["severe_cost"],
                "broad_eligible": v["broad_eligible"],
                "neighbor_plateau": v["neighbor_plateau"],
                "timing_eligible": v["timing_eligible"],
                "score": v["broad_score"],
            }
            for k, v in results.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
