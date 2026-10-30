from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
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
from run_candidate_v99 import (
    calendar_year_summaries,
    horizon_summary,
    rolling_robustness,
    summary,
    tail_and_capture,
)

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r14_core_satellite_study.json"

SATELLITE_WEIGHTS = (0.10, 0.20, 0.30, 0.40)
BASE_REBALANCE_HOURS = 24 * 30
ROBUST_REBALANCE_HOURS = (24 * 7, 24 * 30, 24 * 90)
FAST_POLICY = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6}


def persistent_result(data, parent_targets, execution, spec, ctrl, cost):
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    r5, diag = asymmetric_v99_targets_r5(data, parent_targets, proxy, spec, ctrl)
    routine = r5.shift(4).fillna(0.0)
    shock_long, shock_short, _ = _sparse_side_shock(data.close, parent_targets, ctrl)
    long_now = pd.concat([diag["long_risk_factor"].astype(float), shock_long], axis=1).min(axis=1)
    short_now = pd.concat([diag["short_risk_factor"].astype(float), shock_short], axis=1).min(axis=1)
    targets = _cap_gross(
        routine.clip(lower=0.0).mul(long_now, axis=0)
        + routine.clip(upper=0.0).mul(short_now, axis=0),
        spec.maximum_gross,
    )
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=2.0,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
    )


def combine_sleeves(parent_equity, satellite_equity, satellite_weight, rebalance_hours, transfer_cost_per_side):
    aligned = pd.concat(
        [parent_equity.rename("parent"), satellite_equity.rename("satellite")],
        axis=1,
        join="inner",
    ).dropna()
    pr = aligned["parent"].pct_change(fill_method=None).fillna(0.0)
    sr = aligned["satellite"].pct_change(fill_method=None).fillna(0.0)
    equity = pd.Series(index=aligned.index, dtype=float)

    parent_cap = 1.0 - satellite_weight
    satellite_cap = satellite_weight
    equity.iloc[0] = 1.0
    transfer_cost_total = 0.0

    for i in range(1, len(aligned)):
        parent_cap *= 1.0 + float(pr.iloc[i])
        satellite_cap *= 1.0 + float(sr.iloc[i])
        total = parent_cap + satellite_cap
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            break
        if i % rebalance_hours == 0:
            current_satellite = satellite_cap / total
            moved_fraction = abs(current_satellite - satellite_weight)
            # Conservative approximation: scaling down one sleeve and scaling
            # up the other are both charged one side of execution cost.
            cost = total * moved_fraction * 2.0 * transfer_cost_per_side
            transfer_cost_total += cost
            total = max(0.0, total - cost)
            satellite_cap = total * satellite_weight
            parent_cap = total * (1.0 - satellite_weight)
        equity.iloc[i] = parent_cap + satellite_cap

    equity = equity.ffill().fillna(1.0)
    return equity, float(transfer_cost_total)


def evaluate(equity, parent_equity, required, anti):
    full = summary(equity)
    pfull = summary(parent_equity)
    requested = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in required
    }
    antih = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in anti
    }
    rolling = {str(d): rolling_robustness(parent_equity, equity, d) for d in anti}
    years = calendar_year_summaries(equity)
    pyears = calendar_year_summaries(parent_equity)
    common = sorted(set(years) & set(pyears))
    return {
        "full": full,
        "full_wealth_ratio_to_parent": (1.0 + full["return"]) / (1.0 + pfull["return"]),
        "full_drawdown_improvement_fraction": 1.0 - abs(full["max_drawdown"]) / abs(pfull["max_drawdown"]),
        "requested": requested,
        "anti_overfit": antih,
        "anti_overfit_beat_fraction": sum(
            antih[str(d)]["v99"]["return"] > antih[str(d)]["parent"]["return"] for d in anti
        ) / len(anti),
        "rolling_average_parent_beat_fraction": sum(
            v["candidate_beats_parent_fraction"] for v in rolling.values()
        ) / len(rolling),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(
            years[y]["return"] > pyears[y]["return"] for y in common
        ) / max(1, len(common)),
        "tail": tail_and_capture(parent_equity, equity),
    }


def floor_pass(result, return_ratio=0.98, dd_ratio=1.03):
    checks = {}
    ok = True
    for days, pair in result["requested"].items():
        c, p = pair["v99"], pair["parent"]
        if p["return"] > 0:
            ret_ok = c["return"] >= return_ratio * p["return"]
        else:
            ret_ok = c["return"] >= p["return"]
        risk_ok = abs(c["max_drawdown"]) <= dd_ratio * abs(p["max_drawdown"]) + 1e-12
        checks[days] = {"return_ok": bool(ret_ok), "drawdown_ok": bool(risk_ok)}
        ok = ok and ret_ok and risk_ok
    return checks, bool(ok)


def main():
    candidate = json.loads(CONFIG_PATH.read_text())
    parent = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text())
    if candidate.get("mode") != "PAPER_ONLY" or candidate.get("real_orders"):
        raise RuntimeError("R14 is paper-only research")

    data, parent_targets, parent_base, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    spec = V99AsymmetricSpec(**candidate["asymmetric_overlay"])
    ctrl = V99R4ControlSpec(**candidate["r4_control"])
    persistent_base = persistent_result(
        data, parent_targets, execution, spec, ctrl, execution["base_cost_per_side"]
    )

    pg = parent["circuit_breaker"]
    parent_severe = exact_fast(
        data,
        parent_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=2.0,
        drawdown_guard_threshold=pg["drawdown_threshold"],
        drawdown_guard_multiplier=pg["exposure_multiplier"],
        drawdown_guard_cooldown_hours=pg["cooldown_hours"],
    )
    persistent_severe = persistent_result(
        data, parent_targets, execution, spec, ctrl, execution["severe_cost_per_side"]
    )

    required = [int(v) for v in candidate["research_gate"]["required_horizons_days"]]
    anti = [int(v) for v in candidate["research_gate"]["anti_overfit_horizons_days"]]
    parent_severe_summary = summary(parent_severe.equity)

    results = {}
    for sat_weight in SATELLITE_WEIGHTS:
        key = f"satellite_{int(round(sat_weight * 100))}pct"
        frequency_results = {}
        for hours in ROBUST_REBALANCE_HOURS:
            base_equity, transfer_cost = combine_sleeves(
                parent_base.equity,
                persistent_base.equity,
                sat_weight,
                hours,
                execution["base_cost_per_side"],
            )
            severe_equity, severe_transfer_cost = combine_sleeves(
                parent_severe.equity,
                persistent_severe.equity,
                sat_weight,
                hours,
                execution["severe_cost_per_side"],
            )
            r = evaluate(base_equity, parent_base.equity, required, anti)
            r["severe_cost"] = summary(severe_equity)
            r["parent_severe"] = parent_severe_summary
            r["severe_wealth_ratio_to_parent"] = (
                (1.0 + r["severe_cost"]["return"])
                / (1.0 + parent_severe_summary["return"])
            )
            r["transfer_cost_total"] = transfer_cost
            r["severe_transfer_cost_total"] = severe_transfer_cost
            checks, floor = floor_pass(r)
            r["floor_checks"] = checks
            r["floor_passed"] = floor
            tail = r["tail"]
            r["robust_passed"] = bool(
                floor
                and r["full_wealth_ratio_to_parent"] >= 1.0
                and r["full_drawdown_improvement_fraction"] >= -0.01
                and r["severe_wealth_ratio_to_parent"] >= 1.0
                and r["rolling_average_parent_beat_fraction"] >= 0.48
                and tail["bottom10_damage_improvement_fraction"] >= 0.0
                and tail["worst_day_improvement_fraction"] >= -0.02
                and tail["top_winner_capture"] >= 0.98
            )
            frequency_results[str(hours)] = r

        # Weight is eligible only if the weekly, monthly and quarterly
        # rebalance perturbations all satisfy the same V16 floor.
        robust_all = all(v["robust_passed"] for v in frequency_results.values())
        baseline = frequency_results[str(BASE_REBALANCE_HOURS)]
        results[key] = {
            "satellite_weight": sat_weight,
            "robust_across_rebalance_frequencies": robust_all,
            "baseline_30d": baseline,
            "frequency_results": frequency_results,
        }

    eligible = [
        k for k, r in results.items() if r["robust_across_rebalance_frequencies"]
    ]
    ranking = sorted(
        eligible,
        key=lambda k: (
            results[k]["baseline_30d"]["full"]["return"],
            results[k]["baseline_30d"]["severe_cost"]["return"],
            -abs(results[k]["baseline_30d"]["full"]["max_drawdown"]),
        ),
        reverse=True,
    )

    report = {
        "study": "V99 R14 independent V16 core + persistent alpha satellite",
        "objective": "maximize ROI while preserving at least 98% of V16 positive-horizon return and no more than 3% relative drawdown deterioration, with weekly/monthly/quarterly rebalance robustness",
        "satellite_weights": list(SATELLITE_WEIGHTS),
        "rebalance_hours_robustness": list(ROBUST_REBALANCE_HOURS),
        "selected": ranking[0] if ranking else None,
        "ranking": ranking,
        "parent": summary(parent_base.equity),
        "persistent_engine": summary(persistent_base.equity),
        "results": results,
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
