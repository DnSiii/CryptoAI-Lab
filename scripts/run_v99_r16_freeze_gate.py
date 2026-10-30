from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_r4 import V99R4ControlSpec
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import horizon_summary, summary, tail_and_capture
from run_v99_r14_core_satellite_study import persistent_result
from run_v99_r15_dynamic_core_satellite_study import trailing_vote, desired_satellite_weight

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r16_freeze_gate.json"
FROZEN_MAX_SATELLITE = 0.10
FROZEN_REBALANCE_HOURS = 24 * 30
CADENCE_DAYS = (21, 30, 45, 60)
PHASE_DAYS = (0, 7, 14)
CAP_SENSITIVITY = (0.08, 0.10, 0.12)
RANDOM_WINDOW_DAYS = (30, 90, 180, 365)
RANDOM_SAMPLES_PER_WINDOW = 120
RANDOM_SEED = 9916


def combine_dynamic_phase(parent_equity, satellite_equity, target_satellite, rebalance_hours, phase_hours, transfer_cost_per_side):
    aligned = pd.concat([
        parent_equity.rename("parent"),
        satellite_equity.rename("satellite"),
        target_satellite.rename("target_satellite"),
    ], axis=1, join="inner").dropna()
    pr = aligned["parent"].pct_change(fill_method=None).fillna(0.0)
    sr = aligned["satellite"].pct_change(fill_method=None).fillna(0.0)
    target = aligned["target_satellite"].clip(0.0, 1.0)
    parent_cap, satellite_cap = 1.0, 0.0
    equity = pd.Series(index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    transfer_cost_total = 0.0
    for i in range(1, len(aligned)):
        parent_cap *= 1.0 + float(pr.iloc[i])
        satellite_cap *= 1.0 + float(sr.iloc[i])
        total = parent_cap + satellite_cap
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            break
        if i >= phase_hours and (i - phase_hours) % rebalance_hours == 0:
            desired = float(target.iloc[i])
            current = satellite_cap / total
            moved = abs(current - desired)
            cost = total * moved * 2.0 * transfer_cost_per_side
            transfer_cost_total += cost
            total = max(0.0, total - cost)
            satellite_cap = total * desired
            parent_cap = total * (1.0 - desired)
        equity.iloc[i] = parent_cap + satellite_cap
    return equity.ffill().fillna(1.0), float(transfer_cost_total)


def requested_floor(equity, parent_equity, days_list, return_ratio, dd_ratio):
    checks = {}
    passed = True
    for days in days_list:
        c = horizon_summary(equity, days)
        p = horizon_summary(parent_equity, days)
        if p["return"] > 0:
            ret_ok = c["return"] >= return_ratio * p["return"]
        else:
            ret_ok = c["return"] >= p["return"]
        dd_ok = abs(c["max_drawdown"]) <= dd_ratio * abs(p["max_drawdown"]) + 1e-12
        checks[str(days)] = {
            "candidate": c,
            "parent": p,
            "return_ok": bool(ret_ok),
            "drawdown_ok": bool(dd_ok),
        }
        passed = passed and ret_ok and dd_ok
    return checks, bool(passed)


def daily_returns(equity):
    return equity.resample("1D").last().pct_change(fill_method=None).dropna()


def compound(values):
    return float((1.0 + values).prod() - 1.0)


def best_day_dependency(equity):
    r = daily_returns(equity)
    ordered = r.sort_values(ascending=False)
    top1 = set(ordered.head(1).index)
    top5 = set(ordered.head(min(5, len(ordered))).index)
    return {
        "full_daily_compound": compound(r),
        "without_best_day": compound(r.loc[~r.index.isin(top1)]),
        "without_top5_days": compound(r.loc[~r.index.isin(top5)]),
        "best_day": float(ordered.iloc[0]) if len(ordered) else 0.0,
    }


def random_window_robustness(parent_equity, candidate_equity):
    p = parent_equity.resample("1D").last().dropna()
    c = candidate_equity.resample("1D").last().dropna()
    aligned = pd.concat([p.rename("parent"), c.rename("candidate")], axis=1).dropna()
    rng = np.random.default_rng(RANDOM_SEED)
    out = {}
    for days in RANDOM_WINDOW_DAYS:
        if len(aligned) <= days + 1:
            continue
        starts = rng.integers(0, len(aligned) - days, size=RANDOM_SAMPLES_PER_WINDOW)
        rows = []
        for start in starts:
            frame = aligned.iloc[int(start): int(start) + days + 1]
            pr = float(frame["parent"].iloc[-1] / frame["parent"].iloc[0] - 1.0)
            cr = float(frame["candidate"].iloc[-1] / frame["candidate"].iloc[0] - 1.0)
            rows.append((pr, cr))
        arr = np.asarray(rows, dtype=float)
        out[str(days)] = {
            "samples": int(len(arr)),
            "candidate_positive_fraction": float((arr[:, 1] > 0.0).mean()),
            "parent_positive_fraction": float((arr[:, 0] > 0.0).mean()),
            "candidate_beats_parent_fraction": float((arr[:, 1] > arr[:, 0]).mean()),
            "median_candidate_return": float(np.median(arr[:, 1])),
            "median_parent_return": float(np.median(arr[:, 0])),
        }
    return out


def main():
    c = json.loads(CONFIG_PATH.read_text())
    p = json.loads((PROJECT / "config" / c["parent_candidate_config"]).read_text())
    if c.get("mode") != "PAPER_ONLY" or c.get("real_orders"):
        raise RuntimeError("R16 freeze gate is paper-only research")

    data, parent_targets, parent_base, _, quarantined = build_v16(p)
    execution = load_execution(p)
    spec = V99AsymmetricSpec(**c["asymmetric_overlay"])
    ctrl = V99R4ControlSpec(**c["r4_control"])
    satellite_base = persistent_result(data, parent_targets, execution, spec, ctrl, execution["base_cost_per_side"])
    vote = trailing_vote(parent_base.equity, satellite_base.equity)

    desired = desired_satellite_weight(vote, FROZEN_MAX_SATELLITE)
    baseline, baseline_transfer_cost = combine_dynamic_phase(
        parent_base.equity, satellite_base.equity, desired,
        FROZEN_REBALANCE_HOURS, 0, execution["base_cost_per_side"],
    )

    pg = p["circuit_breaker"]
    parent_severe = exact_fast(
        data, parent_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=2.0,
        drawdown_guard_threshold=pg["drawdown_threshold"],
        drawdown_guard_multiplier=pg["exposure_multiplier"],
        drawdown_guard_cooldown_hours=pg["cooldown_hours"],
    )
    satellite_severe = persistent_result(data, parent_targets, execution, spec, ctrl, execution["severe_cost_per_side"])
    severe, severe_transfer_cost = combine_dynamic_phase(
        parent_severe.equity, satellite_severe.equity, desired,
        FROZEN_REBALANCE_HOURS, 0, execution["severe_cost_per_side"],
    )

    required = [7, 30, 90, 180, 365]
    baseline_checks, baseline_floor = requested_floor(baseline, parent_base.equity, required, 0.99, 1.03)
    base_summary = summary(baseline)
    parent_summary = summary(parent_base.equity)
    severe_summary = summary(severe)
    parent_severe_summary = summary(parent_severe.equity)
    tail = tail_and_capture(parent_base.equity, baseline)

    cadence_phase = {}
    perturb_passes = []
    for days in CADENCE_DAYS:
        hours = days * 24
        for phase_days in PHASE_DAYS:
            phase = min(phase_days * 24, max(0, hours - 1))
            eq, cost = combine_dynamic_phase(
                parent_base.equity, satellite_base.equity, desired,
                hours, phase, execution["base_cost_per_side"],
            )
            checks, floor = requested_floor(eq, parent_base.equity, required, 0.975, 1.05)
            s = summary(eq)
            key = f"{days}d_phase{phase_days}d"
            passed = bool(
                floor
                and (1.0 + s["return"]) / (1.0 + parent_summary["return"]) >= 0.98
                and abs(s["max_drawdown"]) <= 1.05 * abs(parent_summary["max_drawdown"])
            )
            perturb_passes.append(passed)
            cadence_phase[key] = {
                "summary": s,
                "checks": checks,
                "transfer_cost_total": cost,
                "passed": passed,
            }

    cap_sensitivity = {}
    cap_passes = []
    for cap in CAP_SENSITIVITY:
        cap_desired = desired_satellite_weight(vote, cap)
        eq, cost = combine_dynamic_phase(
            parent_base.equity, satellite_base.equity, cap_desired,
            FROZEN_REBALANCE_HOURS, 0, execution["base_cost_per_side"],
        )
        checks, floor = requested_floor(eq, parent_base.equity, required, 0.98, 1.04)
        s = summary(eq)
        passed = bool(
            floor
            and (1.0 + s["return"]) / (1.0 + parent_summary["return"]) >= 1.0
            and abs(s["max_drawdown"]) <= 1.04 * abs(parent_summary["max_drawdown"])
        )
        cap_passes.append(passed)
        cap_sensitivity[str(cap)] = {
            "summary": s,
            "checks": checks,
            "transfer_cost_total": cost,
            "passed": passed,
        }

    random_windows = random_window_robustness(parent_base.equity, baseline)
    random_pass = all(
        item["candidate_positive_fraction"] >= item["parent_positive_fraction"] - 0.03
        and item["candidate_beats_parent_fraction"] >= 0.45
        for item in random_windows.values()
    )

    dependency = best_day_dependency(baseline)
    parent_dependency = best_day_dependency(parent_base.equity)
    best_day_pass = bool(
        dependency["without_best_day"] > 0.0
        and dependency["without_top5_days"] > 0.0
        and (1.0 + dependency["without_top5_days"])
        / (1.0 + parent_dependency["without_top5_days"]) >= 0.95
    )

    severe_ratio = (1.0 + severe_summary["return"]) / (1.0 + parent_severe_summary["return"])
    full_ratio = (1.0 + base_summary["return"]) / (1.0 + parent_summary["return"])
    strict_gate = {
        "baseline_v16_floor": baseline_floor,
        "full_roi_not_below_v16": full_ratio >= 1.0,
        "full_drawdown_not_worse": abs(base_summary["max_drawdown"]) <= abs(parent_summary["max_drawdown"]),
        "severe_cost_not_below_v16": severe_ratio >= 1.0,
        "worst_day_not_worse": tail["worst_day_improvement_fraction"] >= -0.01,
        "bottom10_not_worse": tail["bottom10_damage_improvement_fraction"] >= 0.0,
        "top_winners_preserved": tail["top_winner_capture"] >= 0.99,
        "cadence_phase_robustness": sum(perturb_passes) / len(perturb_passes) >= 0.75,
        "cap_sensitivity": all(cap_passes),
        "random_subwindows": random_pass,
        "best_day_dependency": best_day_pass,
    }
    passed = all(strict_gate.values())

    report = {
        "study": "V99 R16 frozen forward-candidate robustness gate",
        "frozen_candidate": {
            "architecture": "V16 core + consensus-gated persistent alpha satellite",
            "maximum_satellite_weight": FROZEN_MAX_SATELLITE,
            "rebalance_days": 30,
            "allocator_windows_days": [45, 60, 90, 120, 180, 240],
            "routine_persistence_hours": 4,
            "emergency_side_protection": "immediate",
        },
        "baseline": base_summary,
        "parent": parent_summary,
        "requested": baseline_checks,
        "tail": tail,
        "severe_cost": severe_summary,
        "parent_severe": parent_severe_summary,
        "full_wealth_ratio_to_v16": full_ratio,
        "severe_wealth_ratio_to_v16": severe_ratio,
        "baseline_transfer_cost_total": baseline_transfer_cost,
        "severe_transfer_cost_total": severe_transfer_cost,
        "cadence_phase_perturbations": cadence_phase,
        "cap_sensitivity": cap_sensitivity,
        "random_subwindows": random_windows,
        "best_day_dependency": dependency,
        "parent_best_day_dependency": parent_dependency,
        "strict_gate": strict_gate,
        "strict_gate_passed": passed,
        "forward_rule": "If this gate passes, freeze all strategy and allocation parameters before counting any subsequent paper observations as independent forward evidence.",
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not passed:
        failed = [k for k, v in strict_gate.items() if not v]
        print("R16 FREEZE GATE FAILED:", ", ".join(failed))


if __name__ == "__main__":
    main()
