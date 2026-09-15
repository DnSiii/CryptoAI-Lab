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
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase6_marginal_state_attribution.json"


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "payoff": float(m["payoff_ratio"]),
    }


def compare(a: dict, b: dict) -> dict:
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


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)

    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    sleeve_results = {n: p1.run_targets(data, t, ex, guard, base_cost, p1.NATIVE_GROSS_CAP) for n, t in sleeves.items()}
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, stability = p2.stability_router(sleeve_results, data, direction, vol, train_start, train_end)

    d = direction.shift(1).reindex(data.close.index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(data.close.index).fillna("UNKNOWN")
    state = d.astype(str) + "__" + v.astype(str)

    state_targets = {}
    for key, items in routing.items():
        block = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
        if items:
            for item in items:
                block = block.add(sleeves[item["sleeve"]] * float(item["weight"]), fill_value=0.0)
            block = block.where(state.eq(key), 0.0)
        state_targets[key] = p1.cap(block, p1.NATIVE_GROSS_CAP)

    common_start = data.close.index[0]
    common_end = data.close.index[-1]
    hold_idx = data.close.index[data.close.index > p1.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    base_analysis = audit.analyze_result(r98_result, data, direction, vol, common_start, common_end)
    hold_base = audit.analyze_result(r98_result, data, direction, vol, hold_start, common_end)

    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    severe_base = audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end)

    rows = {}
    for key, native in state_targets.items():
        if not routing.get(key):
            rows[key] = {"routing": [], "active_fraction": 0.0}
            continue
        target = p1.cap(r98_targets.add(native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
        result = p1.run_targets(data, target, ex, guard, base_cost, p1.GROSS_CAP)
        full = audit.analyze_result(result, data, direction, vol, common_start, common_end)
        hold = audit.analyze_result(result, data, direction, vol, hold_start, common_end)
        sev_target = p1.cap(r98_sev_targets.add(native * p1.HYBRID_ALPHA_SCALE, fill_value=0.0), p1.GROSS_CAP)
        sev_result = p1.run_targets(data, sev_target, ex, guard, severe_cost, p1.GROSS_CAP)
        sev = audit.analyze_result(sev_result, data, direction, vol, common_start, common_end)
        rows[key] = {
            "routing": routing[key],
            "active_fraction": float(native.abs().sum(axis=1).gt(1e-9).mean()),
            "base": full,
            "holdout": hold,
            "severe": sev,
            "delta_base_vs_r98": compare(full, base_analysis),
            "delta_holdout_vs_r98": compare(hold, hold_base),
            "delta_severe_vs_r98": compare(sev, severe_base),
        }

    out = {
        "study": "V99 R106 phase 6 diagnostic — marginal regime-cell attribution over R98",
        "status": "DIAGNOSTIC_ONLY_NO_ROUTER_REFIT",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "routing_frozen_from_phase3_train": routing,
        "phase3_stability": stability,
        "r98": {"base": base_analysis, "holdout": hold_base, "severe": severe_base},
        "cells": rows,
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "holdout_start": hold_start.isoformat(), "quarantined_symbols": quarantined, "metadata": metadata},
        "interpretation_contract": {
            "purpose": "identify alpha redundancy: standalone-stable sleeves can still be marginally harmful when added to R98",
            "no_parameter_selection": True,
            "holdout_is_diagnostic_not_used_to_refit_phase3": True,
        },
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "r98": {"base": compact(base_analysis), "holdout": compact(hold_base), "severe": compact(severe_base)},
        "cells": {
            k: ({"routing": v.get("routing", []), "active_fraction": v.get("active_fraction", 0.0)} if not v.get("routing") else {
                "routing": v["routing"], "active_fraction": v["active_fraction"],
                "base": compact(v["base"]), "holdout": compact(v["holdout"]), "severe": compact(v["severe"]),
                "delta_base_vs_r98": v["delta_base_vs_r98"],
                "delta_holdout_vs_r98": v["delta_holdout_vs_r98"],
                "delta_severe_vs_r98": v["delta_severe_vs_r98"],
            }) for k, v in rows.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
