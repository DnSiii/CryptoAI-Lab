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
import run_v99_r106_phase5_segregated_sleeve_risk as p5
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase6_incremental_alpha_router.json"
MIN_STABLE_FOLDS = 3
MAX_DD_RATIO = 1.05
MIN_TRAIN_WEALTH_RATIO = 1.01

STATE_MENUS = {
    "BULL__HIGH_VOLATILITY": ("trend", "impulse", "breakout"),
    "BULL__LOW_VOLATILITY": ("trend", "funding", "meanrev"),
    "BEAR__HIGH_VOLATILITY": ("bear_dispersion", "funding", "breakout"),
    "BEAR__LOW_VOLATILITY": ("breakout", "funding", "bear_dispersion"),
    "SIDEWAYS__HIGH_VOLATILITY": ("impulse", "meanrev", "funding"),
    "SIDEWAYS__LOW_VOLATILITY": ("meanrev", "funding", "trend"),
}


def state_masks(index: pd.DatetimeIndex, direction: pd.Series, vol: pd.Series) -> dict[str, pd.Series]:
    d = direction.shift(1).reindex(index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(index).fillna("UNKNOWN")
    state = d.astype(str) + "__" + v.astype(str)
    return {key: state.eq(key) for key in p1.MATRIX_STATES}


def path_from_returns(ret: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    r = ret.loc[(ret.index >= start) & (ret.index <= end)].fillna(0.0).astype(float)
    if len(r) < 2:
        return {"roi": 0.0, "max_dd_abs": 1.0, "worst_day_abs": 1.0, "positive_days": 0.0}
    wealth = (1.0 + r.clip(lower=-0.999999)).cumprod()
    dd = wealth / wealth.cummax() - 1.0
    daily = wealth.resample("1D").last().pct_change(fill_method=None).dropna()
    return {
        "roi": float(wealth.iloc[-1] - 1.0),
        "terminal": float(wealth.iloc[-1]),
        "max_dd_abs": float(abs(dd.min())),
        "worst_day_abs": float(abs(daily.min())) if len(daily) else 0.0,
        "positive_days": float((daily > 0).mean()) if len(daily) else 0.0,
    }


def candidate_incremental_result(data, target: pd.DataFrame, state_mask: pd.Series, ex, guard, cost):
    masked = target.where(state_mask.reindex(target.index).fillna(False), 0.0)
    result = p1.run_targets(data, masked, ex, guard, cost, p1.NATIVE_GROSS_CAP)
    effective, _ = p5.effective_targets(masked, result, guard)
    return masked, result, effective


def incremental_router(data, core_targets, core_result, sleeve_targets, ex, guard, base_cost, direction, vol, train_start, train_end):
    masks = state_masks(data.close.index, direction, vol)
    core_effective, _ = p5.effective_targets(core_targets, core_result, guard)
    core_ret = core_result.equity.pct_change(fill_method=None).fillna(0.0)
    folds = p2.fold_bounds(data.close.index, train_start, train_end)

    routing: dict[str, list[dict]] = {}
    diagnostics: dict[str, list[dict]] = {}

    for state, menu in STATE_MENUS.items():
        rows = []
        for name in menu:
            _, result, effective = candidate_incremental_result(
                data, sleeve_targets[name], masks[state], ex, guard, base_cost
            )
            native_ret = result.equity.pct_change(fill_method=None).fillna(0.0)

            core_gross = core_effective.abs().sum(axis=1)
            desired_gross = effective.abs().sum(axis=1) * p1.HYBRID_ALPHA_SCALE
            headroom = (p1.GROSS_CAP - core_gross).clip(lower=0.0)
            use = (headroom / desired_gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
            # Headroom decision at close t applies to the return earned over t->t+1.
            exec_scale = (use * p1.HYBRID_ALPHA_SCALE).shift(1).fillna(0.0)
            combined_ret = core_ret.add(native_ret * exec_scale, fill_value=0.0)

            core_train = path_from_returns(core_ret, train_start, train_end)
            cand_train = path_from_returns(combined_ret, train_start, train_end)
            train_wealth_ratio = cand_train["terminal"] / max(core_train["terminal"], 1e-12)
            train_dd_ratio = cand_train["max_dd_abs"] / max(core_train["max_dd_abs"], 1e-12)

            fold_rows = []
            stable = 0
            for lo, hi in folds:
                c0 = path_from_returns(core_ret, lo, hi)
                c1 = path_from_returns(combined_ret, lo, hi)
                wr = c1["terminal"] / max(c0["terminal"], 1e-12)
                ddr = c1["max_dd_abs"] / max(c0["max_dd_abs"], 1e-12)
                good = wr > 1.0 and ddr <= MAX_DD_RATIO
                stable += int(good)
                fold_rows.append({"start": lo.isoformat(), "end": hi.isoformat(), "wealth_ratio": float(wr), "dd_ratio": float(ddr), "passed": bool(good)})

            eligible = bool(
                train_wealth_ratio >= MIN_TRAIN_WEALTH_RATIO
                and train_dd_ratio <= MAX_DD_RATIO
                and stable >= MIN_STABLE_FOLDS
            )
            score = float(np.log(max(train_wealth_ratio, 1e-12)) / max(train_dd_ratio, 0.5)) if eligible else -1e9
            rows.append({
                "sleeve": name,
                "eligible": eligible,
                "score": score,
                "train_wealth_ratio": float(train_wealth_ratio),
                "train_dd_ratio": float(train_dd_ratio),
                "stable_folds": int(stable),
                "folds": fold_rows,
                "mean_headroom_use_when_active": float(use[desired_gross.gt(1e-12)].mean()) if desired_gross.gt(1e-12).any() else 0.0,
            })

        rows.sort(key=lambda x: x["score"], reverse=True)
        chosen = next((x for x in rows if x["eligible"]), None)
        routing[state] = ([{"sleeve": chosen["sleeve"], "weight": 1.0}] if chosen else [])
        diagnostics[state] = rows
    return routing, diagnostics


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]), "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]), "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]), "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]), "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
    }


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)

    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}

    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, diagnostics = incremental_router(
        data, r98_targets, r98_result, sleeves, ex, guard, base_cost,
        direction, vol, train_start, train_end
    )

    native_targets = p1.route_native(sleeves, direction, vol, routing)
    native_result = p1.run_targets(data, native_targets, ex, guard, base_cost, p1.GROSS_CAP)
    core_effective, _ = p5.effective_targets(r98_targets, r98_result, guard)
    native_effective, _ = p5.effective_targets(native_targets, native_result, guard)
    combined_targets, _, headroom_diag = p5.combine_with_headroom(
        core_effective, native_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    result = p5.run_no_dd_guard(data, combined_targets, ex, base_cost, p1.GROSS_CAP)

    # F5 reference using the old standalone-alpha router.
    old_native_targets, old_routing, _ = p5.build_phase3_native(data, ex, guard, base_cost, direction, vol)
    old_native_result = p1.run_targets(data, old_native_targets, ex, guard, base_cost, p1.GROSS_CAP)
    old_native_effective, _ = p5.effective_targets(old_native_targets, old_native_result, guard)
    old_combined, _, _ = p5.combine_with_headroom(core_effective, old_native_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP)
    f5_result = p5.run_no_dd_guard(data, old_combined, ex, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for name, item in benchmarks.items()}
    bench_analyses = {name: audit.analyze_result(br, item["data"], direction, vol, common_start, common_end) for (name, br), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench_analyses.items()})

    full = {n: audit.analyze_result(r, data, direction, vol, common_start, common_end) for n, r in {
        "r98": r98_result, "f5_segregated": f5_result, "f6_incremental": result
    }.items()}
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold = {n: audit.analyze_result(r, data, direction, vol, hold_start, common_end) for n, r in {
        "r98": r98_result, "f5_segregated": f5_result, "f6_incremental": result
    }.items()}

    # Severe-cost validation with routing frozen from base training.
    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    native_sev = p1.run_targets(data, native_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    core_sev_effective, _ = p5.effective_targets(r98_sev_targets, r98_sev, guard)
    native_sev_effective, _ = p5.effective_targets(native_targets, native_sev, guard)
    combined_sev, _, severe_headroom = p5.combine_with_headroom(
        core_sev_effective, native_sev_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    result_sev = p5.run_no_dd_guard(data, combined_sev, ex, severe_cost, p1.GROSS_CAP)
    severe = {n: audit.analyze_result(r, data, direction, vol, common_start, common_end) for n, r in {
        "r98": r98_sev, "f6_incremental": result_sev
    }.items()}

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 6 — incremental alpha router on segregated core",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "selection_objective": "incremental wealth over R98 with <=5% DD deterioration in train folds",
            "min_train_wealth_ratio": MIN_TRAIN_WEALTH_RATIO,
            "max_dd_ratio": MAX_DD_RATIO,
            "min_stable_folds": MIN_STABLE_FOLDS,
            "one_sleeve_max_per_state": True,
            "no_grid_search": True,
            "segregated_risk_from_phase5": True,
        },
        "routing": routing,
        "routing_diagnostics": diagnostics,
        "old_phase3_routing": old_routing,
        "headroom": headroom_diag,
        "severe_headroom": severe_headroom,
        "base": {**full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": hold,
        "severe": severe,
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "disclosure": "Historical research/holdout only. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "routing": routing,
        "routing_diagnostics": diagnostics,
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "pass_counts": {n: passes(c) for n, c in cmp.items()},
    }, indent=2, default=audit.safe_float))


if __name__ == "__main__":
    main()
