from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase2_bear_native_alpha as p2
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r106_phase7_train_validated_bhv_short_veto as p7
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase9_train_marginal_pareto_router.json"
MIN_CELL_FOLD_HOURS = 24
MIN_PASS_FOLDS = 3


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


def pareto_pass(candidate: dict, core: dict) -> bool:
    c, b = candidate["global"], core["global"]
    return bool(
        float(c["roi"]) > float(b["roi"])
        and float(c["profit_factor"]) >= float(b["profit_factor"])
        and float(c["max_drawdown_abs"]) <= float(b["max_drawdown_abs"]) + 1e-12
        and float(c["worst_day_abs"]) <= float(b["worst_day_abs"]) + 1e-12
    )


def delta(a: dict, b: dict) -> dict:
    am, bm = a["global"], b["global"]
    return {
        "wealth_ratio": float((1.0 + am["roi"]) / max(1e-12, 1.0 + bm["roi"])),
        "roi_delta": float(am["roi"] - bm["roi"]),
        "dd_delta": float(am["max_drawdown_abs"] - bm["max_drawdown_abs"]),
        "worst_day_delta": float(am["worst_day_abs"] - bm["worst_day_abs"]),
        "pf_delta": float(am["profit_factor"] - bm["profit_factor"]),
        "win_rate_delta": float(am["trade_win_rate"] - bm["trade_win_rate"]),
        "positive_days_delta": float(am["positive_day_ratio"] - bm["positive_day_ratio"]),
        "payoff_delta": float(am["payoff_ratio"] - bm["payoff_ratio"]),
    }


def build_f7_core(data, raw, ex, guard, gross, cost, direction, vol):
    r98_targets, r98_result, r98_diag = p1.build_r98_targets(data, raw, ex, guard, gross, cost)
    bhv = p7.bhv_mask(data.close.index, direction, vol)
    long_targets = p7.isolated_side_targets(r98_targets, bhv, "long")
    short_targets = p7.isolated_side_targets(r98_targets, bhv, "short")
    long_res = p1.run_targets(data, long_targets, ex, guard, cost, p1.GROSS_CAP)
    short_res = p1.run_targets(data, short_targets, ex, guard, cost, p1.GROSS_CAP)
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    long_train = audit.analyze_result(long_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    short_train = audit.analyze_result(short_res, data, direction, vol, train_start, train_end)["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
    enable = bool(
        float(long_train.get("roi", 0.0)) > 0.0
        and float(long_train.get("profit_factor", 0.0)) > 1.0
        and float(short_train.get("roi", 0.0)) < 0.0
        and float(short_train.get("profit_factor", 0.0)) < 1.0
    )
    core_targets = p7.short_veto_targets(r98_targets, bhv) if enable else r98_targets.copy()
    core_result = p1.run_targets(data, core_targets, ex, guard, cost, p1.GROSS_CAP)
    return core_targets, core_result, {
        "short_veto_enabled": enable,
        "long_train": long_train,
        "short_train": short_train,
        "r98_diag": r98_diag,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])

    core_targets, core_result, core_diag = build_f7_core(data, raw, ex, guard, gross, base_cost, direction, vol)

    # Rebuild the phase-3 train-stable sleeve universe and routing. Phase 9 does not
    # accept those routes automatically; each cell must prove marginal Pareto value.
    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    sleeve_results = {n: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for n, t in sleeves.items()}
    routing, stability = p2.stability_router(sleeve_results, data, direction, vol, train_start, train_end)

    d = direction.shift(1).reindex(data.close.index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(data.close.index).fillna("UNKNOWN")
    state = d.astype(str) + "__" + v.astype(str)
    folds = p2.fold_bounds(data.close.index, train_start, train_end)

    core_train = audit.analyze_result(core_result, data, direction, vol, train_start, train_end)
    selected = []
    diagnostics = {}
    cell_targets = {}

    for key, items in routing.items():
        block = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
        if items:
            for item in items:
                block = block.add(sleeves[item["sleeve"]] * float(item["weight"]), fill_value=0.0)
            block = block.where(state.eq(key), 0.0)
        block = p1.cap(block, p1.NATIVE_GROSS_CAP)
        cell_targets[key] = block
        if not items or not block.abs().sum(axis=1).gt(1e-9).any():
            diagnostics[key] = {"routing": items, "eligible": False, "reason": "empty_cell"}
            continue

        candidate_targets = p1.cap(core_targets.add(block * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
        candidate_result = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)
        cand_train = audit.analyze_result(candidate_result, data, direction, vol, train_start, train_end)
        aggregate_pass = pareto_pass(cand_train, core_train)

        fold_rows = []
        pass_folds = 0
        eligible_folds = 0
        for lo, hi in folds:
            active = int(block.loc[lo:hi].abs().sum(axis=1).gt(1e-9).sum())
            if active < MIN_CELL_FOLD_HOURS:
                fold_rows.append({"start": lo.isoformat(), "end": hi.isoformat(), "active_hours": active, "eligible": False})
                continue
            eligible_folds += 1
            core_fold = audit.analyze_result(core_result, data, direction, vol, lo, hi)
            cand_fold = audit.analyze_result(candidate_result, data, direction, vol, lo, hi)
            passed = pareto_pass(cand_fold, core_fold)
            pass_folds += int(passed)
            fold_rows.append({
                "start": lo.isoformat(), "end": hi.isoformat(), "active_hours": active,
                "eligible": True, "passed": passed,
                "delta": delta(cand_fold, core_fold),
            })

        eligible = bool(aggregate_pass and eligible_folds >= MIN_PASS_FOLDS and pass_folds >= MIN_PASS_FOLDS)
        if eligible:
            selected.append(key)
        diagnostics[key] = {
            "routing": items,
            "eligible": eligible,
            "aggregate_train_pass": aggregate_pass,
            "aggregate_train_delta": delta(cand_train, core_train),
            "eligible_folds": eligible_folds,
            "pass_folds": pass_folds,
            "folds": fold_rows,
        }

    integrated_native = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
    for key in selected:
        integrated_native = integrated_native.add(cell_targets[key], fill_value=0.0)
    integrated_native = p1.cap(integrated_native, p1.NATIVE_GROSS_CAP)
    candidate_targets = p1.cap(core_targets.add(integrated_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    candidate_result = p1.run_targets(data, candidate_targets, ex, guard, base_cost, p1.GROSS_CAP)

    common_start, common_end = data.close.index[0], data.close.index[-1]
    hold_idx = data.close.index[data.close.index > p1.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    full = {
        "r98": audit.analyze_result(p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)[1], data, direction, vol, common_start, common_end),
        "f7_core": audit.analyze_result(core_result, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(candidate_result, data, direction, vol, common_start, common_end),
    }
    hold = {
        "r98": audit.analyze_result(p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)[1], data, direction, vol, hold_start, common_end),
        "f7_core": audit.analyze_result(core_result, data, direction, vol, hold_start, common_end),
        "candidate": audit.analyze_result(candidate_result, data, direction, vol, hold_start, common_end),
    }

    # Severe-cost candidate with train decisions frozen.
    r98_sev_targets, r98_sev_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    bhv = p7.bhv_mask(data.close.index, direction, vol)
    core_sev_targets = p7.short_veto_targets(r98_sev_targets, bhv) if core_diag["short_veto_enabled"] else r98_sev_targets.copy()
    core_sev_result = p1.run_targets(data, core_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    cand_sev_targets = p1.cap(core_sev_targets.add(integrated_native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
    cand_sev_result = p1.run_targets(data, cand_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev_result, data, direction, vol, common_start, common_end),
        "f7_core": audit.analyze_result(core_sev_result, data, direction, vol, common_start, common_end),
        "candidate": audit.analyze_result(cand_sev_result, data, direction, vol, common_start, common_end),
    }

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    bench_results = {n: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for n, item in benchmarks.items()}
    bench = {n: audit.analyze_result(res, item["data"], direction, vol, common_start, common_end) for (n, res), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench.items()})
    cmp = audit.candidate_vs_envelope(full["candidate"]["global"], env)

    def count_pass(c): return {"passed": sum(int(v["passed"]) for v in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 9 — train-only marginal Pareto router on F7 core",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "selection_contract": {
            "core": "R98 plus train-validated phase-7 BEAR+HIGH_VOL short veto",
            "cell_selection_uses_holdout": False,
            "aggregate_condition": "candidate wealth>core AND PF>=core AND DD<=core AND worst_day<=core",
            "fold_condition": "same strict Pareto rule; at least 3 eligible folds must pass",
            "native_scale": p1.HYBRID_ALPHA_SCALE,
            "no_grid_search": True,
        },
        "core_train_diagnostics": core_diag,
        "phase3_routing_source": routing,
        "phase3_stability_source": stability,
        "marginal_train_diagnostics": diagnostics,
        "selected_cells": selected,
        "base": full,
        "holdout": hold,
        "severe": severe,
        "delta_candidate_vs_f7": {
            "base": delta(full["candidate"], full["f7_core"]),
            "holdout": delta(hold["candidate"], hold["f7_core"]),
            "severe": delta(severe["candidate"], severe["f7_core"]),
        },
        "delta_candidate_vs_r98": {
            "base": delta(full["candidate"], full["r98"]),
            "holdout": delta(hold["candidate"], hold["r98"]),
            "severe": delta(severe["candidate"], severe["r98"]),
        },
        "vs_v13_v16_metric_envelope": cmp,
        "pass_count": count_pass(cmp),
        "regimes": {
            n: a["regimes"] for n, a in full.items()
        },
        "horizons": {
            "r98": p1.horizon_stats(p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)[1].equity, common_end),
            "f7_core": p1.horizon_stats(core_result.equity, common_end),
            "candidate": p1.horizon_stats(candidate_result.equity, common_end),
        },
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "disclosure": "Historical research with chronological holdout. Holdout never selects regime cells. No real orders.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "selected_cells": selected,
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "delta_candidate_vs_f7": out["delta_candidate_vs_f7"],
        "delta_candidate_vs_r98": out["delta_candidate_vs_r98"],
        "pass_count": out["pass_count"],
        "marginal_train_summary": {k: {kk: vv for kk, vv in v.items() if kk != "folds"} for k, v in diagnostics.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
