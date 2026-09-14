from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase2_bear_native_alpha as p2
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase5_position_reallocator.json"


def bear_hv_position_reallocator(
    targets: pd.DataFrame,
    close: pd.DataFrame,
    direction: pd.Series,
    vol: pd.Series,
) -> tuple[pd.DataFrame, dict]:
    """Reallocate existing gross from misaligned positions to aligned positions.

    This is not a new directional alpha and does not increase portfolio gross.
    It only operates in prior-known BEAR+HIGH_VOL. A position's causal alignment
    is sign(target) * prior 12h return, normalized by prior realized volatility.
    Misaligned positions use the already-researched continuous R106 attenuation
    curve; released gross is recycled only to already-open aligned positions.
    Outside BEAR+HIGH_VOL, targets are bit-for-bit unchanged.
    """
    out = targets.copy().astype(float)
    idx = out.index
    d = direction.shift(1).reindex(idx).fillna("UNKNOWN")
    v = vol.shift(1).reindex(idx).fillna("UNKNOWN")
    active = d.eq("BEAR") & v.eq("HIGH_VOLATILITY")

    r12 = close.pct_change(12, fill_method=None).shift(1).reindex(idx)
    sigma = (
        close.pct_change(fill_method=None)
        .rolling(72, min_periods=36)
        .std()
        .mul(np.sqrt(12.0))
        .shift(1)
        .reindex(idx)
    )
    signed_alignment = np.sign(out).mul(r12).div(sigma.replace(0.0, np.nan))

    original = out.loc[active].copy()
    if len(original):
        align = signed_alignment.loc[active].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        loser_scale = np.exp(align.clip(lower=-1.05, upper=0.0)).clip(lower=0.35, upper=1.0)
        reduced = original.where(align.ge(0.0), original.mul(loser_scale))

        original_gross = original.abs().sum(axis=1)
        reduced_gross = reduced.abs().sum(axis=1)
        freed = (original_gross - reduced_gross).clip(lower=0.0)

        aligned_strength = align.clip(lower=0.0).mul(original.abs())
        denom = aligned_strength.sum(axis=1).replace(0.0, np.nan)
        weights = aligned_strength.div(denom, axis=0).fillna(0.0)
        recycled_abs = weights.mul(freed, axis=0)
        recycled = np.sign(original).mul(recycled_abs)
        controlled = reduced.add(recycled, fill_value=0.0)

        # Numerical guard: recycling may never exceed original row gross.
        cg = controlled.abs().sum(axis=1)
        row_scale = original_gross.div(cg.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
        controlled = controlled.mul(row_scale, axis=0)
        out.loc[active, :] = controlled

        avg_freed = float(freed.mean())
        recycled_fraction = float((recycled.abs().sum(axis=1) / freed.replace(0.0, np.nan)).fillna(0.0).mean())
        reduced_position_fraction = float((align.lt(0.0) & original.ne(0.0)).to_numpy().mean())
    else:
        avg_freed = 0.0
        recycled_fraction = 0.0
        reduced_position_fraction = 0.0

    out = p1.cap(out, p1.GROSS_CAP)
    return out, {
        "architecture": "position_level_alignment_reallocation",
        "active_regime": "BEAR__HIGH_VOLATILITY",
        "alignment_window_hours": 12,
        "vol_normalization_hours": 72,
        "misaligned_floor": 0.35,
        "attenuation": "exp(clipped negative signed alignment)",
        "gross_increase_allowed": False,
        "recycle_only_to_existing_aligned_positions": True,
        "outside_regime_unchanged": True,
        "future_data": False,
        "active_fraction": float(active.mean()),
        "avg_freed_gross": avg_freed,
        "recycled_fraction_of_freed_gross": recycled_fraction,
        "reduced_position_fraction": reduced_position_fraction,
    }


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
    }


def passes(c: dict) -> dict:
    return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}


def build_phase3_native(data, ex, guard, base_cost, direction, vol):
    base = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeve_targets = {**base, "bear_dispersion": dispersion, "breakout": breakout}
    sleeve_results = {
        name: p1.run_targets(data, targets, ex, guard, base_cost, p1.NATIVE_GROSS_CAP)
        for name, targets in sleeve_targets.items()
    }
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, stability = p2.stability_router(
        sleeve_results, data, direction, vol, train_start, train_end
    )
    native_targets = p1.route_native(sleeve_targets, direction, vol, routing)
    return native_targets, routing, stability


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    native_targets, routing, stability = build_phase3_native(
        data, ex, guard, base_cost, direction, vol
    )

    f3_targets = p1.cap(
        r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f3_result = p1.run_targets(data, f3_targets, ex, guard, base_cost, p1.GROSS_CAP)

    controlled_core_targets, control_diag = bear_hv_position_reallocator(
        r98_targets, data.close, direction, vol
    )
    controlled_core_result = p1.run_targets(
        data, controlled_core_targets, ex, guard, base_cost, p1.GROSS_CAP
    )
    hybrid_targets = p1.cap(
        controlled_core_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    hybrid_result = p1.run_targets(data, hybrid_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    env = audit.metric_envelope({n: a["global"] for n, a in bench.items()})

    result_map = {
        "r98": r98_result,
        "f3_hybrid": f3_result,
        "controlled_core": controlled_core_result,
        "phase5_hybrid": hybrid_result,
    }
    full = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in result_map.items()
    }
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        name: audit.analyze_result(result, data, direction, vol, hold_start, common_end)
        for name, result in result_map.items()
    }
    hold_cmp = {n: audit.candidate_vs_envelope(a["global"], hold_env) for n, a in hold.items()}

    r98_sev_targets, r98_sev_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    controlled_sev_targets, _ = bear_hv_position_reallocator(
        r98_sev_targets, data.close, direction, vol
    )
    f3_sev_targets = p1.cap(
        r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f3_sev_result = p1.run_targets(data, f3_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    controlled_sev_result = p1.run_targets(
        data, controlled_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP
    )
    hybrid_sev_targets = p1.cap(
        controlled_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    hybrid_sev_result = p1.run_targets(data, hybrid_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)

    severe_bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(severe_bench_results.items(), benchmarks.values())
    }
    severe_env = audit.metric_envelope({n: a["global"] for n, a in severe_bench.items()})
    severe_map = {
        "r98": r98_sev_result,
        "f3_hybrid": f3_sev_result,
        "controlled_core": controlled_sev_result,
        "phase5_hybrid": hybrid_sev_result,
    }
    severe = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in severe_map.items()
    }
    severe_cmp = {n: audit.candidate_vs_envelope(a["global"], severe_env) for n, a in severe.items()}

    out = {
        "study": "V99 R106 phase 5 — position-level BEAR+HIGH_VOL capital reallocator",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "same_phase3_native_router": True,
            "same_hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE,
            "gross_increase": False,
            "controller": control_diag,
        },
        "routing": routing,
        "stability_diagnostics": stability,
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "metadata": metadata,
        },
        "base": {"benchmark_envelope": env, **full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": {"benchmark_envelope": hold_env, **hold, "vs_envelope": hold_cmp, "pass_counts": {n: passes(c) for n, c in hold_cmp.items()}},
        "severe": {"benchmark_envelope": severe_env, **severe, "vs_envelope": severe_cmp, "pass_counts": {n: passes(c) for n, c in severe_cmp.items()}},
        "horizons": {
            name: p1.horizon_stats(result.equity, common_end)
            for name, result in result_map.items()
        },
        "promotion": {"r106_promoted": False, "reason": "phase 5 research gate pending evidence review"},
        "disclosure": "Historical research/holdout only. No real orders. Results are not profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "pass_counts": {
            "base": {n: passes(c) for n, c in cmp.items()},
            "holdout": {n: passes(c) for n, c in hold_cmp.items()},
            "severe": {n: passes(c) for n, c in severe_cmp.items()},
        },
        "controller": control_diag,
        "routing": routing,
        "bear_high_vol": {
            n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
            for n, a in full.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
