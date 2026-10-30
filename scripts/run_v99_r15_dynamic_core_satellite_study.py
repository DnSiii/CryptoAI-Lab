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
from run_candidate_v99 import (
    calendar_year_summaries,
    horizon_summary,
    rolling_robustness,
    summary,
    tail_and_capture,
)
from run_v99_r14_core_satellite_study import persistent_result

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r15_dynamic_core_satellite_study.json"
WINDOWS = (45, 60, 90, 120, 180, 240)
MAX_SATELLITE_WEIGHTS = (0.05, 0.10, 0.20, 0.30, 0.40)
REBALANCE_HOURS = (24, 24 * 7, 24 * 30)


def trailing_vote(parent_equity: pd.Series, satellite_equity: pd.Series) -> pd.Series:
    p = parent_equity.pct_change(fill_method=None).fillna(0.0)
    s = satellite_equity.pct_change(fill_method=None).fillna(0.0)
    votes = []
    for days in WINDOWS:
        lookback = days * 24
        min_periods = lookback // 2
        p_score = p.rolling(lookback, min_periods=min_periods).mean().div(
            p.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        )
        s_score = s.rolling(lookback, min_periods=min_periods).mean().div(
            s.rolling(lookback, min_periods=min_periods).std().replace(0.0, np.nan)
        )
        votes.append(s_score.gt(p_score).astype(float))
    return pd.concat(votes, axis=1).mean(axis=1).fillna(0.0)


def desired_satellite_weight(vote: pd.Series, maximum_weight: float) -> pd.Series:
    # Strict-majority ramp: no satellite allocation at 3/6 votes or below;
    # 4/6 -> one third of cap, 5/6 -> two thirds, 6/6 -> full cap.
    conviction = ((vote - 0.5) * 2.0).clip(0.0, 1.0)
    return conviction * maximum_weight


def combine_dynamic(
    parent_equity: pd.Series,
    satellite_equity: pd.Series,
    target_satellite: pd.Series,
    rebalance_hours: int,
    transfer_cost_per_side: float,
):
    aligned = pd.concat(
        [
            parent_equity.rename("parent"),
            satellite_equity.rename("satellite"),
            target_satellite.rename("target_satellite"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    pr = aligned["parent"].pct_change(fill_method=None).fillna(0.0)
    sr = aligned["satellite"].pct_change(fill_method=None).fillna(0.0)
    target = aligned["target_satellite"].clip(0.0, 1.0)

    parent_cap = 1.0
    satellite_cap = 0.0
    equity = pd.Series(index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    realized_satellite_weight = pd.Series(0.0, index=aligned.index)
    transfer_cost_total = 0.0

    for i in range(1, len(aligned)):
        parent_cap *= 1.0 + float(pr.iloc[i])
        satellite_cap *= 1.0 + float(sr.iloc[i])
        total = parent_cap + satellite_cap
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            break
        # Vote at close i is observable now and is used only for subsequent
        # returns. Rebalancing happens after applying hour i's realized return.
        if i % rebalance_hours == 0:
            desired = float(target.iloc[i])
            current = satellite_cap / total
            moved_fraction = abs(current - desired)
            cost = total * moved_fraction * 2.0 * transfer_cost_per_side
            transfer_cost_total += cost
            total = max(0.0, total - cost)
            satellite_cap = total * desired
            parent_cap = total * (1.0 - desired)
        equity.iloc[i] = parent_cap + satellite_cap
        realized_satellite_weight.iloc[i] = satellite_cap / max(parent_cap + satellite_cap, 1e-12)

    return equity.ffill().fillna(1.0), realized_satellite_weight, float(transfer_cost_total)


def evaluate(equity, parent_equity, required, anti):
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
    rolling = {str(d): rolling_robustness(parent_equity, equity, d) for d in anti}
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
        "rolling_average_parent_beat_fraction": sum(
            v["candidate_beats_parent_fraction"] for v in rolling.values()
        ) / len(rolling),
        "calendar_years": years,
        "calendar_year_beat_fraction": sum(
            years[y]["return"] > py[y]["return"] for y in common
        ) / max(1, len(common)),
        "tail": tail_and_capture(parent_equity, equity),
    }


def floor_pass(result, return_ratio=0.99, dd_ratio=1.03):
    checks = {}
    passed = True
    for days, pair in result["requested"].items():
        c, p = pair["v99"], pair["parent"]
        if p["return"] > 0.0:
            ret_ok = c["return"] >= return_ratio * p["return"]
        else:
            ret_ok = c["return"] >= p["return"]
        dd_ok = abs(c["max_drawdown"]) <= dd_ratio * abs(p["max_drawdown"]) + 1e-12
        checks[days] = {"return_ok": bool(ret_ok), "drawdown_ok": bool(dd_ok)}
        passed = passed and ret_ok and dd_ok
    return checks, bool(passed)


def main():
    c = json.loads(CONFIG_PATH.read_text())
    p = json.loads((PROJECT / "config" / c["parent_candidate_config"]).read_text())
    if c.get("mode") != "PAPER_ONLY" or c.get("real_orders"):
        raise RuntimeError("R15 is paper-only research")

    data, parent_base_targets, parent_base, _, quarantined = build_v16(p)
    execution = load_execution(p)
    spec = V99AsymmetricSpec(**c["asymmetric_overlay"])
    ctrl = V99R4ControlSpec(**c["r4_control"])
    satellite_base = persistent_result(
        data, parent_base_targets, execution, spec, ctrl, execution["base_cost_per_side"]
    )

    pg = p["circuit_breaker"]
    parent_severe = exact_fast(
        data,
        parent_base_targets,
        cost_per_side=execution["severe_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=2.0,
        drawdown_guard_threshold=pg["drawdown_threshold"],
        drawdown_guard_multiplier=pg["exposure_multiplier"],
        drawdown_guard_cooldown_hours=pg["cooldown_hours"],
    )
    satellite_severe = persistent_result(
        data, parent_base_targets, execution, spec, ctrl, execution["severe_cost_per_side"]
    )

    vote = trailing_vote(parent_base.equity, satellite_base.equity)
    required = [int(v) for v in c["research_gate"]["required_horizons_days"]]
    anti = [int(v) for v in c["research_gate"]["anti_overfit_horizons_days"]]
    parent_severe_summary = summary(parent_severe.equity)

    results = {}
    for max_weight in MAX_SATELLITE_WEIGHTS:
        desired = desired_satellite_weight(vote, max_weight)
        by_frequency = {}
        for hours in REBALANCE_HOURS:
            equity, realized, transfer_cost = combine_dynamic(
                parent_base.equity,
                satellite_base.equity,
                desired,
                hours,
                execution["base_cost_per_side"],
            )
            severe_equity, _, severe_transfer_cost = combine_dynamic(
                parent_severe.equity,
                satellite_severe.equity,
                desired,
                hours,
                execution["severe_cost_per_side"],
            )
            r = evaluate(equity, parent_base.equity, required, anti)
            r["severe_cost"] = summary(severe_equity)
            r["parent_severe"] = parent_severe_summary
            r["severe_wealth_ratio_to_parent"] = (
                (1.0 + r["severe_cost"]["return"])
                / (1.0 + parent_severe_summary["return"])
            )
            r["mean_realized_satellite_weight"] = float(realized.mean())
            r["max_realized_satellite_weight"] = float(realized.max())
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
                and r["rolling_average_parent_beat_fraction"] >= 0.50
                and r["calendar_year_beat_fraction"] >= 4.0 / 7.0
                and tail["bottom10_damage_improvement_fraction"] >= 0.0
                and tail["worst_day_improvement_fraction"] >= -0.02
                and tail["top_winner_capture"] >= 0.98
            )
            by_frequency[str(hours)] = r

        daily = by_frequency["24"]
        weekly = by_frequency[str(24 * 7)]
        # Daily and weekly must both pass; monthly is retained as a perturbation
        # stress report rather than a selection knob.
        eligible = bool(daily["robust_passed"] and weekly["robust_passed"])
        results[f"max_satellite_{int(round(max_weight * 100))}pct"] = {
            "maximum_satellite_weight": max_weight,
            "eligible": eligible,
            "baseline_daily": daily,
            "frequency_results": by_frequency,
        }

    eligible = [k for k, v in results.items() if v["eligible"]]
    ranking = sorted(
        eligible,
        key=lambda k: (
            results[k]["baseline_daily"]["full"]["return"],
            results[k]["baseline_daily"]["severe_cost"]["return"],
            -abs(results[k]["baseline_daily"]["full"]["max_drawdown"]),
        ),
        reverse=True,
    )
    report = {
        "study": "V99 R15 dynamic V16 core with consensus-gated alpha satellite",
        "objective": "maximize ROI subject to at least 99% of V16 positive-horizon return, tight drawdown floor, tail preservation, severe cost resilience and daily/weekly rebalance robustness",
        "windows_days": list(WINDOWS),
        "maximum_satellite_weights": list(MAX_SATELLITE_WEIGHTS),
        "selected": ranking[0] if ranking else None,
        "ranking": ranking,
        "parent": summary(parent_base.equity),
        "satellite": summary(satellite_base.equity),
        "results": results,
        "funding_quarantined_symbols": quarantined,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
