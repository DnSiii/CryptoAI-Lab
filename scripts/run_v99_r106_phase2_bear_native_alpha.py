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
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase2_bear_native_alpha.json"
TRAIN_FOLDS = 4
TOP_SLEEVES_PER_STATE = 2
MIN_FOLD_ACTIVE_HOURS = 24 * 7
MIN_STABLE_FRACTION = 0.60
BEAR_SHORT_GROSS = 1.10


def bear_native_short_targets(
    data,
    direction: pd.Series,
    vol_state: pd.Series,
) -> tuple[pd.DataFrame, dict]:
    """Causal short-only alpha for bear regimes, not a hedge.

    The sleeve ranks persistent downside relative strength and requires each
    selected contract to be below a slow trend anchor. HIGH_VOL uses a faster
    blend; LOW_VOL uses a slower blend. Selection is cross-sectional so the
    sleeve seeks the weakest contracts rather than shorting the whole market.
    """
    close = data.close.astype(float)
    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    r168 = close.pct_change(168, fill_method=None)
    ema336 = close.ewm(span=336, adjust=False, min_periods=336).mean()
    below = close < ema336

    def pct_rank(frame: pd.DataFrame) -> pd.DataFrame:
        return frame.rank(axis=1, pct=True, ascending=True, method="average")

    fast_score = 0.60 * pct_rank(r24) + 0.40 * pct_rank(r72)
    slow_score = 0.45 * pct_rank(r72) + 0.55 * pct_rank(r168)
    hv = vol_state.shift(1).reindex(close.index).eq("HIGH_VOLATILITY")
    score = slow_score.copy()
    score.loc[hv] = fast_score.loc[hv]

    available = close.notna() & close.shift(336).notna() & below
    negative = (r72 < 0.0) | (r168 < 0.0)
    rank = score.where(available & negative).rank(axis=1, ascending=True, method="first")
    selected = (rank <= 4).fillna(False)

    hourly_vol = close.pct_change(fill_method=None).rolling(168, min_periods=72).std()
    inv = selected.astype(float).div(hourly_vol.replace(0.0, np.nan))
    gross = inv.sum(axis=1).replace(0.0, np.nan)
    raw = -inv.div(gross, axis=0).fillna(0.0) * BEAR_SHORT_GROSS

    bear = direction.shift(1).reindex(close.index).eq("BEAR")
    raw = raw.where(bear, 0.0)

    # Position-level contribution controller. Only misaligned shorts are cut.
    # A short whose recent signed contribution is positive is never reduced by
    # this layer, even during a crash. This is the R3/R4 principle generalized
    # from side-level protection to each position.
    r12 = close.pct_change(12, fill_method=None)
    sigma = close.pct_change(fill_method=None).rolling(72, min_periods=36).std() * np.sqrt(12.0)
    signed_alignment = (-r12).div(sigma.replace(0.0, np.nan))
    misaligned = signed_alignment < 0.0
    scale = np.exp(signed_alignment.clip(lower=-1.05, upper=0.0)).clip(lower=0.35, upper=1.0)
    controlled = raw.where(~misaligned, raw.mul(scale))
    controlled = p1.cap(controlled, BEAR_SHORT_GROSS)

    diag = {
        "architecture": "cross_sectional_short_only_bear_alpha",
        "top_n": 4,
        "gross": BEAR_SHORT_GROSS,
        "high_vol_score": "0.60*rank24 + 0.40*rank72",
        "low_vol_score": "0.45*rank72 + 0.55*rank168",
        "slow_trend_anchor_hours": 336,
        "contribution_window_hours": 12,
        "misaligned_position_floor": 0.35,
        "aligned_positions_preserved": True,
        "uses_future_data": False,
        "active_fraction": float(controlled.abs().sum(axis=1).gt(1e-9).mean()),
    }
    return controlled, diag


def fold_bounds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo = int(cuts[i])
        hi = int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def stability_router(
    results: dict[str, object],
    data,
    direction: pd.Series,
    vol: pd.Series,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> tuple[dict[str, list[dict]], dict]:
    aggregate = {
        name: audit.analyze_result(result, data, direction, vol, train_start, train_end)
        for name, result in results.items()
    }
    folds = fold_bounds(data.close.index, train_start, train_end)
    fold_analyses: dict[str, list[dict]] = {name: [] for name in results}
    for name, result in results.items():
        for lo, hi in folds:
            fold_analyses[name].append(
                audit.analyze_result(result, data, direction, vol, lo, hi)
            )

    routing: dict[str, list[dict]] = {}
    diagnostics: dict[str, list[dict]] = {}
    for state in p1.MATRIX_STATES:
        rows = []
        for name in results:
            agg = aggregate[name]["regimes"]["matrix"][state]
            eligible_fold_metrics = []
            for fa in fold_analyses[name]:
                m = fa["regimes"]["matrix"][state]
                if int(m.get("active_hours", 0)) >= MIN_FOLD_ACTIVE_HOURS:
                    eligible_fold_metrics.append(m)
            stable_wins = sum(
                int(float(m.get("roi", 0.0)) > 0.0 and float(m.get("profit_factor", 0.0)) > 1.0)
                for m in eligible_fold_metrics
            )
            stable_fraction = stable_wins / len(eligible_fold_metrics) if eligible_fold_metrics else 0.0
            eligible = bool(
                int(agg.get("active_hours", 0)) >= 24 * 30
                and float(agg.get("roi", 0.0)) > 0.0
                and float(agg.get("profit_factor", 0.0)) > 1.0
                and len(eligible_fold_metrics) >= 2
                and stable_fraction >= MIN_STABLE_FRACTION
            )
            quality = p1.score_metrics(agg) if eligible else -1e9
            rows.append({
                "sleeve": name,
                "eligible": eligible,
                "quality_score": float(quality),
                "train_roi": float(agg.get("roi", 0.0)),
                "train_pf": float(agg.get("profit_factor", 0.0)),
                "train_dd_abs": float(agg.get("max_drawdown_abs", 0.0)),
                "stable_fold_fraction": float(stable_fraction),
                "eligible_folds": len(eligible_fold_metrics),
                "positive_pf_folds": int(stable_wins),
            })
        rows.sort(key=lambda x: x["quality_score"], reverse=True)
        chosen = [x for x in rows if x["eligible"]][:TOP_SLEEVES_PER_STATE]
        routing[state] = (
            [{"sleeve": x["sleeve"], "weight": 1.0 / len(chosen)} for x in chosen]
            if chosen else []
        )
        diagnostics[state] = rows
    return routing, diagnostics


def build_integrated_native(
    sleeve_targets: dict[str, pd.DataFrame],
    direction: pd.Series,
    vol: pd.Series,
    routing: dict[str, list[dict]],
) -> pd.DataFrame:
    return p1.route_native(sleeve_targets, direction, vol, routing)


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "trade_win_rate_pct": 100.0 * float(m["trade_win_rate"]),
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
    base_sleeve_targets = p1.fixed_sleeves(data)
    bear_targets, bear_diag = bear_native_short_targets(data, direction, vol)
    sleeve_targets = {**base_sleeve_targets, "bear_short": bear_targets}
    sleeve_results = {
        name: p1.run_targets(data, targets, ex, guard, base_cost, p1.NATIVE_GROSS_CAP)
        for name, targets in sleeve_targets.items()
    }

    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, stability = stability_router(
        sleeve_results, data, direction, vol, train_start, train_end
    )
    native_targets = build_integrated_native(sleeve_targets, direction, vol, routing)
    native_result = p1.run_targets(data, native_targets, ex, guard, base_cost, p1.GROSS_CAP)

    # Preserve R98 exactly. Native alpha is additive only in train-stable cells.
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
    bench_analyses = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    env = audit.metric_envelope({n: a["global"] for n, a in bench_analyses.items()})

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, common_start, common_end),
        "bear_short": audit.analyze_result(sleeve_results["bear_short"], data, direction, vol, common_start, common_end),
    }
    cmp = {name: audit.candidate_vs_envelope(a["global"], env) for name, a in full.items() if name != "bear_short"}

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
        "bear_short": audit.analyze_result(sleeve_results["bear_short"], data, direction, vol, hold_start, common_end),
    }
    hold_cmp = {name: audit.candidate_vs_envelope(a["global"], hold_env) for name, a in hold.items() if name != "bear_short"}

    # Severe-cost rerun with routing frozen from base-cost training.
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
        "bear_short": audit.analyze_result(sleeve_sev["bear_short"], data, direction, vol, common_start, common_end),
    }
    severe_cmp = {name: audit.candidate_vs_envelope(a["global"], severe_env) for name, a in severe.items() if name != "bear_short"}

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 2 — bear-native alpha + chronological stability router",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "changes_vs_phase1": [
            "added independent short-only bear alpha sleeve",
            "replaced aggregate-train router eligibility with chronological train-fold stability",
            "removed blanket side-aware cut from the R98 core; R98 is preserved exactly",
            "bear sleeve uses position-level contribution control that only cuts misaligned shorts and preserves aligned shorts",
        ],
        "precommitment": {
            "same_hybrid_alpha_scale_as_phase1": p1.HYBRID_ALPHA_SCALE,
            "no_holdout_parameter_fit": True,
            "train_folds": TRAIN_FOLDS,
            "minimum_stable_fraction": MIN_STABLE_FRACTION,
            "top_sleeves_per_state": TOP_SLEEVES_PER_STATE,
            "bear_short": bear_diag,
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "metadata": metadata,
        },
        "routing": routing,
        "stability_diagnostics": stability,
        "base": {
            "benchmark_envelope": env,
            **full,
            "vs_envelope": cmp,
            "pass_counts": {n: passes(c) for n, c in cmp.items()},
        },
        "holdout": {
            "benchmark_envelope": hold_env,
            **hold,
            "vs_envelope": hold_cmp,
            "pass_counts": {n: passes(c) for n, c in hold_cmp.items()},
        },
        "severe": {
            "benchmark_envelope": severe_env,
            **severe,
            "vs_envelope": severe_cmp,
            "pass_counts": {n: passes(c) for n, c in severe_cmp.items()},
        },
        "horizons": {
            "r98": p1.horizon_stats(r98_result.equity, common_end),
            "native": p1.horizon_stats(native_result.equity, common_end),
            "hybrid": p1.horizon_stats(hybrid_result.equity, common_end),
            "bear_short": p1.horizon_stats(sleeve_results["bear_short"].equity, common_end),
        },
        "promotion": {"r106_promoted": False, "reason": "phase 2 research gate pending evidence review"},
        "disclosure": "Historical research/holdout only. No real orders. Results are not profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "base": {k: compact(v) for k, v in full.items()},
        "holdout": {k: compact(v) for k, v in hold.items()},
        "severe": {k: compact(v) for k, v in severe.items()},
        "pass_counts": {
            "base": {n: passes(c) for n, c in cmp.items()},
            "holdout": {n: passes(c) for n, c in hold_cmp.items()},
            "severe": {n: passes(c) for n, c in severe_cmp.items()},
        },
        "routing": routing,
        "bear_train": {
            k: [x for x in rows if x["sleeve"] == "bear_short"][0]
            for k, rows in stability.items() if k.startswith("BEAR__")
        },
    }, indent=2))


if __name__ == "__main__":
    main()
