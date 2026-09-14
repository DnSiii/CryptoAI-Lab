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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase6_beta_neutralizer.json"


def build_phase3_native(data, ex, guard, base_cost, direction, vol):
    base = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeve_targets = {**base, "bear_dispersion": dispersion, "breakout": breakout}
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
    return native_targets, routing, stability


def beta_neutralize_shock(
    targets: pd.DataFrame,
    close: pd.DataFrame,
    direction: pd.Series,
    vol: pd.Series,
) -> tuple[pd.DataFrame, dict]:
    """Neutralize wrong-way net beta during confirmed high-vol shocks.

    The overlay is not a standalone alpha sleeve. It preserves the already
    aligned side and funds a BTC hedge only by reducing the opposing side.
    The exact replacement amount is net_exposure/2, which is the algebraic
    amount needed to move portfolio net exposure to zero when one unit of
    wrong-way gross is replaced by one unit of opposite BTC gross.

    No leverage or gross increase is allowed. Decisions use only completed
    prior data: prior regime labels and prior 12h BTC return.
    """
    out = targets.copy().astype(float)
    idx = out.index
    d = direction.shift(1).reindex(idx).fillna("UNKNOWN")
    v = vol.shift(1).reindex(idx).fillna("UNKNOWN")
    btc12 = close["BTCUSDT"].pct_change(12, fill_method=None).shift(1).reindex(idx)

    bear_shock = d.eq("BEAR") & v.eq("HIGH_VOLATILITY") & btc12.lt(0.0)
    bull_shock = d.eq("BULL") & v.eq("HIGH_VOLATILITY") & btc12.gt(0.0)

    before_gross = out.abs().sum(axis=1)
    before_net = out.sum(axis=1)
    bear_events = 0
    bull_events = 0
    bear_hedge_total = 0.0
    bull_hedge_total = 0.0

    for ts in out.index[bear_shock | bull_shock]:
        row = out.loc[ts].copy()
        long = row.clip(lower=0.0)
        short_abs = -row.clip(upper=0.0)
        lg = float(long.sum())
        sg = float(short_abs.sum())
        net = lg - sg

        if bool(bear_shock.loc[ts]) and net > 1e-12 and lg > 1e-12:
            # Replacing x long gross by x short gross changes net by -2x.
            x = min(net / 2.0, lg)
            long_scale = max((lg - x) / lg, 0.0)
            row = long * long_scale - short_abs
            row.loc["BTCUSDT"] = float(row.loc["BTCUSDT"]) - x
            out.loc[ts] = row
            bear_events += 1
            bear_hedge_total += x

        elif bool(bull_shock.loc[ts]) and net < -1e-12 and sg > 1e-12:
            x = min((-net) / 2.0, sg)
            short_scale = max((sg - x) / sg, 0.0)
            row = long - short_abs * short_scale
            row.loc["BTCUSDT"] = float(row.loc["BTCUSDT"]) + x
            out.loc[ts] = row
            bull_events += 1
            bull_hedge_total += x

    # Never allow the overlay to create more gross than the input row.
    after_gross = out.abs().sum(axis=1)
    gross_scale = before_gross.div(after_gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    out = out.mul(gross_scale, axis=0)
    out = p1.cap(out, p1.GROSS_CAP)

    after_net = out.sum(axis=1)
    active_bear = bear_shock & before_net.gt(0.0)
    active_bull = bull_shock & before_net.lt(0.0)
    diag = {
        "architecture": "exact_net_beta_neutralization_funded_by_wrong_way_side",
        "bear_condition": "prior BEAR + HIGH_VOL + prior BTC 12h return < 0 + portfolio net long",
        "bull_condition": "prior BULL + HIGH_VOL + prior BTC 12h return > 0 + portfolio net short",
        "hedge_asset": "BTCUSDT",
        "hedge_amount_formula": "abs(net_exposure)/2 because replacing x wrong-way gross with x opposite gross changes net by 2x",
        "parameter_fitted": False,
        "gross_increase_allowed": False,
        "aligned_side_preserved": True,
        "future_data": False,
        "bear_event_fraction": float(active_bear.mean()),
        "bull_event_fraction": float(active_bull.mean()),
        "bear_events": int(bear_events),
        "bull_events": int(bull_events),
        "mean_bear_hedge_gross": float(bear_hedge_total / bear_events) if bear_events else 0.0,
        "mean_bull_hedge_gross": float(bull_hedge_total / bull_events) if bull_events else 0.0,
        "mean_abs_net_before_active_bear": float(before_net.loc[active_bear].abs().mean()) if active_bear.any() else 0.0,
        "mean_abs_net_after_active_bear": float(after_net.loc[active_bear].abs().mean()) if active_bear.any() else 0.0,
        "mean_abs_net_before_active_bull": float(before_net.loc[active_bull].abs().mean()) if active_bull.any() else 0.0,
        "mean_abs_net_after_active_bull": float(after_net.loc[active_bull].abs().mean()) if active_bull.any() else 0.0,
        "max_gross_increase": float((out.abs().sum(axis=1) - before_gross).max()),
    }
    return out, diag


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
    native_targets, routing, stability = build_phase3_native(
        data, ex, guard, base_cost, direction, vol
    )
    f3_targets = p1.cap(
        r98_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f3_result = p1.run_targets(data, f3_targets, ex, guard, base_cost, p1.GROSS_CAP)

    neutralized_targets, hedge_diag = beta_neutralize_shock(
        f3_targets, data.close, direction, vol
    )
    phase6_result = p1.run_targets(
        data, neutralized_targets, ex, guard, base_cost, p1.GROSS_CAP
    )

    # Also isolate the same hedge on R98 alone to see if the overlay itself has
    # portfolio value independent of the F3 native alpha.
    r98_hedged_targets, r98_hedge_diag = beta_neutralize_shock(
        r98_targets, data.close, direction, vol
    )
    r98_hedged_result = p1.run_targets(
        data, r98_hedged_targets, ex, guard, base_cost, p1.GROSS_CAP
    )

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

    result_map = {
        "r98": r98_result,
        "f3_hybrid": f3_result,
        "r98_beta_hedged": r98_hedged_result,
        "phase6_hybrid": phase6_result,
    }
    full = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in result_map.items()
    }
    cmp = {n: audit.candidate_vs_envelope(a["global"], env) for n, a in full.items()}

    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end
    hold_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, hold_start, common_end)
        for (name, result), item in zip(bench_results.items(), benchmarks.values())
    }
    hold_env = audit.metric_envelope({n: a["global"] for n, a in hold_bench.items()})
    hold = {
        name: audit.analyze_result(result, data, direction, vol, hold_start, common_end)
        for name, result in result_map.items()
    }
    hold_cmp = {n: audit.candidate_vs_envelope(a["global"], hold_env) for n, a in hold.items()}

    # Severe costs: freeze the exact base-cost routing and hedge logic.
    r98_sev_targets, r98_sev_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, severe_cost)
    f3_sev_targets = p1.cap(
        r98_sev_targets.add(native_targets * p1.HYBRID_ALPHA_SCALE, fill_value=0.0),
        p1.GROSS_CAP,
    )
    f3_sev_result = p1.run_targets(data, f3_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP)
    r98_hedged_sev_targets, _ = beta_neutralize_shock(
        r98_sev_targets, data.close, direction, vol
    )
    phase6_sev_targets, _ = beta_neutralize_shock(
        f3_sev_targets, data.close, direction, vol
    )
    r98_hedged_sev_result = p1.run_targets(
        data, r98_hedged_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP
    )
    phase6_sev_result = p1.run_targets(
        data, phase6_sev_targets, ex, guard, severe_cost, p1.GROSS_CAP
    )
    severe_bench_results = {
        name: audit.exact_benchmark_result(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: audit.analyze_result(result, item["data"], direction, vol, common_start, common_end)
        for (name, result), item in zip(severe_bench_results.items(), benchmarks.values())
    }
    severe_env = audit.metric_envelope({n: a["global"] for n, a in severe_bench.items()})
    severe_map = {
        "r98": r98_sev_result,
        "f3_hybrid": f3_sev_result,
        "r98_beta_hedged": r98_hedged_sev_result,
        "phase6_hybrid": phase6_sev_result,
    }
    severe = {
        name: audit.analyze_result(result, data, direction, vol, common_start, common_end)
        for name, result in severe_map.items()
    }
    severe_cmp = {n: audit.candidate_vs_envelope(a["global"], severe_env) for n, a in severe.items()}

    out = {
        "study": "V99 R106 phase 6 — exact net-beta neutralization hedge",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "same_phase3_native_router": True,
            "same_hybrid_alpha_scale": p1.HYBRID_ALPHA_SCALE,
            "hedge_is_evaluated_by_portfolio_marginal_contribution_not_standalone_pf": True,
            "gross_increase": False,
            "phase6_hedge": hedge_diag,
            "r98_hedge": r98_hedge_diag,
        },
        "routing": routing,
        "stability_diagnostics": stability,
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "metadata": metadata,
        },
        "base": {"benchmark_envelope": env, **full, "vs_envelope": cmp, "pass_counts": {n: passes(c) for n, c in cmp.items()}},
        "holdout": {"benchmark_envelope": hold_env, **hold, "vs_envelope": hold_cmp, "pass_counts": {n: passes(c) for n, c in hold_cmp.items()}},
        "severe": {"benchmark_envelope": severe_env, **severe, "vs_envelope": severe_cmp, "pass_counts": {n: passes(c) for n, c in severe_cmp.items()}},
        "horizons": {
            name: p1.horizon_stats(result.equity, common_end)
            for name, result in result_map.items()
        },
        "promotion": {"r106_promoted": False, "reason": "phase 6 research gate pending evidence review"},
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
        "hedge": hedge_diag,
        "bear_high_vol": {
            n: a["regimes"]["matrix"]["BEAR__HIGH_VOLATILITY"]
            for n, a in full.items()
        },
        "bull_high_vol": {
            n: a["regimes"]["matrix"]["BULL__HIGH_VOLATILITY"]
            for n, a in full.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
