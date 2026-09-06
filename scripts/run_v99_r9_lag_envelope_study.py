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
from cryptoai_v13.v99_r9 import LagEnvelopeSpec, lag_confirm_growth
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import calendar_year_summaries, horizon_summary, rolling_robustness, summary, tail_and_capture

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r9_lag_envelope_study.json"
HOURS = [1, 2, 3, 4, 6]
FAST_POLICY = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6, "recovery": None}


def run_exact(data, targets, execution, gross_cap, cost):
    return exact_fast(
        data, targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
    )


def evaluate(equity, parent_equity, required_days, anti_days):
    full = summary(equity)
    parent_full = summary(parent_equity)
    requested = {str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)} for d in required_days}
    anti = {str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)} for d in anti_days}
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
        "anti_overfit_beat_fraction": sum(anti[str(d)]["v99"]["return"] > anti[str(d)]["parent"]["return"] for d in anti_days) / len(anti_days),
        "rolling_average_parent_beat_fraction": sum(v["candidate_beats_parent_fraction"] for v in rolling.values()) / len(rolling),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(years[y]["return"] > parent_years[y]["return"] for y in common) / max(len(common), 1),
        "tail": tail_and_capture(parent_equity, equity),
    }


def score(r):
    t = r["tail"]
    return (
        2.5 * r["full_wealth_ratio_to_parent"]
        + 2.5 * r["full_drawdown_improvement_fraction"]
        + r["anti_overfit_beat_fraction"]
        + r["rolling_average_parent_beat_fraction"]
        + r["calendar_year_beat_fraction"]
        + max(-0.5, min(0.5, t["worst_day_improvement_fraction"]))
        + max(-0.5, min(0.5, t["bottom10_damage_improvement_fraction"]))
        + min(1.2, t["top_winner_capture"])
    )


def main():
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text(encoding="utf-8"))
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R9 must remain orderless")

    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    base_targets, base_diag = asymmetric_v99_targets_r5(
        data, parent_targets, proxy,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R4ControlSpec(**candidate["r3_control"]),
    )
    gate = candidate["research_gate"]
    required = [int(v) for v in gate["required_horizons_days"]]
    anti = [int(v) for v in gate["anti_overfit_horizons_days"]]
    gross_cap = float(candidate["circuit_breaker"]["gross_drift_guard_cap"])
    results = {}
    for h in HOURS:
        confirmed, diag = lag_confirm_growth(base_targets, base_diag, LagEnvelopeSpec(h, float(candidate["asymmetric_overlay"]["maximum_gross"]), True))
        base = run_exact(data, confirmed, execution, gross_cap, execution["base_cost_per_side"])
        severe = run_exact(data, confirmed, execution, gross_cap, execution["severe_cost_per_side"])
        r = evaluate(base.equity, parent_result.equity, required, anti)
        r["confirm_hours"] = h
        r["severe_cost"] = summary(severe.equity)
        r["turnover_total"] = float(base.turnover.sum())
        r["limited_fraction"] = float(diag["limited_count"].gt(0).mean())
        r["no_ruin"] = not (base.ruin or severe.ruin)
        r["broad_score"] = score(r)
        r["broad_eligible"] = bool(
            r["no_ruin"]
            and r["full_wealth_ratio_to_parent"] >= 1.05
            and r["full_drawdown_improvement_fraction"] >= 0.0
            and r["tail"]["top_winner_capture"] >= 0.95
            and r["anti_overfit_beat_fraction"] >= 0.50
            and r["calendar_year_beat_fraction"] >= 0.50
        )
        results[str(h)] = r

    tested = set(HOURS)
    for h in HOURS:
        neighbors = [n for n in (h - 1, h + 1) if n in tested]
        results[str(h)]["neighbor_plateau"] = any(results[str(n)]["broad_eligible"] for n in neighbors)
        results[str(h)]["eligible"] = bool(h > 1 and results[str(h)]["broad_eligible"] and results[str(h)]["neighbor_plateau"])
    eligible = [h for h in HOURS if results[str(h)]["eligible"]]
    ranking = sorted(eligible, key=lambda h: results[str(h)]["broad_score"], reverse=True)
    report = {
        "study": "V99 R9 predeclared lag-envelope confirmation study",
        "selection_rule": "Fast-down/lag-confirmed-up windows were declared before R8 results. Requested horizon magnitudes are reported but excluded from selection. Adjacent plateau required.",
        "parent": summary(parent_result.equity),
        "selected_confirm_hours": ranking[0] if ranking else None,
        "ranking": ranking,
        "results": results,
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
