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
REPORT = PROJECT / "reports" / "candidate_v99_r49_continuation_gross_brake.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)

# Fixed before R49: R40 selected structural frontier from R40 report.
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

# Thresholds are copied unchanged from R48's first-60%-chronological training split.
GATE_PRESETS = (
    {
        "name": "early_gross_xvol",
        "dd_min": 0.05,
        "dd_max": 0.12,
        "gross_min": 1.0872536731014524,
        "cross_vol_min": 0.009514317772473338,
        "net_min": None,
        "r48_holdout_lift_7d": 1.811248041440419,
    },
    {
        "name": "mid_gross_xvol",
        "dd_min": 0.08,
        "dd_max": 0.18,
        "gross_min": 1.136975439677298,
        "cross_vol_min": 0.00889784954080152,
        "net_min": None,
        "r48_holdout_lift_7d": 2.170296132721816,
    },
    {
        "name": "high_net_q95",
        "dd_min": 0.05,
        "dd_max": 0.18,
        "gross_min": None,
        "cross_vol_min": None,
        "net_min": 1.3708505397570574,
        "r48_holdout_lift_7d": 2.11619579713335,
    },
)


def continuation_gate(
    r30_equity: pd.Series,
    r30_targets: pd.DataFrame,
    close: pd.DataFrame,
    p: dict,
) -> tuple[pd.Series, dict]:
    idx = r30_equity.index.intersection(r30_targets.index).intersection(close.index)
    eq = r30_equity.reindex(idx).astype(float)
    t = r30_targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)

    dd_depth = (1.0 - eq / eq.cummax()).clip(lower=0.0)
    gross = t.abs().sum(axis=1)
    net_abs = t.sum(axis=1).abs()
    cross_vol = c.pct_change(fill_method=None).std(axis=1).fillna(0.0)

    state = (dd_depth >= p["dd_min"]) & (dd_depth < p["dd_max"])
    if p.get("net_min") is not None:
        risk = net_abs >= float(p["net_min"])
    else:
        risk = (
            (gross >= float(p["gross_min"]))
            & (cross_vol >= float(p["cross_vol_min"]))
        )
    instant = (state & risk).fillna(False)
    active = instant.astype(float).rolling(int(p["cooldown"]), min_periods=1).max().gt(0.0)

    return active, {
        "instant_fraction": float(instant.mean()),
        "active_fraction": float(active.mean()),
        "dd_depth_median_when_instant": float(dd_depth.loc[instant].median()) if instant.any() else 0.0,
        "gross_median_when_instant": float(gross.loc[instant].median()) if instant.any() else 0.0,
        "net_abs_median_when_instant": float(net_abs.loc[instant].median()) if instant.any() else 0.0,
        "cross_vol_median_when_instant": float(cross_vol.loc[instant].median()) if instant.any() else 0.0,
    }


def build_candidate(data, raw, ex, guard, gross, cost, p):
    # R40 is fixed. R30 shadow/targets are rebuilt only to evaluate the unchanged
    # R48 continuation feature definitions; the brake is applied to R40 targets.
    r40_result, r30_result, r40_targets, _, r40_diag = r40.build_candidate(
        data, raw, ex, guard, gross, cost, R40_FIXED
    )
    _, r30_targets, _ = r37.build_r30(data, raw, ex, guard, gross, cost)
    active, gate_diag = continuation_gate(r30_result.equity, r30_targets, data.close, p)

    a = active.reindex(r40_targets.index).fillna(False).astype(float)
    scale = 1.0 - a * (1.0 - float(p["risk_scale"]))
    targets = r40_targets.mul(scale, axis=0)
    targets = cap(targets, float(R40_FIXED["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(R40_FIXED["gross_cap"]), guard)
    return result, r40_result, targets, active, {"r40": r40_diag, "continuation": gate_diag}


def isolated_candidate(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, parent, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity), r36.stats(parent.equity)


def benchmarks_setup(cand, data, raw, ex, guard, gross):
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

    parent, _, _, _, parent_diag = r40.build_candidate(data, raw, ex, guard, gross, base_cost, R40_FIXED)
    parent_sev, _, _, _, _ = r40.build_candidate(data, raw, ex, guard, gross, severe_cost, R40_FIXED)
    parent_stats = r36.stats(parent.equity)
    parent_severe = r36.stats(parent_sev.equity)

    benchmarks = benchmarks_setup(cand, data, raw, ex, guard, gross)
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

    split = int(len(parent.equity) * 0.60)
    hold_start = parent.equity.index[min(split + 1, len(parent.equity) - 1)]
    parent_hold = r36.stats(parent.equity.loc[hold_start:])

    rows = []
    for preset, risk_scale, cooldown in itertools.product(
        GATE_PRESETS, (0.70, 0.82, 0.90), (24, 48, 72)
    ):
        p = {**preset, "risk_scale": risk_scale, "cooldown": cooldown}
        result, _, _, active, diag = build_candidate(data, raw, ex, guard, gross, base_cost, p)
        s = r36.stats(result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        parent_wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + parent_stats["return"])
        parent_hold_wealth = (1.0 + hold["return"]) / max(1e-12, 1.0 + parent_hold["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        score = (
            10.0 * np.log(max(return_env, 1e-12))
            + 6.0 * np.log(max(parent_hold_wealth, 1e-12))
            + 18.0 * max(0.0, 1.0 - dd_env)
            - 18.0 * max(0.0, dd_env - 1.0)
            + 10.0 * max(0.0, 1.0 - worst_env)
            - 12.0 * max(0.0, worst_env - 1.0)
            - 2.0 * max(0.0, 0.05 - float(active.mean()))
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "return_ratio_to_full_envelope": float(return_env),
            "wealth_ratio_to_r40": float(parent_wealth),
            "holdout_wealth_ratio_to_r40": float(parent_hold_wealth),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "active_fraction": float(active.mean()),
            "diagnostics": diag,
            "score": float(score),
        })
        gc.collect()

    rows.sort(key=lambda x: x["score"], reverse=True)
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []

    for row in rows[:7]:
        p = row["params"]
        isolated, isolated_parent, isolated_bench, wins = {}, {}, {}, {}
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

        sev_result, _, _, sev_active, sev_diag = build_candidate(
            data, raw, ex, guard, gross, severe_cost, p
        )
        sev = r36.stats(sev_result.equity)
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_dd_pass = abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
        full_worst_pass = abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_dd_pass = abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
        severe_worst_pass = abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        horizon_wins = sum(sum(v.values()) for v in wins.values())
        alt_wins = sum(
            int(v["return_win"]) + int(v["drawdown_win"]) + int(v["worst_day_win"])
            for v in alternative.values()
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_r40": isolated_parent,
            "isolated_benchmarks": isolated_bench,
            "envelope_wins": wins,
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
            "requested_horizon_dimension_wins": int(horizon_wins),
            "alternative_dimension_wins": int(alt_wins),
            "dominant_gate_passed": bool(
                full_return_pass and full_dd_pass and full_worst_pass
                and severe_return_pass and severe_dd_pass and severe_worst_pass
                and horizon_wins == 15
                and all(v["return_win"] and v["drawdown_win"] and v["worst_day_win"] for v in alternative.values())
            ),
        })
        gc.collect()

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["requested_horizon_dimension_wins"],
            z["alternative_dimension_wins"],
            z["full_return_pass"], z["full_drawdown_pass"], z["full_worst_day_pass"],
            z["severe_return_pass"], z["severe_drawdown_pass"], z["severe_worst_day_pass"],
            z["holdout_wealth_ratio_to_r40"],
            z["score"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R49 R40 continuation gross brake",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": (
            "retain fixed R40 structural return+drawdown frontier and scale gross exposure only during "
            "rare R48-validated moderate-drawdown states that showed stable out-of-sample lift for further "
            "drawdown deepening; avoid the broad persistent activation that caused R43 to sacrifice return"
        ),
        "parent_r40_fixed": R40_FIXED,
        "parent_r40_summary": parent_stats,
        "parent_r40_severe": parent_severe,
        "parent_r40_gate_diagnostics": parent_diag,
        "r48_gate_presets": GATE_PRESETS,
        "grid_policy": "27 predeclared combinations = 3 fixed R48 gates x 3 gross scales x 3 cooldowns; R40 parent and R48 thresholds fixed before this run",
        "grid_size": 27,
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "top_full_grid": rows[:15],
        "disclosure": (
            "Research only. R49 thresholds come unchanged from R48 train-only diagnostics. The R40 parent "
            "is fixed. No frozen engine or paper state is modified. Future horizons are validation gates, "
            "not inputs to the continuation signal."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_r40": parent_stats,
        "full_envelope": full_env,
        "selected": selected,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
