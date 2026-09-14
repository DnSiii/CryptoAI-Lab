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
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r106_phase5_segregated_sleeve_risk as p5
import run_v99_r106_phase6_incremental_alpha_router as p6
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase7_online_sleeve_confidence.json"
CONFIDENCE_HOURS = (168, 720, 2160)  # 7D / 30D / 90D
MIN_POSITIVE_HORIZONS = 2

OPTIONAL_BY_STATE = {
    "BULL__HIGH_VOLATILITY": "impulse",
    "BEAR__LOW_VOLATILITY": "breakout",
    "SIDEWAYS__HIGH_VOLATILITY": "impulse",
    "SIDEWAYS__LOW_VOLATILITY": "funding",
}


def state_series(index: pd.DatetimeIndex, direction: pd.Series, vol: pd.Series) -> pd.Series:
    d = direction.shift(1).reindex(index).fillna("UNKNOWN")
    v = vol.shift(1).reindex(index).fillna("UNKNOWN")
    return d.astype(str) + "__" + v.astype(str)


def confidence_gate(equity: pd.Series) -> tuple[pd.Series, dict]:
    eq = equity.astype(float).ffill().fillna(1.0)
    votes = pd.DataFrame(index=eq.index)
    for h in CONFIDENCE_HOURS:
        votes[str(h)] = eq.pct_change(int(h), fill_method=None).gt(0.0)
    gate = votes.sum(axis=1).ge(MIN_POSITIVE_HORIZONS)
    enough = pd.Series(False, index=eq.index)
    enough.iloc[max(CONFIDENCE_HOURS):] = True
    gate = gate & enough
    return gate.fillna(False), {
        "horizons_hours": list(CONFIDENCE_HOURS),
        "minimum_positive_horizons": MIN_POSITIVE_HORIZONS,
        "active_fraction": float(gate.mean()),
        "vote_positive_fraction": {c: float(votes[c].mean()) for c in votes},
    }


def build_online_native(data, sleeves, ex, guard, severe_cost, direction, vol, base_routing):
    idx = data.close.index
    state = state_series(idx, direction, vol)
    template = next(iter(sleeves.values()))
    out = pd.DataFrame(0.0, index=template.index, columns=template.columns)
    diagnostics = {}

    # Stable base alpha from F6 is always used exactly as selected in train.
    for key, items in base_routing.items():
        mask = state.eq(key)
        if not mask.any() or not items:
            continue
        block = pd.DataFrame(0.0, index=out.index, columns=out.columns)
        for item in items:
            block = block.add(sleeves[item["sleeve"]] * float(item["weight"]), fill_value=0.0)
        out.loc[mask, :] = block.loc[mask, :]

    # F5-only alphas are opportunistic. Their confidence is learned online from
    # a severe-cost shadow that trades only inside the state where the sleeve
    # would be allowed. This never sees future holdout information.
    for key, sleeve_name in OPTIONAL_BY_STATE.items():
        regime_mask = state.eq(key)
        shadow_target = sleeves[sleeve_name].where(regime_mask, 0.0)
        shadow_result = p1.run_targets(data, shadow_target, ex, guard, severe_cost, p1.NATIVE_GROSS_CAP)
        gate, diag = confidence_gate(shadow_result.equity)
        active = regime_mask & gate

        # If F6 already has a stable base in this state, blend 50/50 with the
        # opportunistic sleeve, matching F5's equal-weight architecture. If F6
        # has no base, the optional sleeve can occupy the state alone.
        has_base = bool(base_routing.get(key))
        if active.any():
            if has_base:
                current = out.loc[active].copy()
                out.loc[active] = current * 0.5 + sleeves[sleeve_name].loc[active] * 0.5
            else:
                out.loc[active] = sleeves[sleeve_name].loc[active]
        diagnostics[key] = {
            "sleeve": sleeve_name,
            "has_f6_base": has_base,
            "regime_fraction": float(regime_mask.mean()),
            "online_gate_fraction": float(gate.mean()),
            "effective_active_fraction": float(active.mean()),
            "confidence": diag,
        }
    return p1.cap(out, p1.NATIVE_GROSS_CAP), diagnostics


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
    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}

    # Recreate F6 routing using training only; this is the stable base layer.
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    f6_routing, f6_diag = p6.incremental_router(
        data, r98_targets, r98_result, sleeves, ex, guard, base_cost,
        direction, vol, train_start, train_end
    )

    online_native, online_diag = build_online_native(
        data, sleeves, ex, guard, severe_cost, direction, vol, f6_routing
    )
    online_native_result = p1.run_targets(data, online_native, ex, guard, base_cost, p1.GROSS_CAP)

    core_effective, _ = p5.effective_targets(r98_targets, r98_result, guard)
    online_effective, _ = p5.effective_targets(online_native, online_native_result, guard)
    combined, _, headroom_diag = p5.combine_with_headroom(
        core_effective, online_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    result = p5.run_no_dd_guard(data, combined, ex, base_cost, p1.GROSS_CAP)

    # References: F5 and F6 built with exactly the same data/cost.
    f5_native, f5_routing, _ = p5.build_phase3_native(data, ex, guard, base_cost, direction, vol)
    f5_native_res = p1.run_targets(data, f5_native, ex, guard, base_cost, p1.GROSS_CAP)
    f5_eff, _ = p5.effective_targets(f5_native, f5_native_res, guard)
    f5_comb, _, _ = p5.combine_with_headroom(core_effective, f5_eff, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP)
    f5_result = p5.run_no_dd_guard(data, f5_comb, ex, base_cost, p1.GROSS_CAP)

    f6_native = p1.route_native(sleeves, direction, vol, f6_routing)
    f6_native_res = p1.run_targets(data, f6_native, ex, guard, base_cost, p1.GROSS_CAP)
    f6_eff, _ = p5.effective_targets(f6_native, f6_native_res, guard)
    f6_comb, _, _ = p5.combine_with_headroom(core_effective, f6_eff, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP)
    f6_result = p5.run_no_dd_guard(data, f6_comb, ex, base_cost, p1.GROSS_CAP)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    bench_results = {name: audit.exact_benchmark_result(item, float(item["execution"]["base_cost_per_side"])) for name, item in benchmarks.items()}
    bench_analyses = {name: audit.analyze_result(br, item["data"], direction, vol, common_start, common_end) for (name, br), item in zip(bench_results.items(), benchmarks.values())}
    env = audit.metric_envelope({n: a["global"] for n, a in bench_analyses.items()})

    result_map = {"r98": r98_result, "f5": f5_result, "f6": f6_result, "f7_online": result}
    full = {n: audit.analyze_result(r, data, direction, vol, common_start, common_end) for n, r in result_map.items()}
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold = {n: audit.analyze_result(r, data, direction, vol, hold_start, common_end) for n, r in result_map.items()}

    # Severe-cost actual execution; online confidence shadows are already severe
    # and therefore unchanged. R98/native breaker states are recomputed at severe cost.
    r98_sev_targets, r98_sev, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    online_native_sev_res = p1.run_targets(data, online_native, ex, guard, severe_cost, p1.GROSS_CAP)
    core_sev_eff, _ = p5.effective_targets(r98_sev_targets, r98_sev, guard)
    online_sev_eff, _ = p5.effective_targets(online_native, online_native_sev_res, guard)
    sev_comb, _, severe_headroom = p5.combine_with_headroom(
        core_sev_eff, online_sev_eff, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    sev_result = p5.run_no_dd_guard(data, sev_comb, ex, severe_cost, p1.GROSS_CAP)
    severe = {
        "r98": audit.analyze_result(r98_sev, data, direction, vol, common_start, common_end),
        "f7_online": audit.analyze_result(sev_result, data, direction, vol, common_start, common_end),
    }

    def passes(c):
        return {"passed": sum(int(x["passed"]) for x in c.values()), "total": len(c)}

    out = {
        "study": "V99 R106 phase 7 — online confidence over segregated incremental router",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "f6_stable_base_preserved": True,
            "optional_f5_alphas": OPTIONAL_BY_STATE,
            "confidence_horizons_hours": list(CONFIDENCE_HOURS),
            "minimum_positive_horizons": MIN_POSITIVE_HORIZONS,
            "shadow_cost": "severe_cost_per_side",
            "no_holdout_fit": True,
            "no_grid_search": True,
            "segregated_risk_architecture": True,
        },
        "f6_routing": f6_routing,
        "f6_diagnostics": f6_diag,
        "online_diagnostics": online_diag,
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
        "f6_routing": f6_routing,
        "online_diagnostics": online_diag,
        "base": {n: compact(a) for n, a in full.items()},
        "holdout": {n: compact(a) for n, a in hold.items()},
        "severe": {n: compact(a) for n, a in severe.items()},
        "pass_counts": {n: passes(c) for n, c in cmp.items()},
    }, indent=2, default=audit.safe_float))


if __name__ == "__main__":
    main()
