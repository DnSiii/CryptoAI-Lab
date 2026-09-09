from __future__ import annotations

import gc
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r40_tail_lift_hedge as r40

r36 = r40.r36
r37 = r40.r37
cap = r40.cap
REPORT = PROJECT / "reports" / "candidate_v99_r50_crash_deleveraging_overlay.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)

R40_FIXED = {
    "name": "broad_q80_net",
    "net_abs": 0.8752233748404276,
    "btc_abs3": 0.011464117595499812,
    "breadth_abs2": 0.0661764705882353,
    "cross_vol": 0.012670447074253053,
    "extra_hedge": 0.10,
    "cooldown": 12,
    "gross_cap": 1.90,
}

# Exact R37 predeclared crash presets. No signal retuning in R50.
CRASH_PRESETS = (
    {"name": "early", "r6_trigger": -0.025, "dd_trigger": -0.050, "r24_trigger": -0.040, "btc24_trigger": -0.035, "btc72_trigger": -0.070, "cooldown": 6},
    {"name": "medium", "r6_trigger": -0.035, "dd_trigger": -0.070, "r24_trigger": -0.055, "btc24_trigger": -0.045, "btc72_trigger": -0.090, "cooldown": 12},
    {"name": "deep", "r6_trigger": -0.045, "dd_trigger": -0.090, "r24_trigger": -0.070, "btc24_trigger": -0.055, "btc72_trigger": -0.110, "cooldown": 24},
)
# Exact complements of R37's safe-weight grid 0.50 / 0.35 / 0.20.
RISK_SCALES = (0.50, 0.65, 0.80)


def build_parent(data, raw, ex, guard, gross, cost):
    return r40.build_candidate(data, raw, ex, guard, gross, cost, R40_FIXED)


def apply_overlay(data, parent_targets, r30_equity, ex, guard, cost, p):
    active, signal_diag = r37.crash_signal(
        r30_equity.reindex(parent_targets.index),
        data.close["BTCUSDT"].reindex(parent_targets.index),
        p,
    )
    a = active.reindex(parent_targets.index).fillna(False).astype(float)
    scale = 1.0 - a * (1.0 - float(p["risk_scale"]))
    targets = parent_targets.mul(scale, axis=0)
    targets = cap(targets, float(R40_FIXED["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(R40_FIXED["gross_cap"]), guard)
    return result, targets, active, signal_diag


def build_candidate(data, raw, ex, guard, gross, cost, p):
    parent, r30, parent_targets, parent_active, parent_diag = build_parent(
        data, raw, ex, guard, gross, cost
    )
    result, targets, crash_active, crash_diag = apply_overlay(
        data, parent_targets, r30.equity, ex, guard, cost, p
    )
    return result, parent, r30, targets, crash_active, {
        "r40": parent_diag,
        "crash": crash_diag,
        "r40_tail_active_fraction": float(parent_active.mean()),
    }


def isolated_candidate(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, parent, _, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity), r36.stats(parent.equity)


def benchmark_items(cand, data, raw, ex, guard, gross):
    v13_c, v13_d, v13_t, v13_ex, v13_kw = r36.build_v13_benchmark()
    v14_c, v14_d, v14_t, v14_ex, v14_kw = r36.build_v14_benchmark()
    v16_c, v16_d, v16_t, v16_ex, v16_kw = r36.build_v16_benchmark()
    return {
        "v13": {"candidate": v13_c, "data": v13_d, "targets": v13_t, "execution": v13_ex, "kwargs": v13_kw},
        "v14": {"candidate": v14_c, "data": v14_d, "targets": v14_t, "execution": v14_ex, "kwargs": v14_kw},
        "v15": {"candidate": cand, "data": data, "targets": raw, "execution": ex, "kwargs": {
            "maintenance_equity_fraction": ex["maintenance_equity_fraction"],
            "gross_guard_cap": gross,
            "drawdown_guard_threshold": guard["drawdown_threshold"],
            "drawdown_guard_multiplier": guard["exposure_multiplier"],
            "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
        }},
        "v16": {"candidate": v16_c, "data": v16_d, "targets": v16_t, "execution": v16_ex, "kwargs": v16_kw},
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    parent, r30, parent_targets, _, parent_diag = build_parent(data, raw, ex, guard, gross, base_cost)
    parent_stats = r36.stats(parent.equity)
    parent_hold_start = parent.equity.index[min(int(len(parent.equity) * 0.60) + 1, len(parent.equity) - 1)]
    parent_hold = r36.stats(parent.equity.loc[parent_hold_start:])

    parent_sev, r30_sev, parent_targets_sev, _, _ = build_parent(data, raw, ex, guard, gross, severe_cost)
    parent_severe_stats = r36.stats(parent_sev.equity)

    benchmarks = benchmark_items(cand, data, raw, ex, guard, gross)
    full_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    full_env = r36.envelope(full_bench)
    severe_env = r36.envelope(severe_bench)

    rows = []
    for preset, risk_scale in itertools.product(CRASH_PRESETS, RISK_SCALES):
        p = {**preset, "risk_scale": risk_scale}
        result, _, active, diag = apply_overlay(
            data, parent_targets, r30.equity, ex, guard, base_cost, p
        )
        s = r36.stats(result.equity)
        hold = r36.stats(result.equity.loc[parent_hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        parent_wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + parent_stats["return"])
        hold_parent = (1.0 + hold["return"]) / max(1e-12, 1.0 + parent_hold["return"])
        score = (
            10.0 * np.log(max(return_env, 1e-12))
            + 6.0 * np.log(max(hold_parent, 1e-12))
            + 18.0 * max(0.0, 1.0 - dd_env)
            - 18.0 * max(0.0, dd_env - 1.0)
            + 16.0 * max(0.0, 1.0 - worst_env)
            - 18.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "active_fraction": float(active.mean()),
            "diagnostics": diag,
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "wealth_ratio_to_r40": float(parent_wealth),
            "holdout_wealth_ratio_to_r40": float(hold_parent),
            "score": float(score),
        })
        gc.collect()

    rows.sort(key=lambda x: x["score"], reverse=True)
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []

    for row in rows:
        p = row["params"]
        isolated, isolated_parent, isolated_bench, wins, material = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c, par = isolated_candidate(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            isolated[k], isolated_parent[k], isolated_bench[k] = c, par, bench
            wins[k] = {
                "return": c["return"] >= env["return"],
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
            }
            material[k] = {
                "return": c["return"] >= env["return"] + r36.metric_margin(env["return"]),
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"] * 0.95,
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"] * 0.95,
            }

        alternative = {}
        for days in ALT_HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            if start < earliest:
                continue
            c, par = isolated_candidate(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alternative[str(days)] = {
                "candidate": c,
                "r40": par,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        sev_result, _, sev_active, sev_diag = apply_overlay(
            data, parent_targets_sev, r30_sev.equity, ex, guard, severe_cost, p
        )
        sev = r36.stats(sev_result.equity)
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_dd_pass = abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
        full_worst_pass = abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_dd_pass = abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
        severe_worst_pass = abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        requested_wins = sum(sum(v.values()) for v in wins.values())
        requested_material = sum(sum(v.values()) for v in material.values())
        alt_all = bool(alternative) and all(
            x["return_win"] and x["drawdown_win"] and x["worst_day_win"]
            for x in alternative.values()
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_r40": isolated_parent,
            "isolated_benchmarks": isolated_bench,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alternative,
            "severe_cost": sev,
            "severe_active_fraction": float(sev_active.mean()),
            "severe_diagnostics": sev_diag,
            "full_return_pass": full_return_pass,
            "full_drawdown_pass": full_dd_pass,
            "full_worst_day_pass": full_worst_pass,
            "severe_return_pass": severe_return_pass,
            "severe_drawdown_pass": severe_dd_pass,
            "severe_worst_day_pass": severe_worst_pass,
            "requested_horizon_dimension_wins": int(requested_wins),
            "requested_horizon_material_wins": int(requested_material),
            "all_alternative_envelopes_won": alt_all,
            "dominant_gate_passed": bool(
                full_return_pass and full_dd_pass and full_worst_pass
                and severe_return_pass and severe_dd_pass and severe_worst_pass
                and requested_wins == 15 and requested_material == 15 and alt_all
            ),
        })
        gc.collect()

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["requested_horizon_material_wins"],
            z["requested_horizon_dimension_wins"],
            z["all_alternative_envelopes_won"],
            z["full_return_pass"], z["full_drawdown_pass"], z["full_worst_day_pass"],
            z["severe_return_pass"], z["severe_drawdown_pass"], z["severe_worst_day_pass"],
            z["holdout_wealth_ratio_to_r40"],
            z["score"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R50 fixed-R40 crash deleveraging overlay",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": (
            "apply the exact causal R37 crash detector directly to a fixed R40 target book by temporarily "
            "reducing gross exposure, rather than routing capital through continuously maintained sleeves; "
            "seek R37-like tail protection with execution costs naturally modeled by the underlying engine"
        ),
        "parent_r40_fixed": R40_FIXED,
        "parent_r40_summary": parent_stats,
        "parent_r40_severe": parent_severe_stats,
        "parent_r40_diagnostics": parent_diag,
        "grid_policy": "9 predeclared combinations = exact 3 R37 crash presets x exact complements of R37 safe-weight grid (risk scales 0.50/0.65/0.80); no new signal thresholds",
        "grid_size": 9,
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "disclosure": (
            "Research only. R40 parent is fixed. Crash thresholds and risk scales are inherited unchanged from "
            "previously predeclared R37 choices. No frozen engine or paper state is modified."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "parent": parent_stats, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    main()
