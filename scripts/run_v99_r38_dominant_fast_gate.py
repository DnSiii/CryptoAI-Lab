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

from run_v99_r25_trisleeve_meta import cap
import run_v99_r37_crash_shield as r37

r37.r36.cap = cap
r36 = r37.r36

REPORT = PROJECT / "reports" / "candidate_v99_r38_dominant_fast_gate.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def dominant_fast_gate(targets: pd.DataFrame, close: pd.DataFrame, p: dict):
    gross = targets.abs().sum(axis=1).replace(0.0, np.nan)
    share = targets.abs().div(gross, axis=0).fillna(0.0)
    top_share = share.max(axis=1)
    top_mask = share.eq(top_share, axis=0) & share.gt(0.0)
    sign = np.sign(targets)
    signed3 = sign * close.pct_change(3, fill_method=None)
    signed6 = sign * close.pct_change(6, fill_method=None)

    bad = (
        top_mask
        & (share >= p["share_trigger"])
        & ((signed3 <= -p["adverse3"]) | (signed6 <= -p["adverse6"]))
    ).fillna(False)
    if p["cooldown"] > 1:
        bad = bad.astype(float).rolling(int(p["cooldown"]), min_periods=1).max().gt(0.0)

    factor = pd.DataFrame(1.0, index=targets.index, columns=targets.columns).mask(bad, p["cut_scale"])
    adjusted = targets * factor * p["gross_multiplier"]
    adjusted = cap(adjusted, p["gross_cap"])
    return adjusted, bad, {
        "event_fraction": float(bad.to_numpy(dtype=float).mean()),
        "row_event_fraction": float(bad.any(axis=1).mean()),
        "mean_top_share": float(top_share.mean()),
        "p95_top_share": float(top_share.quantile(0.95)),
    }


def build_candidate(data, raw, ex, guard, gross, cost, p):
    r30_result, r30_targets, _ = r37.build_r30(data, raw, ex, guard, gross, cost)
    targets, bad, diag = dominant_fast_gate(r30_targets, data.close, p)
    result = r36.run(data, targets, ex, cost, p["gross_cap"], guard)
    return result, r30_result, targets, bad, diag


def isolated_candidate(data, raw, ex, guard, gross, cost, p, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    result, r30_result, _, _, _ = build_candidate(d, rr, ex, guard, gross, cost, p)
    return r36.stats(result.equity), r36.stats(r30_result.equity)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    r30_base, _, r30_hedge_active = r37.build_r30(data, raw, ex, guard, gross, base_cost)
    r30_severe, _, _ = r37.build_r30(data, raw, ex, guard, gross, severe_cost)
    r30_stats = r36.stats(r30_base.equity)
    r30_severe_stats = r36.stats(r30_severe.equity)

    v13_c, v13_d, v13_t, v13_ex, v13_kw = r36.build_v13_benchmark()
    v14_c, v14_d, v14_t, v14_ex, v14_kw = r36.build_v14_benchmark()
    v16_c, v16_d, v16_t, v16_ex, v16_kw = r36.build_v16_benchmark()
    benchmarks = {
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

    presets = (
        {"name": "early", "share_trigger": 0.40, "adverse3": 0.015, "adverse6": 0.025, "cooldown": 3},
        {"name": "medium", "share_trigger": 0.50, "adverse3": 0.020, "adverse6": 0.035, "cooldown": 6},
        {"name": "deep", "share_trigger": 0.60, "adverse3": 0.025, "adverse6": 0.045, "cooldown": 12},
    )

    split = int(len(r30_base.equity) * 0.60)
    hold_start = r30_base.equity.index[min(split + 1, len(r30_base.equity) - 1)]
    r30_hold = r36.stats(r30_base.equity.loc[hold_start:])
    rows = []

    for preset, cut_scale, gross_multiplier in itertools.product(
        presets, (0.25, 0.50, 0.75), (1.00, 1.03, 1.06)
    ):
        p = {
            **preset,
            "cut_scale": cut_scale,
            "gross_multiplier": gross_multiplier,
            "gross_cap": 1.90,
        }
        result, _, _, _, diag = build_candidate(data, raw, ex, guard, gross, base_cost, p)
        s = r36.stats(result.equity)
        hold = r36.stats(result.equity.loc[hold_start:])
        wealth_r30 = (1.0 + s["return"]) / max(1e-12, 1.0 + r30_stats["return"])
        hold_r30 = (1.0 + hold["return"]) / max(1e-12, 1.0 + r30_hold["return"])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        score = (
            8.0 * np.log(max(return_env, 1e-12))
            + 4.0 * np.log(max(hold_r30, 1e-12))
            + 12.0 * max(0.0, 1.0 - dd_env)
            - 16.0 * max(0.0, dd_env - 1.0)
            + 10.0 * max(0.0, 1.0 - worst_env)
            - 14.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "wealth_ratio_to_r30": float(wealth_r30),
            "holdout_wealth_ratio_to_r30": float(hold_r30),
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "gate_diagnostics": diag,
            "score": float(score),
        })
        gc.collect()

    rows.sort(key=lambda x: x["score"], reverse=True)
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    earliest = max(item["data"].close.index[0] for item in benchmarks.values())
    finalists = []

    for row in rows[:9]:
        p = row["params"]
        isolated, isolated_r30, isolated_bench, envelopes, wins, material = {}, {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c, rb = isolated_candidate(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            isolated[k], isolated_r30[k], isolated_bench[k], envelopes[k] = c, rb, bench, env
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
            c, rb = isolated_candidate(data, raw, ex, guard, gross, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alternative[str(days)] = {
                "candidate": c,
                "r30": rb,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        sev_result, _, _, _, sev_diag = build_candidate(data, raw, ex, guard, gross, severe_cost, p)
        sev = r36.stats(sev_result.equity)
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_risk_pass = (
            abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
            and abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        )
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_risk_pass = (
            abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
            and abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        )
        all_wins = all(all(v.values()) for v in wins.values())
        all_material = all(all(v.values()) for v in material.values())
        alt_all = bool(alternative) and all(
            x["return_win"] and x["drawdown_win"] and x["worst_day_win"]
            for x in alternative.values()
        )
        dominant = bool(
            all_material
            and alt_all
            and full_return_pass
            and full_risk_pass
            and row["holdout_wealth_ratio_to_r30"] >= 1.03
            and severe_return_pass
            and severe_risk_pass
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_r30": isolated_r30,
            "isolated_benchmarks": isolated_bench,
            "isolated_envelope": envelopes,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alternative,
            "all_envelope_dimensions_won": all_wins,
            "all_material_envelope_dimensions_won": all_material,
            "all_alternative_envelopes_won": alt_all,
            "severe_cost": sev,
            "severe_gate_diagnostics": sev_diag,
            "full_return_pass": full_return_pass,
            "full_risk_pass": full_risk_pass,
            "severe_return_pass": severe_return_pass,
            "severe_risk_pass": severe_risk_pass,
            "dominant_gate_passed": dominant,
        })
        gc.collect()

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["all_material_envelope_dimensions_won"],
            z["all_envelope_dimensions_won"],
            sum(sum(v.values()) for v in z["material_envelope_wins"].values()),
            sum(sum(v.values()) for v in z["envelope_wins"].values()),
            z["all_alternative_envelopes_won"],
            z["full_return_pass"], z["full_risk_pass"],
            z["holdout_wealth_ratio_to_r30"],
            -z["drawdown_ratio_to_full_envelope"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R38 dominant-position fast adverse gate",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "start from the strongest defensive R30 direct-hedge frontier, identify only the current top-gross position, cut it when 3h/6h movement turns materially against its requested side, never redistribute the removed risk, and test only a small gross recovery multiplier",
        "r30_fixed_base": r37.R30_BASE,
        "r30_base_summary": r30_stats,
        "r30_base_severe": r30_severe_stats,
        "r30_hedge_active_fraction": float(r30_hedge_active.mean()),
        "grid_policy": "27 predeclared combinations = 3 fast-gate severities x 3 cut scales x 3 gross multipliers; validation horizons are not optimizer inputs",
        "grid_size": len(rows),
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "all_screened": rows,
        "disclosure": "Historical research only. Position share and 3h/6h signed returns are known at close t and alter only the next requested target. Removed risk is not redistributed. The base R30 hedge is independently causal. No real-order path is enabled. Any historical winner requires freezing and forward paper before promotion.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "r30": r30_stats, "full_envelope": full_env, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    main()
