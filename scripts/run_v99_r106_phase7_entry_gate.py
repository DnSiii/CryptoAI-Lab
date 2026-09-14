from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase2_bear_native_alpha as p2
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase7_entry_gate.json"


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


def wrong_way_entry_gate(
    targets: pd.DataFrame,
    direction: pd.Series,
    vol: pd.Series,
) -> tuple[pd.DataFrame, dict]:
    """Block only NEW wrong-way entries in directional high-vol regimes.

    Existing positions are never resized merely because the regime changed.
    In BEAR+HIGH_VOL a desired long can continue only if the gated book was
    already long in that asset on the previous hour. New shorts are untouched.
    BULL+HIGH_VOL is symmetric for new shorts. Outside these regimes the
    desired target is copied exactly.

    This is stateful by design: an entry blocked at t does not sneak in at t+1
    simply because the ungated desired target remained nonzero.
    """
    desired = targets.astype(float)
    out = desired.copy()
    d = direction.shift(1).reindex(desired.index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(desired.index).fillna("UNKNOWN")
    bear_hv = d.eq("BEAR") & v.eq("HIGH_VOLATILITY")
    bull_hv = d.eq("BULL") & v.eq("HIGH_VOLATILITY")

    blocked_long_entries = 0
    blocked_short_entries = 0
    preserved_long_hours = 0
    preserved_short_hours = 0

    prev = pd.Series(0.0, index=desired.columns)
    for ts in desired.index:
        row = desired.loc[ts].copy()
        if bool(bear_hv.loc[ts]):
            new_long = row.gt(0.0) & prev.le(0.0)
            existing_long = row.gt(0.0) & prev.gt(0.0)
            blocked_long_entries += int(new_long.sum())
            preserved_long_hours += int(existing_long.sum())
            row.loc[new_long] = 0.0
        elif bool(bull_hv.loc[ts]):
            new_short = row.lt(0.0) & prev.ge(0.0)
            existing_short = row.lt(0.0) & prev.lt(0.0)
            blocked_short_entries += int(new_short.sum())
            preserved_short_hours += int(existing_short.sum())
            row.loc[new_short] = 0.0
        out.loc[ts] = row
        prev = row

    out = p1.cap(out, p1.GROSS_CAP)
    return out, {
        "architecture": "stateful_wrong_way_entry_gate",
        "bear_rule": "BEAR+HIGH_VOL blocks new longs only; existing longs and all shorts remain untouched",
        "bull_rule": "BULL+HIGH_VOL blocks new shorts only; existing shorts and all longs remain untouched",
        "uses_prior_regime_only": True,
        "resizes_existing_positions": False,
        "gross_increase_allowed": False,
        "parameter_fitted": False,
        "blocked_long_entries": int(blocked_long_entries),
        "blocked_short_entries": int(blocked_short_entries),
        "preserved_existing_long_asset_hours": int(preserved_long_hours),
        "preserved_existing_short_asset_hours": int(preserved_short_hours),
        "bear_high_vol_fraction": float(bear_hv.mean()),
        "bull_high_vol_fraction": float(bull_hv.mean()),
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


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    native_targets, routing, stability = build_phase3_native(data, ex, guard, base_cost, direction, vol)
    f3_targets = p1.cap(r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    f3_result = p1.run_targets(data, f3_targets, ex, guard, base_cost, p1.GROSS_CAP)

    r98_gated_targets, r98_gate_diag = wrong_way_entry_gate(r98_targets, direction, vol)
    f3_gated_targets, gate_diag = wrong_way_entry_gate(f3_targets, direction, vol)
    r98_gated_result = p1.run_targets(data, r98_gated_targets, ex, guard, base_cost, p1.GROSS_CAP)
    phase7_result = p1.run_targets(data, f3_gated_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for name, item in benchmarks.items()}
    bench = {name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end) for (name, result), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench.items()})

    result_map = {"r98": r98_result, "f3_hybrid": f3_result, "r98_entry_gated": r98_gated_result, "phase7_hybrid": phase7_result}
    full = {name: audit.analyze_result(result, data, direction, vol, common_start, common_end) for name, result in result_map.items()}
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end) for (name, result), item in zip(bench_results.items(), benchmarks.values())}
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {name: audit.analyze_result(result, data, direction, vol, hold_start, common_end) for name, result in result_map.items()}
    hold_cmp = {n: audit.candidate_vs_envelope(a["global"], hold_env) for n, a in hold.items()}

    r98_sev_targets, r98_sev_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    f3_sev_targets = p1.cap(r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    f3_sev_result = p1.run_targets(data, f3_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    r98_gated_sev_targets, _ = wrong_way_entry_gate(r98_sev_targets, direction, vol)
    f3_gated_sev_targets, _ = wrong_way_entry_gate(f3_sev_targets, direction, vol)
    r98_gated_sev_result = p1.run_targets(data, r98_gated_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    phase7_sev_result = p1.run_targets(data, f3_gated_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe_bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["severe_cost_per_side"])) for name, item in benchmarks.items()}
    severe_bench = {name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end) for (name, result), item in zip(severe_bench_results.items(), benchmarks.values())}
    severe_env = audit.metric_envelope({n: a["global"] for n, a in severe_bench.items()})
    severe_map = {"r98": r98_sev_result, "f3_hybrid": f3_sev_result, "r98_entry_gated": r98_gated_sev_result, "phase7_hybrid": phase7_sev_result}
    severe = {name: audit.analyze_result(result, data, direction, vol, common_start, common_end) for name, result in severe_map.items()}
    severe_cmp = {n: audit.candidate_vs_envelope(a["global"], severe_env) for n, a in severe.items()}

    out = {
        "study": "V99 R106 phase 7 — stateful wrong-way entry gate",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {"no_grid_search": True, "same_phase3_native_router": True, "same_hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE, "gate": gate_diag, "r98_gate": r98_gate_diag},
        "routing": routing,
        "stability_diagnostics": stability,
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "base": {"benchmark_envelope": env, **full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": {"benchmark_envelope": hold_env, **hold, "vs_envelope": hold_cmp, "pass_counts": {n: passes(c) for n, c in hold_cmp.items()}},
        "severe": {"benchmark_envelope": severe_env, **severe, "vs_envelope": severe_cmp, "pass_counts": {n: passes(c) for n, c in severe_cmp.items()}},
        "horizons": {name: p1.horizon_stats(result.equity, common_end) for name, result in result_map.items()},
        "promotion": {"r106_promoted": False, "reason": "phase 7 research gate pending evidence review"},
        "disclosure": "Historical research/holdout only. No real orders. Results are not profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "pass_counts": {"base": {n: passes(c) for n, c in cmp.items()}, "holdout": {n: passes(c) for n, c in hold_cmp.items()}, "severe": {n: passes(c) for n, c in severe_cmp.items()}},
        "gate": gate_diag,
        "bear_high_vol": {n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"] for n, a in full.items()},
        "bull_high_vol": {n: a["regimes"]["matrix"]["BULL__HIGH_VOLATILITY"] for n, a in full.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
