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

import run_v99_r55_low_hedge_amplitude_frontier as r55

r36 = r55.r36
r37 = r55.r37
cap = r55.cap
REPORT = PROJECT / "reports" / "candidate_v99_r59_h15_mild_crash.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
PARENT = {**r55.FIXED, "hedge_size": 0.15}

CRASH_PRESETS = (
    {"name": "medium", "r6_trigger": -0.035, "dd_trigger": -0.070, "r24_trigger": -0.055,
     "btc24_trigger": -0.045, "btc72_trigger": -0.090, "cooldown": 12},
    {"name": "deep", "r6_trigger": -0.045, "dd_trigger": -0.090, "r24_trigger": -0.070,
     "btc24_trigger": -0.055, "btc72_trigger": -0.110, "cooldown": 24},
)
RISK_SCALES = (0.85, 0.90, 0.95)


def build_parent(data, raw, ex, guard, gross, cost):
    shadow = r36.run(data, raw, ex, cost, gross, guard)
    return r55.build_with_shadow(data, raw, ex, guard, gross, cost, PARENT, shadow=shadow)


def apply_overlay(data, parent, parent_targets, ex, guard, cost, p):
    active, diag = r37.crash_signal(
        parent.equity.reindex(parent_targets.index),
        data.close["BTCUSDT"].reindex(parent_targets.index),
        p,
    )
    a = active.reindex(parent_targets.index).fillna(False).astype(float)
    scale = 1.0 - a * (1.0 - float(p["risk_scale"]))
    targets = cap(parent_targets.mul(scale, axis=0), float(PARENT["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(PARENT["gross_cap"]), guard)
    return result, targets, active, diag


def build_candidate(data, raw, ex, guard, gross, cost, p):
    parent, shadow, parent_targets, parent_active = build_parent(data, raw, ex, guard, gross, cost)
    result, targets, crash_active, crash_diag = apply_overlay(
        data, parent, parent_targets, ex, guard, cost, p
    )
    return result, parent, shadow, targets, crash_active, {
        "parent_hedge_active_fraction": float(parent_active.mean()),
        "crash": crash_diag,
    }


def isolated(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, parent, _, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity), r36.stats(parent.equity)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    parent, _, parent_targets, parent_active = build_parent(data, raw, ex, guard, gross, base_cost)
    parent_sev, _, parent_targets_sev, parent_active_sev = build_parent(
        data, raw, ex, guard, gross, severe_cost
    )
    parent_stats = r36.stats(parent.equity)
    parent_severe = r36.stats(parent_sev.equity)
    split = int(len(parent.equity) * 0.60)
    hold_start = parent.equity.index[min(split + 1, len(parent.equity) - 1)]
    parent_hold = r36.stats(parent.equity.loc[hold_start:])

    benchmarks = r55.benchmark_items(cand, data, raw, ex, guard, gross)
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
            data, parent, parent_targets, ex, guard, base_cost, p
        )
        sev_result, _, sev_active, sev_diag = apply_overlay(
            data, parent_sev, parent_targets_sev, ex, guard, severe_cost, p
        )
        s = r36.stats(result.equity)
        sev = r36.stats(sev_result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        sev_return_env = (1.0 + sev["return"]) / max(1e-12, 1.0 + severe_env["return"])
        parent_wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + parent_stats["return"])
        hold_parent = (1.0 + hold["return"]) / max(1e-12, 1.0 + parent_hold["return"])
        score = (
            10.0 * np.log(max(return_env, 1e-12))
            + 6.0 * np.log(max(sev_return_env, 1e-12))
            + 5.0 * np.log(max(hold_parent, 1e-12))
            + 20.0 * max(0.0, 1.0 - dd_env)
            - 22.0 * max(0.0, dd_env - 1.0)
            + 18.0 * max(0.0, 1.0 - worst_env)
            - 20.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "severe_cost": sev,
            "active_fraction": float(active.mean()),
            "severe_active_fraction": float(sev_active.mean()),
            "diagnostics": diag,
            "severe_diagnostics": sev_diag,
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "severe_return_ratio_to_envelope": float(sev_return_env),
            "wealth_ratio_to_parent": float(parent_wealth),
            "holdout_wealth_ratio_to_parent": float(hold_parent),
            "score": float(score),
        })
        gc.collect()

    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []

    for row in rows:
        p = row["params"]
        isolated_stats, isolated_parent, isolated_bench, wins, material = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c, par = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            isolated_stats[k], isolated_parent[k], isolated_bench[k] = c, par, bench
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
            c, par = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alternative[str(days)] = {
                "candidate": c,
                "parent": par,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        horizon_wins = sum(sum(v.values()) for v in wins.values())
        material_wins = sum(sum(v.values()) for v in material.values())
        alt_wins = sum(
            int(v["return_win"]) + int(v["drawdown_win"]) + int(v["worst_day_win"])
            for v in alternative.values()
        )
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_dd_pass = abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
        full_worst_pass = abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        severe_return_pass = row["severe_cost"]["return"] >= severe_env["return"]
        severe_dd_pass = abs(row["severe_cost"]["max_drawdown"]) <= severe_env["max_drawdown_abs"]
        severe_worst_pass = abs(row["severe_cost"]["worst_day"]) <= severe_env["worst_day_abs"]
        finalists.append({
            **row,
            "isolated": isolated_stats,
            "isolated_parent": isolated_parent,
            "isolated_benchmarks": isolated_bench,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alternative,
            "requested_horizon_dimension_wins": int(horizon_wins),
            "requested_horizon_material_wins": int(material_wins),
            "alternative_dimension_wins": int(alt_wins),
            "full_return_pass": full_return_pass,
            "full_drawdown_pass": full_dd_pass,
            "full_worst_day_pass": full_worst_pass,
            "severe_return_pass": severe_return_pass,
            "severe_drawdown_pass": severe_dd_pass,
            "severe_worst_day_pass": severe_worst_pass,
            "dominant_gate_passed": bool(
                full_return_pass and full_dd_pass and full_worst_pass
                and severe_return_pass and severe_dd_pass and severe_worst_pass
                and horizon_wins == 15 and material_wins == 15
                and all(v["return_win"] and v["drawdown_win"] and v["worst_day_win"] for v in alternative.values())
            ),
        })
        gc.collect()

    finalists.sort(key=lambda z: (
        z["dominant_gate_passed"],
        z["requested_horizon_material_wins"],
        z["requested_horizon_dimension_wins"],
        z["alternative_dimension_wins"],
        z["full_return_pass"], z["severe_return_pass"],
        z["full_dd_pass"], z["full_worst_pass"],
        z["severe_dd_pass"], z["severe_worst_pass"],
        z["score"],
    ), reverse=True)
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R59 hedge-0.15 parent + mild crash deleveraging",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": (
            "preserve the R55 hedge-0.15 return/cost frontier and spend only part of its one-year and severe-cost "
            "margin on the already validated R37 medium/deep crash detector using mild 5%, 10% and 15% gross cuts"
        ),
        "parent_fixed": PARENT,
        "parent_summary": parent_stats,
        "parent_holdout": parent_hold,
        "parent_severe": parent_severe,
        "parent_hedge_active_fraction": float(parent_active.mean()),
        "parent_severe_hedge_active_fraction": float(parent_active_sev.mean()),
        "grid_policy": "6 predeclared combinations = exact R37 medium/deep presets x fixed mild risk scales 0.85/0.90/0.95; no early detector and no signal retuning",
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "disclosure": "Historical research only. Crash signal uses only information available through t and the existing causal execution engine. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
