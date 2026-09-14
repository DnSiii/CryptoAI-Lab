from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.signals import StrategySpec, build_targets
import run_v99_r98_friction_aware_hybrid as r98
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_native_all_regime_engine.json"
TRAIN_END = r98.TRAIN_END
GROSS_CAP = float(r98.r86.P15["gross_cap"])
NATIVE_GROSS_CAP = 1.50
HYBRID_ALPHA_SCALE = 0.30
HORIZONS = (7, 30, 90, 180, 365)

# One structural hypothesis per alpha family. No grid search in R106 phase 1.
# The impulse sleeve reuses the historically selected V14 signal specification.
SLEEVE_SPECS = {
    "trend": StrategySpec(
        family="trend", lookback=168, rebalance=12,
        fast=72, slow=336, vol_lookback=168, vol_target=0.55,
        leverage_cap=1.25, threshold=0.010,
    ),
    "impulse": StrategySpec(
        family="impulse", lookback=48, rebalance=3, top_n=2,
        fast=24, slow=336, vol_lookback=168, vol_target=0.8,
        leverage_cap=1.0, trend_lookback=168, long_short_balance=0.8,
        threshold=0.015, exit_lookback=24, volume_multiple=2.0,
        stop_loss=0.03, trailing_stop=0.20, max_holding=168,
        rebalance_phase=0, trend_filter_hours=336, cooldown_hours=24,
    ),
    "meanrev": StrategySpec(
        family="meanrev", lookback=72, rebalance=6,
        vol_lookback=168, vol_target=0.40, leverage_cap=0.85,
        trend_lookback=168, threshold=2.0,
    ),
    "funding": StrategySpec(
        family="funding", lookback=168, rebalance=8, top_n=3,
        vol_lookback=336, vol_target=0.30, leverage_cap=0.70,
        trend_lookback=336, long_short_balance=0.5, threshold=0.00001,
    ),
}

MATRIX_STATES = tuple(
    f"{d}__{v}"
    for d in ("BULL", "BEAR", "SIDEWAYS")
    for v in ("HIGH_VOLATILITY", "LOW_VOLATILITY")
)


def cap(targets: pd.DataFrame, limit: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (float(limit) / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0)


def build_r98_targets(data, raw, ex, guard, gross, cost: float):
    parent, parent_targets, protect, pdiag, _ = r98.r86.build_parent_r73(
        data, raw, ex, guard, gross, cost
    )
    gate, gdiag = r98.r88.daily_gate(parent.equity)
    parent_gross = parent_targets.abs().sum(axis=1)
    high = gate & parent_gross.ge(r98.R97_GROSS_THRESHOLD)
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * r98.R88_SCALE
    if high.any():
        targets.loc[high, :] = parent_targets.loc[high, :] * r98.R96_SCALE
    targets = cap(targets, GROSS_CAP)
    result = r98.r36.run(data, targets, ex, cost, GROSS_CAP, guard)
    return targets, result, {
        **pdiag,
        **gdiag,
        "qualified_high_fraction": float(high.mean()),
        "protect_overlap_high_fraction": float(
            (high & protect.reindex(high.index).fillna(False)).mean()
        ),
    }


def run_targets(data, targets, ex, guard, cost: float, gross_cap: float):
    targets = cap(targets, gross_cap)
    return r98.r36.run(data, targets, ex, cost, gross_cap, guard)


def fixed_sleeves(data) -> dict[str, pd.DataFrame]:
    return {
        name: cap(build_targets(data, spec), NATIVE_GROSS_CAP)
        for name, spec in SLEEVE_SPECS.items()
    }


def score_metrics(m: dict) -> float:
    """Train-only quality score; coarse ranking, not continuous parameter fitting."""
    roi = float(m.get("roi", 0.0))
    pf = float(m.get("profit_factor", 0.0))
    dd = float(m.get("max_drawdown_abs", 1.0))
    hit = float(m.get("positive_day_ratio", 0.0))
    hours = int(m.get("active_hours", 0))
    if hours < 24 * 30 or roi <= 0.0 or pf <= 1.0:
        return -1e9
    wealth = math.log(max(1.0 + roi, 1e-9))
    return float(wealth * max(pf, 0.25) * max(hit, 0.10) / max(dd, 0.05))


def train_router(
    sleeve_analyses: dict[str, dict],
) -> tuple[dict[str, list[dict]], dict]:
    routing: dict[str, list[dict]] = {}
    diagnostics = {}
    for state in MATRIX_STATES:
        rows = []
        for name, analysis in sleeve_analyses.items():
            metrics = analysis["regimes"]["matrix"][state]
            rows.append((name, score_metrics(metrics), metrics))
        rows.sort(key=lambda x: x[1], reverse=True)
        eligible = [x for x in rows if x[1] > -1e8][:2]
        if not eligible:
            routing[state] = []
        elif len(eligible) == 1:
            routing[state] = [{"sleeve": eligible[0][0], "weight": 1.0}]
        else:
            scores = np.array([max(x[1], 1e-9) for x in eligible], dtype=float)
            weights = scores / scores.sum()
            routing[state] = [
                {"sleeve": eligible[i][0], "weight": float(weights[i])}
                for i in range(len(eligible))
            ]
        diagnostics[state] = [
            {
                "sleeve": name,
                "score": float(score),
                "roi": float(metrics.get("roi", 0.0)),
                "profit_factor": float(metrics.get("profit_factor", 0.0)),
                "max_drawdown_abs": float(metrics.get("max_drawdown_abs", 0.0)),
                "positive_day_ratio": float(metrics.get("positive_day_ratio", 0.0)),
                "eligible": bool(score > -1e8),
            }
            for name, score, metrics in rows
        ]
    return routing, diagnostics


def route_native(
    sleeve_targets: dict[str, pd.DataFrame],
    direction: pd.Series,
    vol: pd.Series,
    routing: dict[str, list[dict]],
) -> pd.DataFrame:
    template = next(iter(sleeve_targets.values()))
    out = pd.DataFrame(0.0, index=template.index, columns=template.columns)
    # Decision uses prior known regime only.
    d = direction.shift(1).reindex(template.index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(template.index).fillna("UNKNOWN")
    state = d.astype(str) + "__" + v.astype(str)
    for key, items in routing.items():
        mask = state.eq(key)
        if not mask.any() or not items:
            continue
        block = pd.DataFrame(0.0, index=template.index, columns=template.columns)
        for item in items:
            block = block.add(
                sleeve_targets[item["sleeve"]] * float(item["weight"]),
                fill_value=0.0,
            )
        out.loc[mask, :] = block.loc[mask, :]
    return cap(out, NATIVE_GROSS_CAP)


def side_aware_quality_controller(
    targets: pd.DataFrame,
    close: pd.DataFrame,
    direction: pd.Series,
    vol: pd.Series,
) -> tuple[pd.DataFrame, dict]:
    """Reduce only the side fighting a confirmed violent regime; never both sides."""
    out = targets.copy()
    d = direction.shift(1).reindex(out.index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(out.index).fillna("UNKNOWN")
    btc = close["BTCUSDT"].pct_change(24, fill_method=None).shift(1).reindex(out.index)
    bear_hv = d.eq("BEAR") & v.eq("HIGH_VOLATILITY") & btc.le(-0.025)
    bull_hv = d.eq("BULL") & v.eq("HIGH_VOLATILITY") & btc.ge(0.025)

    # Preserve the side aligned with the move. Only the fighting side is reduced.
    if bear_hv.any():
        positives = out.loc[bear_hv].clip(lower=0.0) * 0.45
        negatives = out.loc[bear_hv].clip(upper=0.0)
        out.loc[bear_hv] = positives + negatives
    if bull_hv.any():
        positives = out.loc[bull_hv].clip(lower=0.0)
        negatives = out.loc[bull_hv].clip(upper=0.0) * 0.45
        out.loc[bull_hv] = positives + negatives
    return cap(out, GROSS_CAP), {
        "bear_high_vol_side_cut_fraction": float(bear_hv.mean()),
        "bull_high_vol_side_cut_fraction": float(bull_hv.mean()),
        "aligned_side_preserved": True,
        "global_risk_cut_used": False,
    }


def horizon_stats(equity: pd.Series, end: pd.Timestamp) -> dict:
    out = {}
    for days in HORIZONS:
        start = end - pd.Timedelta(days=int(days))
        values = equity.loc[equity.index >= start]
        out[str(days)] = r98.r36.stats(values)
    return out


def envelope_comparison(candidate_analysis: dict, benchmark_analyses: dict[str, dict]):
    env = audit.metric_envelope({n: x["global"] for n, x in benchmark_analyses.items()})
    return env, audit.candidate_vs_envelope(candidate_analysis["global"], env)


def count_passes(comparison: dict) -> tuple[int, int]:
    return sum(int(x.get("passed", False)) for x in comparison.values()), len(comparison)


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    benchmarks = r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    direction, vol, regime_diag = audit.classify_regimes(data.close)

    r98_targets, r98_result, r98_diag = build_r98_targets(
        data, raw, ex, guard, gross, base_cost
    )

    sleeve_targets = fixed_sleeves(data)
    sleeve_results = {
        name: run_targets(data, targets, ex, guard, base_cost, NATIVE_GROSS_CAP)
        for name, targets in sleeve_targets.items()
    }

    train_end = min(TRAIN_END, common_end)
    train_sleeve_analyses = {
        name: audit.analyze_result(result, data, direction, vol, common_start, train_end)
        for name, result in sleeve_results.items()
    }
    routing, routing_diag = train_router(train_sleeve_analyses)
    native_targets = route_native(sleeve_targets, direction, vol, routing)
    native_targets, native_risk_diag = side_aware_quality_controller(
        native_targets, data.close, direction, vol
    )
    native_result = run_targets(
        data, native_targets, ex, guard, base_cost, GROSS_CAP
    )

    # Add native alpha without shrinking the validated R98 growth stream.
    hybrid_targets = r98_targets.add(native_targets * HYBRID_ALPHA_SCALE, fill_value=0.0)
    hybrid_targets, hybrid_risk_diag = side_aware_quality_controller(
        hybrid_targets, data.close, direction, vol
    )
    hybrid_targets = cap(hybrid_targets, GROSS_CAP)
    hybrid_result = run_targets(data, hybrid_targets, ex, guard, base_cost, GROSS_CAP)

    # Same exact benchmark envelope used by R105.
    benchmark_results = {}
    for name, item in benchmarks.items():
        benchmark_results[name] = audit.exact_benchmark_result(
            item, float(item["execution"]["base_cost_per_side"])
        )
    benchmark_analyses = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(benchmark_results.items(), benchmarks.values())
    }

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, common_start, common_end),
        "sleeves": {
            name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
            for name, result in sleeve_results.items()
        },
    }
    full_env = audit.metric_envelope({n: a["global"] for n, a in benchmark_analyses.items()})
    full_cmp = {
        name: audit.candidate_vs_envelope(full[name]["global"], full_env)
        for name in ("r98", "native", "hybrid")
    }

    hold_idx = data.close.index[(data.close.index > TRAIN_END) & (data.close.index >= common_start) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end)
        for (name, result), item in zip(benchmark_results.items(), benchmarks.values())
    }
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, hold_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, hold_start, common_end),
    }
    hold_cmp = {
        name: audit.candidate_vs_envelope(hold[name]["global"], hold_env)
        for name in hold
    }

    # Cost robustness for the integrated hybrid only; routing stays frozen from base-cost train.
    r98_sev_targets, r98_sev_result, _ = build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    native_sev_result = run_targets(data, native_targets, ex, guard, severe_cost, GROSS_CAP)
    hybrid_sev_targets = cap(r98_sev_targets.add(native_targets * HYBRID_ALPHA_SCALE, fill_value=0.0), GROSS_CAP)
    hybrid_sev_targets, _ = side_aware_quality_controller(hybrid_sev_targets, data.close, direction, vol)
    hybrid_sev_result = run_targets(data, hybrid_sev_targets, ex, guard, severe_cost, GROSS_CAP)

    severe_bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench_analyses = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(severe_bench_results.items(), benchmarks.values())
    }
    severe_env = audit.metric_envelope({n: a["global"] for n, a in severe_bench_analyses.items()})
    severe = {
        "r98": audit.analyze_result(r98_sev_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_sev_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_sev_result, data, direction, vol, common_start, common_end),
    }
    severe_cmp = {
        name: audit.candidate_vs_envelope(severe[name]["global"], severe_env)
        for name in severe
    }

    full_counts = {name: count_passes(cmp) for name, cmp in full_cmp.items()}
    hold_counts = {name: count_passes(cmp) for name, cmp in hold_cmp.items()}
    severe_counts = {name: count_passes(cmp) for name, cmp in severe_cmp.items()}

    out = {
        "study": "V99 R106 native all-regime engine — structural phase 1",
        "status": "RESEARCH_ONLY_R106_NOT_PROMOTED",
        "branch": "research/v99-r106-native-all-regime-engine",
        "objective": "preserve/exceed R98 growth while adding independent regime-specialized alpha and side-aware risk; eventually dominate the best V13-V16 metric envelope rather than only V16",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "sleeves": {name: spec.to_dict() for name, spec in SLEEVE_SPECS.items()},
            "router_fit_scope": "training segment only through R98 TRAIN_END",
            "router_top_sleeves_per_regime": 2,
            "native_gross_cap": NATIVE_GROSS_CAP,
            "portfolio_gross_cap": GROSS_CAP,
            "hybrid_alpha_scale": HYBRID_ALPHA_SCALE,
            "side_aware_rule": "in confirmed high-vol bear, reduce longs only; in confirmed high-vol bull, reduce shorts only; preserve aligned side",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "v15_metadata": metadata,
        },
        "router": routing,
        "router_training_diagnostics": routing_diag,
        "risk_diagnostics": {
            "native": native_risk_diag,
            "hybrid": hybrid_risk_diag,
            "r98": r98_diag,
        },
        "base": {
            "benchmarks": benchmark_analyses,
            "benchmark_envelope": full_env,
            "r98": full["r98"],
            "native": full["native"],
            "hybrid": full["hybrid"],
            "sleeves": full["sleeves"],
            "vs_envelope": full_cmp,
            "pass_counts": {k: {"passed": v[0], "total": v[1]} for k, v in full_counts.items()},
        },
        "holdout": {
            "start": hold_start.isoformat(),
            "benchmark_envelope": hold_env,
            "r98": hold["r98"],
            "native": hold["native"],
            "hybrid": hold["hybrid"],
            "vs_envelope": hold_cmp,
            "pass_counts": {k: {"passed": v[0], "total": v[1]} for k, v in hold_counts.items()},
        },
        "severe_cost": {
            "benchmark_envelope": severe_env,
            "r98": severe["r98"],
            "native": severe["native"],
            "hybrid": severe["hybrid"],
            "vs_envelope": severe_cmp,
            "pass_counts": {k: {"passed": v[0], "total": v[1]} for k, v in severe_counts.items()},
        },
        "horizons": {
            "r98": horizon_stats(r98_result.equity, common_end),
            "native": horizon_stats(native_result.equity, common_end),
            "hybrid": horizon_stats(hybrid_result.equity, common_end),
        },
        "regime_taxonomy": {
            "causal": True,
            "decision_uses_prior_regime": True,
            "coverage": {
                "directional": direction.value_counts(normalize=True).to_dict(),
                "volatility": vol.value_counts(normalize=True).to_dict(),
            },
        },
        "promotion": {
            "r106_promoted": False,
            "reason": "phase-1 structural probe only; no promotion before native sleeves, router, side-aware controller and holdout/cost/regime results are reviewed together",
        },
        "disclosure": "Historical research and holdout diagnostics only; not a profit promise and no real orders are enabled.",
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    def g(label: str, analysis: dict, counts: tuple[int, int]):
        m = analysis["global"]
        return {
            "label": label,
            "roi_pct": round(100.0 * float(m["roi"]), 2),
            "max_dd_pct": round(-100.0 * float(m["max_drawdown_abs"]), 2),
            "worst_day_pct": round(-100.0 * float(m["worst_day_abs"]), 2),
            "win_rate_pct": round(100.0 * float(m["trade_win_rate"]), 2),
            "profit_factor": round(float(m["profit_factor"]), 3),
            "positive_days_pct": round(100.0 * float(m["positive_day_ratio"]), 2),
            "envelope_passes": f"{counts[0]}/{counts[1]}",
        }

    print(json.dumps({
        "base": [
            g("R98", full["r98"], full_counts["r98"]),
            g("R106_NATIVE", full["native"], full_counts["native"]),
            g("R106_HYBRID", full["hybrid"], full_counts["hybrid"]),
        ],
        "holdout": [
            g("R98", hold["r98"], hold_counts["r98"]),
            g("R106_NATIVE", hold["native"], hold_counts["native"]),
            g("R106_HYBRID", hold["hybrid"], hold_counts["hybrid"]),
        ],
        "severe": [
            g("R98", severe["r98"], severe_counts["r98"]),
            g("R106_NATIVE", severe["native"], severe_counts["native"]),
            g("R106_HYBRID", severe["hybrid"], severe_counts["hybrid"]),
        ],
        "router": routing,
    }, indent=2))


if __name__ == "__main__":
    main()
