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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase4_bear_subregimes.json"
TRAIN_FOLDS = 4
MIN_ACTIVE_HOURS = 24 * 10
MIN_STABLE_FRACTION = 2.0 / 3.0


def bear_high_vol_substates(close: pd.DataFrame, direction: pd.Series, vol: pd.Series) -> dict[str, pd.Series]:
    """Causal BEAR+HIGH_VOL split. All market features are shifted one hour."""
    idx = close.index
    d = direction.shift(1).reindex(idx).fillna("UNKNOWN")
    v = vol.shift(1).reindex(idx).fillna("UNKNOWN")
    bear_hv = d.eq("BEAR") & v.eq("HIGH_VOLATILITY")

    btc = close["BTCUSDT"].astype(float)
    btc24 = btc.pct_change(24, fill_method=None).shift(1)
    btc72 = btc.pct_change(72, fill_method=None).shift(1)
    breadth24 = (close.pct_change(24, fill_method=None) > 0.0).mean(axis=1).shift(1)

    # Structural, predeclared states: violent continuation, countertrend squeeze,
    # and the unresolved middle. Crash gets precedence if conditions overlap.
    crash = bear_hv & ((btc24 <= -0.03) | (btc72 <= -0.06)) & (breadth24 <= 0.40)
    squeeze = bear_hv & ~crash & ((btc24 >= 0.025) | (breadth24 >= 0.65))
    mixed = bear_hv & ~crash & ~squeeze
    return {
        "CRASH_CONTINUATION": crash.fillna(False),
        "BEAR_SQUEEZE": squeeze.fillna(False),
        "MIXED": mixed.fillna(False),
    }


def normalize_one_side(targets: pd.DataFrame, gross: float = 1.0) -> pd.DataFrame:
    g = targets.abs().sum(axis=1).replace(0.0, np.nan)
    return targets.div(g, axis=0).fillna(0.0) * float(gross)


def fixed_bear_substate_sleeves(data, direction: pd.Series) -> dict[str, pd.DataFrame]:
    base = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)

    short_breakdown = normalize_one_side(breakout.clip(upper=0.0), gross=1.0)
    rebound_impulse = normalize_one_side(base["impulse"].clip(lower=0.0), gross=0.90)
    rebound_trend = normalize_one_side(base["trend"].clip(lower=0.0), gross=0.90)

    return {
        "short_breakdown": short_breakdown,
        "bear_dispersion": dispersion,
        "rebound_impulse": rebound_impulse,
        "rebound_trend": rebound_trend,
        "funding": base["funding"],
    }


def segment_metrics(equity: pd.Series, mask: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    ret = equity.astype(float).pct_change(fill_method=None).reindex(mask.index).fillna(0.0)
    use = mask.reindex(ret.index).fillna(False) & ret.index.to_series().between(start, end).to_numpy()
    r = ret.loc[use]
    if len(r) < 2:
        return {"active_hours": int(len(r)), "roi": 0.0, "profit_factor": 0.0, "max_drawdown_abs": 1.0, "positive_hour_ratio": 0.0}
    wealth = (1.0 + r).cumprod()
    dd = wealth / wealth.cummax() - 1.0
    pos = float(r[r > 0.0].sum())
    neg = float(-r[r < 0.0].sum())
    return {
        "active_hours": int(len(r)),
        "roi": float(wealth.iloc[-1] - 1.0),
        "profit_factor": float(pos / neg) if neg > 1e-12 else (999.0 if pos > 0 else 0.0),
        "max_drawdown_abs": float(abs(dd.min())) if len(dd) else 0.0,
        "positive_hour_ratio": float((r > 0.0).mean()),
    }


def fold_bounds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo, hi = int(cuts[i]), int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def choose_substate_router(results: dict[str, object], substates: dict[str, pd.Series], index: pd.DatetimeIndex, train_start: pd.Timestamp, train_end: pd.Timestamp):
    folds = fold_bounds(index, train_start, train_end)
    routing: dict[str, list[dict]] = {}
    diagnostics: dict[str, list[dict]] = {}

    # Deliberately narrow candidate menus by economic purpose.
    menus = {
        "CRASH_CONTINUATION": ("short_breakdown", "bear_dispersion", "funding"),
        "BEAR_SQUEEZE": ("rebound_impulse", "rebound_trend", "funding"),
        "MIXED": ("funding", "bear_dispersion"),
    }

    for state, names in menus.items():
        mask = substates[state]
        rows = []
        for name in names:
            eq = results[name].equity
            agg = segment_metrics(eq, mask, train_start, train_end)
            fm = [segment_metrics(eq, mask, lo, hi) for lo, hi in folds]
            eligible_folds = [m for m in fm if m["active_hours"] >= 24 * 3]
            wins = sum(int(m["roi"] > 0.0 and m["profit_factor"] > 1.0) for m in eligible_folds)
            stable = wins / len(eligible_folds) if eligible_folds else 0.0
            eligible = bool(
                agg["active_hours"] >= MIN_ACTIVE_HOURS
                and agg["roi"] > 0.0
                and agg["profit_factor"] > 1.05
                and len(eligible_folds) >= 2
                and stable >= MIN_STABLE_FRACTION
            )
            quality = (
                np.log(max(1.0 + agg["roi"], 1e-9))
                * max(agg["profit_factor"], 0.25)
                / max(agg["max_drawdown_abs"], 0.05)
                if eligible else -1e9
            )
            rows.append({
                "sleeve": name,
                "eligible": eligible,
                "quality_score": float(quality),
                "train": agg,
                "stable_fold_fraction": float(stable),
                "eligible_folds": len(eligible_folds),
                "positive_pf_folds": int(wins),
            })
        rows.sort(key=lambda x: x["quality_score"], reverse=True)
        chosen = next((x for x in rows if x["eligible"]), None)
        routing[state] = ([{"sleeve": chosen["sleeve"], "weight": 1.0}] if chosen else [])
        diagnostics[state] = rows
    return routing, diagnostics


def route_substates(sleeves: dict[str, pd.DataFrame], substates: dict[str, pd.Series], routing: dict[str, list[dict]]) -> pd.DataFrame:
    template = next(iter(sleeves.values()))
    out = pd.DataFrame(0.0, index=template.index, columns=template.columns)
    for state, items in routing.items():
        if not items:
            continue
        mask = substates[state].reindex(out.index).fillna(False)
        if not mask.any():
            continue
        block = pd.DataFrame(0.0, index=out.index, columns=out.columns)
        for item in items:
            block = block.add(sleeves[item["sleeve"]] * float(item["weight"]), fill_value=0.0)
        out.loc[mask, :] = block.loc[mask, :]
    return p1.cap(out, p1.NATIVE_GROSS_CAP)


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

    # Rebuild phase-3 router exactly outside BEAR+HIGH_VOL.
    phase3_sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    phase3_sleeves = {**phase3_sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    phase3_results = {name: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for name, t in phase3_sleeves.items()}

    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    phase3_routing, phase3_stability = p2.stability_router(phase3_results, data, direction, vol, train_start, train_end)
    phase3_native = p1.route_native(phase3_sleeves, direction, vol, phase3_routing)

    substates = bear_high_vol_substates(data.close, direction, vol)
    sub_sleeves = fixed_bear_substate_sleeves(data, direction)
    sub_results = {name: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for name, t in sub_sleeves.items()}
    sub_routing, sub_diag = choose_substate_router(sub_results, substates, data.close.index, train_start, train_end)
    sub_native = route_substates(sub_sleeves, substates, sub_routing)

    # F3 has no BEAR+HIGH_VOL route; preserve every other cell and fill only this hole.
    native_targets = p1.cap(phase3_native.add(sub_native, fill_value=0.0), p1.NATIVE_GROSS_CAP)
    native_result = p1.run_targets(data, native_targets, ex, guard, base_cost, p1.GROSS_CAP)

    phase3_hybrid_targets = p1.cap(r98_targets.add(phase3_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    phase3_hybrid_result = p1.run_targets(data, phase3_hybrid_targets, ex, guard, base_cost, p1.GROSS_CAP)

    hybrid_targets = p1.cap(r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    hybrid_result = p1.run_targets(data, hybrid_targets, ex, guard, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for name, item in benchmarks.items()}
    bench_analyses = {name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end) for (name, result), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench_analyses.items()})

    full = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, common_start, common_end),
        "phase3_hybrid": audit.analyze_result(phase3_hybrid_result, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, common_start, common_end),
    }
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items() if n in ("r98", "native", "hybrid")}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end) for (name, result), item in zip(bench_results.items(), benchmarks.values())}
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        "r98": audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end),
        "phase3_hybrid": audit.analyze_result(phase3_hybrid_result, data, direction, vol, hold_start, common_end),
        "native": audit.analyze_result(native_result, data, direction, vol, hold_start, common_end),
        "hybrid": audit.analyze_result(hybrid_result, data, direction, vol, hold_start, common_end),
    }
    hold_cmp = {n: audit.candidate_vs_envelope(a["global"], hold_env) for n, a in hold.items() if n in ("r98", "native", "hybrid")}

    # Severe cost with train-frozen routing.
    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    native_sev = p1.run_targets(data, native_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    hybrid_sev_targets = p1.cap(r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    hybrid_sev = p1.run_targets(data, hybrid_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "native": audit.analyze_result(native_sev, data, direction, vol, common_start, common_end),
        "hybrid": audit.analyze_result(hybrid_sev, data, direction, vol, common_start, common_end),
    }

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    # Dedicated substate performance using exact equity streams.
    substate_performance = {}
    for state, mask in substates.items():
        substate_performance[state] = {
            "hours": int(mask.sum()),
            "r98": segment_metrics(r98_result.equity, mask, common_start, common_end),
            "phase3_hybrid": segment_metrics(phase3_hybrid_result.equity, mask, common_start, common_end),
            "phase4_hybrid": segment_metrics(hybrid_result.equity, mask, common_start, common_end),
        }

    out = {
        "study": "V99 R106 phase 4 — BEAR+HIGH_VOL crash continuation vs squeeze router",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "phase3_frozen_outside_bear_high_vol": True,
            "no_grid_search": True,
            "hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE,
            "substates": {
                "CRASH_CONTINUATION": "BEAR+HIGH_VOL and (BTC24<=-3% or BTC72<=-6%) and breadth24<=40%",
                "BEAR_SQUEEZE": "BEAR+HIGH_VOL, not crash, and (BTC24>=+2.5% or breadth24>=65%)",
                "MIXED": "remaining BEAR+HIGH_VOL",
            },
            "aligned_short_preservation_principle": True,
        },
        "routing_phase3": phase3_routing,
        "routing_substates": sub_routing,
        "substate_train_diagnostics": sub_diag,
        "substate_performance": substate_performance,
        "base": {**full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": {**hold, "vs_envelope": hold_cmp, "pass_counts": {n: passes(c) for n, c in hold_cmp.items()}},
        "severe": severe,
        "data": {
            "common_start": common_start.isoformat(), "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined, "metadata": metadata,
        },
        "disclosure": "Historical research/holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "substate_routing": sub_routing,
        "substate_train_diagnostics": sub_diag,
        "substate_performance": substate_performance,
        "pass_counts": {"base": {n: passes(c) for n, c in cmp.items()}, "holdout": {n: passes(c) for n, c in hold_cmp.items()}},
    }, indent=2, default=audit.safe_float))


if __name__ == "__main__":
    main()
