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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase4_bear_subregime.json"
MIN_ACTIVE_HOURS = 72
MIN_STABLE_FRACTION = 0.60


def normalize_side(raw: pd.DataFrame, side: str, gross: float = 1.0) -> pd.DataFrame:
    if side == "long":
        x = raw.clip(lower=0.0)
    else:
        x = -raw.clip(upper=0.0)
    g = x.sum(axis=1).replace(0.0, np.nan)
    norm = x.div(g, axis=0).fillna(0.0) * float(gross)
    return norm if side == "long" else -norm


def bear_substates(data, direction: pd.Series, vol: pd.Series):
    close = data.close.astype(float)
    btc12 = close["BTCUSDT"].pct_change(12, fill_method=None).shift(1)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None).shift(1)
    breadth24 = close.pct_change(24, fill_method=None).gt(0.0).mean(axis=1).shift(1)
    d = direction.shift(1).reindex(close.index)
    v = vol.shift(1).reindex(close.index)
    bhv = d.eq("BEAR") & v.eq("HIGH_VOLATILITY")
    continuation = bhv & btc12.le(0.0) & btc24.lt(0.0) & breadth24.lt(0.50)
    squeeze = bhv & btc12.gt(0.0) & breadth24.gt(0.50)
    transition = bhv & ~(continuation | squeeze)
    return {
        "continuation": continuation.fillna(False),
        "squeeze": squeeze.fillna(False),
        "transition": transition.fillna(False),
    }, {
        "continuation_fraction": float(continuation.mean()),
        "squeeze_fraction": float(squeeze.mean()),
        "transition_fraction": float(transition.mean()),
        "causal": True,
        "btc_windows": [12, 24],
        "breadth_window": 24,
        "breadth_split": 0.50,
    }


def candidate_subsleeves(data, substates):
    raw = p3.build_targets(data, p3.DISPERSION_SPEC)
    short = normalize_side(raw, "short", 1.0).where(substates["continuation"], 0.0)
    long = normalize_side(raw, "long", 1.0).where(substates["squeeze"], 0.0)
    return {
        "crash_continuation_short": p1.cap(short, 1.0),
        "bear_squeeze_long": p1.cap(long, 1.0),
    }


def fold_bounds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), p2.TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(p2.TRAIN_FOLDS):
        lo, hi = int(cuts[i]), int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def validate_subsleeves(results, targets, data, direction, vol, train_start, train_end):
    routing = {}
    diagnostics = {}
    folds = fold_bounds(data.close.index, train_start, train_end)
    for name, result in results.items():
        aggregate = audit.analyze_result(result, data, direction, vol, train_start, train_end)["global"]
        rows = []
        for lo, hi in folds:
            active = int(targets[name].loc[lo:hi].abs().sum(axis=1).gt(1e-9).sum())
            m = audit.analyze_result(result, data, direction, vol, lo, hi)["global"]
            rows.append({
                "start": lo.isoformat(), "end": hi.isoformat(), "active_hours": active,
                "roi": float(m.get("roi", 0.0)), "pf": float(m.get("profit_factor", 0.0)),
                "positive": bool(active >= 24 and float(m.get("roi", 0.0)) > 0.0 and float(m.get("profit_factor", 0.0)) > 1.0),
            })
        eligible_rows = [x for x in rows if x["active_hours"] >= 24]
        positive = sum(int(x["positive"]) for x in eligible_rows)
        stable_fraction = positive / len(eligible_rows) if eligible_rows else 0.0
        total_active = int(targets[name].loc[train_start:train_end].abs().sum(axis=1).gt(1e-9).sum())
        eligible = bool(
            total_active >= MIN_ACTIVE_HOURS
            and float(aggregate.get("roi", 0.0)) > 0.0
            and float(aggregate.get("profit_factor", 0.0)) > 1.0
            and len(eligible_rows) >= 2
            and stable_fraction >= MIN_STABLE_FRACTION
        )
        routing[name] = eligible
        diagnostics[name] = {
            "eligible": eligible,
            "train_roi": float(aggregate.get("roi", 0.0)),
            "train_pf": float(aggregate.get("profit_factor", 0.0)),
            "train_dd_abs": float(aggregate.get("max_drawdown_abs", 0.0)),
            "train_active_hours": total_active,
            "stable_fraction": float(stable_fraction),
            "eligible_folds": len(eligible_rows),
            "positive_folds": positive,
            "folds": rows,
        }
    return routing, diagnostics


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


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)

    # Rebuild phase-3 native engine exactly.
    phase3_sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    phase3_sleeves = {**phase3_sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    phase3_results = {n: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for n, t in phase3_sleeves.items()}
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    phase3_routing, phase3_stability = p2.stability_router(phase3_results, data, direction, vol, train_start, train_end)
    phase3_native = p1.route_native(phase3_sleeves, direction, vol, phase3_routing)

    substates, subdiag = bear_substates(data, direction, vol)
    subtargets = candidate_subsleeves(data, substates)
    subresults = {n: p1.run_targets(data, t, ex, guard, base_cost, 1.0) for n, t in subtargets.items()}
    subroute, substability = validate_subsleeves(subresults, subtargets, data, direction, vol, train_start, train_end)

    phase4_native = phase3_native.copy()
    # Phase-3 BEAR+HIGH_VOL is empty. Add only independently validated sub-state alpha.
    if subroute.get("crash_continuation_short"):
        phase4_native = phase4_native.add(subtargets["crash_continuation_short"], fill_value=0.0)
    if subroute.get("bear_squeeze_long"):
        phase4_native = phase4_native.add(subtargets["bear_squeeze_long"], fill_value=0.0)
    phase4_native = p1.cap(phase4_native, p1.NATIVE_GROSS_CAP)
    native_result = p1.run_targets(data, phase4_native, ex, guard, base_cost, p1.GROSS_CAP)

    hybrid_targets = p1.cap(r98_targets.add(phase4_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    hybrid_result = p1.run_targets(data, hybrid_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {n: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for n, item in benchmarks.items()}
    bench = {n: audit.analyze_result(res, item["data"], direction, vol, common_start, common_end) for (n, res), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: x["global"] for n, x in bench.items()})

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, common_start, common_end),
    }
    cmp = {n: audit.candidate_vs_envelope(x["global"], env) for n, x in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {n: audit.analyze_result(res, item["data"], direction, vol, hold_start, common_end) for (n, res), item in zip(bench_results.items(), benchmarks.values())}
    hold_env = audit.metric_envelope({n: x["global"] for n, x in hold_bench.items()})
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, hold_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, hold_start, common_end),
    }
    hold_cmp = {n: audit.candidate_vs_envelope(x["global"], hold_env) for n, x in hold.items()}

    # Severe-cost validation with routing frozen from base-cost training.
    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    native_sev = p1.run_targets(data, phase4_native, ex, guard, severe_cost, p1.GROSS_CAP)
    hybrid_sev_targets = p1.cap(r98_sev_targets.add(phase4_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    hybrid_sev = p1.run_targets(data, hybrid_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_sev, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_sev, data, direction, vol, common_start, common_end),
    }

    def pass_count(c):
        return {"passed": sum(int(v["passed"]) for v in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 4 — causal bear high-vol crash-vs-squeeze router",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "substate_definition": subdiag,
        "substate_train_validation": substability,
        "substate_enabled": subroute,
        "phase3_routing": phase3_routing,
        "phase3_stability": phase3_stability,
        "base": {**full, "vs_envelope": cmp, "pass_counts": {n: pass_count(c) for n, c in cmp.items()}},
        "holdout": {**hold, "vs_envelope": hold_cmp, "pass_counts": {n: pass_count(c) for n, c in hold_cmp.items()}},
        "severe": severe,
        "bear_high_vol": {n: x["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"] for n, x in full.items()},
        "horizons": {n: p1.horizon_stats(res.equity, common_end) for n, res in {"r98": r98_result, "native": native_result, "hybrid": hybrid_result}.items()},
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "promotion": {"r106_phase4_promoted": False, "reason": "research evidence review required"},
        "disclosure": "Historical research/holdout only. No real orders. No future data in substate classification.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "base": {n: compact(x) for n, x in full.items()},
        "holdout": {n: compact(x) for n, x in hold.items()},
        "severe": {n: compact(x) for n, x in severe.items()},
        "substate_enabled": subroute,
        "substate_train_validation": substability,
        "bear_high_vol": out["bear_high_vol"],
        "pass_counts": {n: pass_count(c) for n, c in cmp.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
