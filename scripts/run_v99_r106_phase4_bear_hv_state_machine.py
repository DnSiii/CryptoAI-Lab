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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase4_bear_hv_state_machine.json"


def bear_hv_state_masks(data, direction: pd.Series, vol: pd.Series) -> tuple[dict[str, pd.Series], dict]:
    close = data.close.astype(float)
    idx = close.index
    d = direction.shift(1).reindex(idx).fillna("UNKNOWN")
    v = vol.shift(1).reindex(idx).fillna("UNKNOWN")
    bear_hv = d.eq("BEAR") & v.eq("HIGH_VOLATILITY")

    r12 = close.pct_change(12, fill_method=None)
    btc12 = r12["BTCUSDT"].shift(1)
    positive_breadth = r12.gt(0.0).mean(axis=1).shift(1)

    crash = bear_hv & btc12.lt(0.0) & positive_breadth.lt(0.50)
    squeeze = bear_hv & btc12.gt(0.0) & positive_breadth.gt(0.50)
    transition = bear_hv & ~(crash | squeeze)

    masks = {"crash_continuation": crash, "bear_squeeze": squeeze, "transition": transition}
    diag = {
        "architecture": "causal_bear_high_vol_state_machine",
        "decision_window_hours": 12,
        "breadth_boundary": 0.50,
        "threshold_fitted": False,
        "uses_prior_completed_data": True,
        "crash_fraction": float(crash.mean()),
        "squeeze_fraction": float(squeeze.mean()),
        "transition_fraction": float(transition.mean()),
        "bear_hv_fraction": float(bear_hv.mean()),
    }
    return masks, diag


def aligned_bear_hv_sleeves(
    base: dict[str, pd.DataFrame],
    breakout: pd.DataFrame,
    masks: dict[str, pd.Series],
) -> tuple[dict[str, pd.DataFrame], dict]:
    # Fixed equal-weight architecture. No parameter search.
    trend = base["trend"]
    impulse = base["impulse"]

    crash_raw = 0.50 * trend.clip(upper=0.0) + 0.50 * breakout.clip(upper=0.0)
    squeeze_raw = 0.50 * trend.clip(lower=0.0) + 0.50 * impulse.clip(lower=0.0)

    crash = p1.cap(crash_raw.where(masks["crash_continuation"], 0.0), 1.10)
    squeeze = p1.cap(squeeze_raw.where(masks["bear_squeeze"], 0.0), 1.10)
    return {
        "bear_hv_crash": crash,
        "bear_hv_squeeze": squeeze,
    }, {
        "crash": "50% negative-only trend + 50% negative-only channel breakout",
        "squeeze": "50% positive-only trend + 50% positive-only impulse",
        "gross_cap": 1.10,
        "aligned_side_only": True,
        "global_cut": False,
        "future_data": False,
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

    base = p1.fixed_sleeves(data)
    dispersion, dispersion_diag = p3.bear_dispersion_targets(data, direction)
    breakout, breakout_diag = p3.breakout_targets(data)
    masks, state_diag = bear_hv_state_masks(data, direction, vol)
    hv_sleeves, hv_diag = aligned_bear_hv_sleeves(base, breakout, masks)

    sleeve_targets = {
        **base,
        "bear_dispersion": dispersion,
        "breakout": breakout,
        **hv_sleeves,
    }
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
    native_result = p1.run_targets(data, native_targets, ex, guard, base_cost, p1.GROSS_CAP)

    hybrid_targets = p1.cap(
        r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
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

    keys = ("r98", "native", "hybrid", "bear_hv_crash", "bear_hv_squeeze")
    result_map = {
        "r98": r98_result,
        "native": native_result,
        "hybrid": hybrid_result,
        "bear_hv_crash": sleeve_results["bear_hv_crash"],
        "bear_hv_squeeze": sleeve_results["bear_hv_squeeze"],
    }
    full = {
        name: audit.analyze_result(result_map[name], data, direction, vol, common_start, common_end)
        for name in keys
    }
    cmp = {n: audit.candidate_vs_envelope(full[n]["global"], env) for n in ("r98", "native", "hybrid")}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        name: audit.analyze_result(result_map[name], data, direction, vol, hold_start, common_end)
        for name in keys
    }
    hold_cmp = {n: audit.candidate_vs_envelope(hold[n]["global"], hold_env) for n in ("r98", "native", "hybrid")}

    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    sleeve_sev = {
        name: p1.run_targets(data, targets, ex, guard, severe_cost, p1.NATIVE_GROSS_CAP)
        for name, targets in sleeve_targets.items()
    }
    native_sev = p1.run_targets(data, native_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    hybrid_sev_targets = p1.cap(
        r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    hybrid_sev = p1.run_targets(data, hybrid_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe_bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(severe_bench_results.items(), benchmarks.values())
    }
    severe_env = audit.metric_envelope({n: a["global"] for n, a in severe_bench.items()})
    severe_results = {
        "r98": r98_sev,
        "native": native_sev,
        "hybrid": hybrid_sev,
        "bear_hv_crash": sleeve_sev["bear_hv_crash"],
        "bear_hv_squeeze": sleeve_sev["bear_hv_squeeze"],
    }
    severe = {
        name: audit.analyze_result(severe_results[name], data, direction, vol, common_start, common_end)
        for name in keys
    }
    severe_cmp = {n: audit.candidate_vs_envelope(severe[n]["global"], severe_env) for n in ("r98", "native", "hybrid")}

    out = {
        "study": "V99 R106 phase 4 — BEAR+HIGH_VOL crash continuation vs squeeze state machine",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "same_hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE,
            "same_chronological_stability_router": True,
            "state_machine": state_diag,
            "state_sleeves": hv_diag,
            "dispersion": dispersion_diag,
            "breakout": breakout_diag,
        },
        "routing": routing,
        "stability_diagnostics": stability,
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "metadata": metadata,
        },
        "base": {"benchmark_envelope": env, **full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": {"benchmark_envelope": hold_env, **hold, "vs_envelope": hold_cmp, "pass_counts": {n: passes(c) for n, c in hold_cmp.items()}},
        "severe": {"benchmark_envelope": severe_env, **severe, "vs_envelope": severe_cmp, "pass_counts": {n: passes(c) for n, c in severe_cmp.items()}},
        "horizons": {
            "r98": p1.horizon_stats(r98_result.equity, common_end),
            "native": p1.horizon_stats(native_result.equity, common_end),
            "hybrid": p1.horizon_stats(hybrid_result.equity, common_end),
        },
        "promotion": {"r106_promoted": False, "reason": "phase 4 research gate pending evidence review"},
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
        "routing": routing,
        "state_machine": state_diag,
        "bear_hv_candidates_train": {
            state: [x for x in rows if x["sleeve"] in ("bear_hv_crash", "bear_hv_squeeze", "bear_dispersion", "breakout")]
            for state, rows in stability.items() if state == "BEAR__HIGH_VOLATILITY"
        },
        "bear_high_vol": {
            n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
            for n, a in full.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
