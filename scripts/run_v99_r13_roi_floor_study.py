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
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r13_roi_floor_study.json"
WINDOWS = (45, 60, 90, 120, 180, 240)
FAST_POLICY = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6}

# Predeclared before seeing R13 results. These are consensus transforms over the
# same six multi-horizon votes; no signal thresholds or requested-window dates
# are tuned here.
VARIANTS = (
    "proportional_control",
    "majority_ramp",
    "supermajority_ramp",
    "supermajority_binary",
)


def replay(data, targets, execution, gross_cap, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
    )


def vote_fraction(index, parent_returns, persistent_returns):
    votes = []
    for days in WINDOWS:
        lookback = days * 24
        min_periods = lookback // 2
        p_mean = parent_returns.rolling(lookback, min_periods=min_periods).mean()
        p_std = parent_returns.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        c_mean = persistent_returns.rolling(lookback, min_periods=min_periods).mean()
        c_std = persistent_returns.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        p_score = p_mean.div(p_std)
        c_score = c_mean.div(c_std)
        votes.append(c_score.gt(p_score).astype(float))
    fraction = pd.concat(votes, axis=1).mean(axis=1)
    event = pd.Series(np.arange(len(index)) % 24 == 0, index=index)
    return fraction.where(event, np.nan).ffill().fillna(0.0)


def persistent_weight(vote: pd.Series, variant: str) -> pd.Series:
    if variant == "proportional_control":
        return vote.clip(0.0, 1.0)
    if variant == "majority_ramp":
        # No persistent allocation without a strict majority. Four, five and
        # six votes map to 1/3, 2/3 and 1 respectively.
        return ((vote - 0.5) * 2.0).clip(0.0, 1.0)
    if variant == "supermajority_ramp":
        # Requires at least five of six votes before meaningful allocation.
        return ((vote - (2.0 / 3.0)) * 3.0).clip(0.0, 1.0)
    if variant == "supermajority_binary":
        return vote.ge(5.0 / 6.0).astype(float)
    raise ValueError(variant)


def eval_all(equity, parent_equity, required, anti):
    full = summary(equity)
    pfull = summary(parent_equity)
    req = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in required
    }
    ah = {
        str(d): {"v99": horizon_summary(equity, d), "parent": horizon_summary(parent_equity, d)}
        for d in anti
    }
    roll = {str(d): rolling_robustness(parent_equity, equity, d) for d in anti}
    years = calendar_year_summaries(equity)
    py = calendar_year_summaries(parent_equity)
    common = sorted(set(years) & set(py))
    return {
        "full": full,
        "full_wealth_ratio_to_parent": (1.0 + full["return"]) / (1.0 + pfull["return"]),
        "full_drawdown_improvement_fraction": 1.0 - abs(full["max_drawdown"]) / abs(pfull["max_drawdown"]),
        "requested": req,
        "anti_overfit": ah,
        "anti_overfit_beat_fraction": sum(
            ah[str(d)]["v99"]["return"] > ah[str(d)]["parent"]["return"] for d in anti
        ) / len(anti),
        "rolling": roll,
        "rolling_average_parent_beat_fraction": sum(
            v["candidate_beats_parent_fraction"] for v in roll.values()
        ) / len(roll),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(
            years[y]["return"] > py[y]["return"] for y in common
        ) / max(1, len(common)),
        "tail": tail_and_capture(parent_equity, equity),
    }


def required_floor(result, minimum_return_ratio=0.95, maximum_dd_ratio=1.05):
    checks = {}
    for days, pair in result["requested"].items():
        c = pair["v99"]
        p = pair["parent"]
        if p["return"] > 0.0:
            return_ok = c["return"] >= minimum_return_ratio * p["return"]
        else:
            return_ok = c["return"] >= p["return"]
        pdd = abs(p["max_drawdown"])
        cdd = abs(c["max_drawdown"])
        dd_ok = cdd <= (maximum_dd_ratio * pdd + 1e-12)
        checks[days] = {
            "return_ok": bool(return_ok),
            "drawdown_ok": bool(dd_ok),
            "candidate_return": c["return"],
            "parent_return": p["return"],
            "candidate_drawdown": c["max_drawdown"],
            "parent_drawdown": p["max_drawdown"],
        }
    return checks, all(v["return_ok"] and v["drawdown_ok"] for v in checks.values())


def main():
    c = json.loads(CONFIG_PATH.read_text())
    p = json.loads((PROJECT / "config" / c["parent_candidate_config"]).read_text())
    if c.get("mode") != "PAPER_ONLY" or c.get("real_orders"):
        raise RuntimeError("R13 must remain paper only and orderless")

    data, parent_targets, parent_result, _, quarantined = build_v16(p)
    execution = load_execution(p)
    spec = V99AsymmetricSpec(**c["asymmetric_overlay"])
    ctrl = V99R4ControlSpec(**c["r4_control"])
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    r5, diag = asymmetric_v99_targets_r5(data, parent_targets, proxy, spec, ctrl)

    # R10/R12 structural discovery: normal signal changes benefit from
    # persistence, while side-aware emergency protection must remain immediate.
    routine = r5.shift(4).fillna(0.0)
    shock_long, shock_short, _ = _sparse_side_shock(data.close, parent_targets, ctrl)
    long_factor = pd.concat([diag["long_risk_factor"].astype(float), shock_long], axis=1).min(axis=1)
    short_factor = pd.concat([diag["short_risk_factor"].astype(float), shock_short], axis=1).min(axis=1)
    persistent = _cap_gross(
        routine.clip(lower=0.0).mul(long_factor, axis=0)
        + routine.clip(upper=0.0).mul(short_factor, axis=0),
        spec.maximum_gross,
    )

    base_cost = execution["base_cost_per_side"]
    parent_screen_returns = screen(data, parent_targets, base_cost).equity.pct_change(fill_method=None).fillna(0.0)
    persistent_screen_returns = screen(data, persistent, base_cost).equity.pct_change(fill_method=None).fillna(0.0)
    votes = vote_fraction(data.close.index, parent_screen_returns, persistent_screen_returns)

    required = [int(v) for v in c["research_gate"]["required_horizons_days"]]
    anti = [int(v) for v in c["research_gate"]["anti_overfit_horizons_days"]]
    gross_cap = float(c["circuit_breaker"]["gross_drift_guard_cap"])
    pg = p["circuit_breaker"]
    parent_severe = exact_fast(
        data,
        parent_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=pg["drawdown_threshold"],
        drawdown_guard_multiplier=pg["exposure_multiplier"],
        drawdown_guard_cooldown_hours=pg["cooldown_hours"],
    )
    parent_severe_summary = summary(parent_severe.equity)

    results = {}
    for variant in VARIANTS:
        pw = persistent_weight(votes, variant)
        mixed = parent_targets.mul(1.0 - pw, axis=0).add(persistent.mul(pw, axis=0), fill_value=0.0)
        mixed = _cap_gross(mixed, spec.maximum_gross)
        base = replay(data, mixed, execution, gross_cap, base_cost)
        severe = replay(data, mixed, execution, gross_cap, execution["severe_cost_per_side"])
        r = eval_all(base.equity, parent_result.equity, required, anti)
        r["severe_cost"] = summary(severe.equity)
        r["parent_severe"] = parent_severe_summary
        r["severe_wealth_ratio_to_parent"] = (
            (1.0 + r["severe_cost"]["return"]) / (1.0 + parent_severe_summary["return"])
        )
        r["turnover_total"] = float(base.turnover.sum())
        r["persistent_weight_mean"] = float(pw.mean())
        r["persistent_weight_high_fraction"] = float(pw.ge(2.0 / 3.0).mean())
        r["no_ruin"] = not (base.ruin or severe.ruin)
        floor_checks, floor_passed = required_floor(r)
        r["required_floor_checks"] = floor_checks
        r["required_floor_passed"] = floor_passed
        tail = r["tail"]
        r["eligible"] = bool(
            r["no_ruin"]
            and floor_passed
            and r["full_wealth_ratio_to_parent"] >= 1.0
            and r["full_drawdown_improvement_fraction"] >= -0.02
            and r["severe_wealth_ratio_to_parent"] >= 1.0
            and r["rolling_average_parent_beat_fraction"] >= 0.50
            and r["calendar_year_beat_fraction"] >= 4.0 / 7.0
            and tail["bottom10_damage_improvement_fraction"] >= 0.0
            and tail["worst_day_improvement_fraction"] >= -0.05
            and tail["top_winner_capture"] >= 0.95
        )
        results[variant] = r

    eligible = [name for name in VARIANTS if results[name]["eligible"]]
    # ROI is the objective only after the V16 floor and robustness constraints
    # are satisfied. This prevents a high-return fragile variant from winning.
    ranked = sorted(
        eligible,
        key=lambda name: (
            results[name]["full"]["return"],
            results[name]["severe_cost"]["return"],
            -abs(results[name]["full"]["max_drawdown"]),
        ),
        reverse=True,
    )
    selected = ranked[0] if ranked else None

    report = {
        "study": "V99 R13 maximize ROI subject to V16 floor and broad robustness",
        "objective": "maximize full-history ROI only among candidates that first satisfy the V16 return/risk floor, rolling/calendar robustness, tail preservation and severe-cost constraints",
        "allocator_windows_days": list(WINDOWS),
        "required_floor": {"minimum_return_ratio_to_v16": 0.95, "maximum_drawdown_ratio_to_v16": 1.05},
        "selected_variant": selected,
        "ranking": ranked,
        "parent": summary(parent_result.equity),
        "results": results,
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
