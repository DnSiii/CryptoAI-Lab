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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase5_segregated_sleeve_risk.json"


def guard_execution_factors(equity: pd.Series, guard: dict) -> pd.Series:
    """Reconstruct the causal DD-guard factor applied at each hourly open."""
    idx = equity.index
    values = equity.astype(float).ffill().fillna(1.0).to_numpy()
    factors = np.ones(len(idx), dtype=float)
    threshold = float(guard["drawdown_threshold"])
    multiplier = float(guard["exposure_multiplier"])
    cooldown = guard.get("cooldown_hours")
    cooldown = int(cooldown) if cooldown is not None else None
    recovery = threshold / 2.0

    peak = 1.0
    active = False
    until = -1
    for i in range(1, len(idx)):
        current = float(values[i - 1])
        if cooldown is not None and active and i >= until:
            active = False
            peak = current
        prior_dd = current / max(peak, 1e-12) - 1.0
        if cooldown is None and active and prior_dd >= -abs(recovery):
            active = False
        elif (not active) and prior_dd <= -abs(threshold):
            active = True
            if cooldown is not None:
                until = i + cooldown
        factors[i] = multiplier if active else 1.0
        peak = max(peak, float(values[i]))
    return pd.Series(factors, index=idx, dtype=float)


def effective_targets(targets: pd.DataFrame, result, guard: dict) -> tuple[pd.DataFrame, pd.Series]:
    exec_factor = guard_execution_factors(result.equity, guard)
    # Target at close t executes at open t+1, where exec_factor[t+1] applies.
    target_factor = pd.Series(1.0, index=targets.index, dtype=float)
    if len(target_factor) > 1:
        target_factor.iloc[:-1] = exec_factor.iloc[1:].to_numpy()
    return targets.mul(target_factor, axis=0), target_factor


def combine_with_headroom(core: pd.DataFrame, native: pd.DataFrame, alpha_scale: float, gross_cap: float):
    desired = native * float(alpha_scale)
    core_gross = core.abs().sum(axis=1)
    desired_gross = desired.abs().sum(axis=1)
    headroom = (float(gross_cap) - core_gross).clip(lower=0.0)
    use = (headroom / desired_gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    overlay = desired.mul(use, axis=0)
    combined = core.add(overlay, fill_value=0.0)
    # Conservative construction: gross-sum headroom is used, so this cap should
    # only catch floating-point edge cases, never shrink the core deliberately.
    combined = p1.cap(combined, gross_cap)
    diag = {
        "mean_core_gross": float(core_gross.mean()),
        "mean_headroom": float(headroom.mean()),
        "native_desired_active_fraction": float(desired_gross.gt(1e-12).mean()),
        "native_fully_used_fraction": float((use.ge(0.999999) & desired_gross.gt(1e-12)).mean()),
        "native_partially_used_fraction": float(((use > 1e-12) & (use < 0.999999)).mean()),
        "native_blocked_fraction": float((use.le(1e-12) & desired_gross.gt(1e-12)).mean()),
        "mean_native_use_when_active": float(use[desired_gross.gt(1e-12)].mean()) if desired_gross.gt(1e-12).any() else 0.0,
        "max_combined_requested_gross": float(combined.abs().sum(axis=1).max()),
    }
    return combined, overlay, diag


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


def build_phase3_native(data, ex, guard, base_cost, direction, vol):
    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    results = {name: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for name, t in sleeves.items()}
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, stability = p2.stability_router(results, data, direction, vol, train_start, train_end)
    native_targets = p1.route_native(sleeves, direction, vol, routing)
    return native_targets, routing, stability


def run_no_dd_guard(data, targets, ex, cost, gross_cap):
    return p1.r98.r36.run(data, targets, ex, cost, gross_cap, guard=None)


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    native_targets, routing, stability = build_phase3_native(data, ex, guard, base_cost, direction, vol)
    native_result = p1.run_targets(data, native_targets, ex, guard, base_cost, p1.GROSS_CAP)

    core_effective, core_factor = effective_targets(r98_targets, r98_result, guard)
    native_effective, native_factor = effective_targets(native_targets, native_result, guard)

    # Core-only reconstruction must reproduce the original R98 path before the
    # segregated architecture is considered valid.
    core_replay = run_no_dd_guard(data, core_effective, ex, base_cost, p1.GROSS_CAP)
    common_idx = r98_result.equity.index.intersection(core_replay.equity.index)
    rel_err = (core_replay.equity.reindex(common_idx) / r98_result.equity.reindex(common_idx) - 1.0).abs()
    reconstruction = {
        "terminal_relative_error": float(rel_err.iloc[-1]),
        "max_path_relative_error": float(rel_err.max()),
        "valid": bool(float(rel_err.max()) <= 5e-6),
    }

    combined_targets, overlay_targets, headroom_diag = combine_with_headroom(
        core_effective, native_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    segregated_result = run_no_dd_guard(data, combined_targets, ex, base_cost, p1.GROSS_CAP)

    # Original F3 combined-target architecture for direct comparison.
    phase3_targets = p1.cap(r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    phase3_result = p1.run_targets(data, phase3_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for name, item in benchmarks.items()}
    bench_analyses = {name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end) for (name, result), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench_analyses.items()})

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "phase3_hybrid": audit.analyze_result(phase3_result, data, direction, vol, common_start, common_end),
        "segregated": audit.analyze_result(segregated_result, data, direction, vol, common_start, common_end),
    }
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold = {n: audit.analyze_result(r, data, direction, vol, hold_start, common_end) for n, r in {
        "r98": r98_result, "phase3_hybrid": phase3_result, "segregated": segregated_result
    }.items()}

    # Severe-cost replay with independent sleeve breaker states reconstructed at
    # severe cost; routing remains frozen from the base-cost training period.
    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    native_sev = p1.run_targets(data, native_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    core_sev_effective, _ = effective_targets(r98_sev_targets, r98_sev, guard)
    native_sev_effective, _ = effective_targets(native_targets, native_sev, guard)
    combined_sev_targets, _, severe_headroom_diag = combine_with_headroom(
        core_sev_effective, native_sev_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    segregated_sev = run_no_dd_guard(data, combined_sev_targets, ex, severe_cost, p1.GROSS_CAP)
    phase3_sev_targets = p1.cap(r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    phase3_sev = p1.run_targets(data, phase3_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {n: audit.analyze_result(r, data, direction, vol, common_start, common_end) for n, r in {
        "r98": r98_sev, "phase3_hybrid": phase3_sev, "segregated": segregated_sev
    }.items()}

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 5 — segregated sleeve risk + headroom overlay",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "architecture": {
            "r98_core_drawdown_guard_isolated": True,
            "native_drawdown_guard_isolated": True,
            "global_normal_drawdown_guard_disabled_after_preapplication": True,
            "mechanical_gross_guard_retained": True,
            "native_uses_only_remaining_headroom": True,
            "core_never_scaled_down_to_fund_native": True,
            "routing_frozen_from_phase3_train": True,
            "alpha_scale": p1.HYBRID_ALPHA_SCALE,
        },
        "core_reconstruction": reconstruction,
        "headroom": headroom_diag,
        "severe_headroom": severe_headroom_diag,
        "routing": routing,
        "routing_stability": stability,
        "base": {**full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": hold,
        "severe": severe,
        "diagnostics": {
            "core_guard_active_target_fraction": float(core_factor.lt(0.999999).mean()),
            "native_guard_active_target_fraction": float(native_factor.lt(0.999999).mean()),
            "overlay_active_fraction": float(overlay_targets.abs().sum(axis=1).gt(1e-12).mean()),
        },
        "data": {
            "common_start": common_start.isoformat(), "common_end": common_end.isoformat(),
            "train_end": min(p1.TRAIN_END, common_end).isoformat(), "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined, "metadata": metadata,
        },
        "disclosure": "Historical research/holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "core_reconstruction": reconstruction,
        "headroom": headroom_diag,
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "pass_counts": {n: passes(c) for n, c in cmp.items()},
    }, indent=2, default=audit.safe_float))


if __name__ == "__main__":
    main()
