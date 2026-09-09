from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r50_crash_deleveraging_overlay as base

r36 = base.r36
r37 = base.r37
cap = base.cap
REPORT = PROJECT / "reports" / "candidate_v99_r55_low_hedge_amplitude_frontier.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
HEDGE_SIZES = (0.10, 0.15, 0.20, 0.25)
FIXED = {
    "dd_trigger": 0.06,
    "cooldown": 72,
    "market_level": 1,
    "min_net": 0.10,
    "gross_cap": 1.90,
}


def params(hedge_size: float) -> dict:
    return {**FIXED, "hedge_size": float(hedge_size)}


def build_with_shadow(data, raw, ex, guard, gross, cost, p, shadow=None):
    if shadow is None:
        shadow = r36.run(data, raw, ex, cost, gross, guard)
    targets, active = r37.r30_targets(raw, shadow.equity, data.close, p)
    targets = cap(targets, float(p["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(p["gross_cap"]), guard)
    return result, shadow, targets, active


def isolated(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, _, _, _ = build_with_shadow(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity)


def benchmark_items(cand, data, raw, ex, guard, gross):
    return base.benchmark_items(cand, data, raw, ex, guard, gross)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    core = r36.run(data, raw, ex, base_cost, gross, guard)
    core_severe = r36.run(data, raw, ex, severe_cost, gross, guard)

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

    split = int(len(core.equity) * 0.60)
    hold_start = core.equity.index[min(split + 1, len(core.equity) - 1)]

    rows = []
    for hedge_size in HEDGE_SIZES:
        p = params(hedge_size)
        result, _, _, active = build_with_shadow(
            data, raw, ex, guard, gross, base_cost, p, shadow=core
        )
        sev_result, _, _, sev_active = build_with_shadow(
            data, raw, ex, guard, gross, severe_cost, p, shadow=core_severe
        )
        s = r36.stats(result.equity)
        sev = r36.stats(sev_result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        severe_return_env = (1.0 + sev["return"]) / max(1e-12, 1.0 + severe_env["return"])
        score = (
            8.0 * np.log(max(return_env, 1e-12))
            + 5.0 * np.log(max(severe_return_env, 1e-12))
            + 10.0 * max(0.0, 1.0 - dd_env)
            - 12.0 * max(0.0, dd_env - 1.0)
            + 8.0 * max(0.0, 1.0 - worst_env)
            - 10.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "severe_cost": sev,
            "hedge_active_fraction": float(active.mean()),
            "severe_hedge_active_fraction": float(sev_active.mean()),
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "severe_return_ratio_to_envelope": float(severe_return_env),
            "score": float(score),
        })
        gc.collect()

    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []
    for row in rows:
        p = row["params"]
        isolated_stats, isolated_bench, wins, material = {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            isolated_stats[k], isolated_bench[k] = c, bench
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
            c = isolated(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alternative[str(days)] = {
                "candidate": c,
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
                and horizon_wins == 15
                and all(v["return_win"] and v["drawdown_win"] and v["worst_day_win"] for v in alternative.values())
            ),
        })
        gc.collect()

    finalists.sort(key=lambda z: (
        z["dominant_gate_passed"],
        z["requested_horizon_material_wins"],
        z["requested_horizon_dimension_wins"],
        z["alternative_dimension_wins"],
        z["severe_return_pass"],
        z["full_return_pass"],
        z["score"],
    ), reverse=True)
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R55 low-hedge amplitude frontier",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "change only direct hedge amplitude around the cost-efficient R30 frontier to test whether 365d return can be recovered without surrendering severe-cost robustness",
        "fixed_parameters": FIXED,
        "hedge_sizes_predeclared": list(HEDGE_SIZES),
        "grid_policy": "one-dimensional 4-point grid; only hedge_size changes (0.10/0.15/0.20/0.25), all timing/stress/net/gross parameters fixed before the run",
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "disclosure": "Historical research only. Stress state uses information known by close t and targets execute through the existing causal engine. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
