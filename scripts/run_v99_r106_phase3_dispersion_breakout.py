from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.signals import StrategySpec, build_targets
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase2_bear_native_alpha as p2
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase3_dispersion_breakout.json"

DISPERSION_SPEC = StrategySpec(
    family="xmom",
    lookback=168,
    rebalance=12,
    top_n=3,
    vol_lookback=168,
    vol_target=0.45,
    leverage_cap=1.0,
    trend_lookback=336,
    long_short_balance=0.50,
    threshold=0.0,
)

BREAKOUT_SPEC = StrategySpec(
    family="breakout",
    lookback=72,
    rebalance=6,
    vol_lookback=168,
    vol_target=0.55,
    leverage_cap=1.10,
    exit_lookback=24,
)


def dollar_neutral(targets: pd.DataFrame, gross: float = 1.0) -> pd.DataFrame:
    pos = targets.clip(lower=0.0)
    neg = -targets.clip(upper=0.0)
    pg = pos.sum(axis=1).replace(0.0, np.nan)
    ng = neg.sum(axis=1).replace(0.0, np.nan)
    long = pos.div(pg, axis=0).fillna(0.0) * (gross / 2.0)
    short = neg.div(ng, axis=0).fillna(0.0) * (gross / 2.0)
    both = pg.notna() & ng.notna()
    out = long - short
    return out.where(both, 0.0)


def bear_dispersion_targets(data, direction: pd.Series) -> tuple[pd.DataFrame, dict]:
    raw = build_targets(data, DISPERSION_SPEC)
    spread = dollar_neutral(raw, gross=1.0)
    bear = direction.shift(1).reindex(spread.index).eq("BEAR")
    spread = spread.where(bear, 0.0)
    return spread, {
        "architecture": "bear_only_dollar_neutral_cross_sectional_momentum",
        "spec": DISPERSION_SPEC.to_dict(),
        "net_beta_intent": "approximately market neutral; alpha from relative strength dispersion",
        "active_fraction": float(spread.abs().sum(axis=1).gt(1e-9).mean()),
        "future_data": False,
    }


def breakout_targets(data) -> tuple[pd.DataFrame, dict]:
    targets = build_targets(data, BREAKOUT_SPEC)
    return p1.cap(targets, 1.10), {
        "architecture": "symmetric_channel_breakout",
        "spec": BREAKOUT_SPEC.to_dict(),
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


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)

    # Keep the economically distinct phase-1 families; drop the failed outright
    # bear short from phase 2 and add dispersion + breakout instead.
    sleeve_targets = p1.fixed_sleeves(data)
    dispersion, dispersion_diag = bear_dispersion_targets(data, direction)
    breakout, breakout_diag = breakout_targets(data)
    sleeve_targets = {
        **sleeve_targets,
        "bear_dispersion": dispersion,
        "breakout": breakout,
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

    # Preserve R98 exactly; no global controller is applied to the core.
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

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, common_start, common_end),
        "bear_dispersion": audit.analyze_result(sleeve_results["bear_dispersion"], data, direction, vol, common_start, common_end),
        "breakout": audit.analyze_result(sleeve_results["breakout"], data, direction, vol, common_start, common_end),
    }
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items() if n in ("r98", "native", "hybrid")}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, hold_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, hold_start, common_end),
        "bear_dispersion": audit.analyze_result(sleeve_results["bear_dispersion"], data, direction, vol, hold_start, common_end),
        "breakout": audit.analyze_result(sleeve_results["breakout"], data, direction, vol, hold_start, common_end),
    }
    hold_cmp = {n: audit.candidate_vs_envelope(a["global"], hold_env) for n, a in hold.items() if n in ("r98", "native", "hybrid")}

    # Severe-cost validation with routing frozen from base-cost training.
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
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_sev, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_sev, data, direction, vol, common_start, common_end),
        "bear_dispersion": audit.analyze_result(sleeve_sev["bear_dispersion"], data, direction, vol, common_start, common_end),
        "breakout": audit.analyze_result(sleeve_sev["breakout"], data, direction, vol, common_start, common_end),
    }
    severe_cmp = {n: audit.candidate_vs_envelope(a["global"], severe_env) for n, a in severe.items() if n in ("r98", "native", "hybrid")}

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 3 — bear dispersion + channel breakout",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "same_hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE,
            "same_chronological_stability_router": True,
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
        "promotion": {"r106_promoted": False, "reason": "phase 3 research gate pending evidence review"},
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
        "bear_candidates_train": {
            state: [x for x in rows if x["sleeve"] in ("bear_dispersion", "breakout")]
            for state, rows in stability.items() if state.startswith("BEAR__")
        },
        "bear_high_vol": {
            n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
            for n, a in full.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
