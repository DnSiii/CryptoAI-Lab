from __future__ import annotations

import gc
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import FuturesData, point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from paper_once_v13 import apply_funding_quarantine, cap_targets
from paper_once_v15 import build_v15
from paper_once_v16 import build_v16
from run_final_candidate import build_candidate
from run_v99_r25_trisleeve_meta import cap, run, sdata, stats

REPORT = PROJECT / "reports" / "candidate_v99_r35_surgical_envelope.json"
HORIZONS = (7, 30, 90, 180, 365)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def metric_margin(value: float, floor: float = 0.01) -> float:
    return max(floor, abs(value) * 0.05)


def build_v13_benchmark():
    finalist = load_json(PROJECT / "config" / "candidate_v13_circuit_breaker.json")
    base = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    data, targets, _, _ = build_candidate(base)
    targets = cap_targets(targets, finalist["target_cap"])
    data, targets, _ = apply_funding_quarantine(data, targets)
    execution = base["execution"]
    guard = finalist["circuit_breaker"]
    kwargs = {
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": finalist["gross_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    return finalist, data, targets, execution, kwargs


def build_v14_benchmark():
    candidate = load_json(PROJECT / "config" / "candidate_v14_max_capture.json")
    finalist = load_json(PROJECT / "config" / candidate["frozen_core_config"])
    base = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    data, core_targets, _, _ = build_candidate(base)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    universe = base["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    raw = build_targets(signal_data, StrategySpec(**candidate["opportunity"]["spec"]))
    alloc = candidate["allocation"]
    targets, _ = additive_opportunity_targets(
        core_targets,
        raw,
        OpportunityBudget(alloc["maximum_overlay_gross"], alloc["maximum_portfolio_gross"]),
    )
    data, targets, _ = apply_funding_quarantine(data, targets)
    execution = base["execution"]
    guard = candidate["circuit_breaker"]
    kwargs = {
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": alloc["gross_drift_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    return candidate, data, targets, execution, kwargs


def build_v16_benchmark():
    candidate = load_json(PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json")
    data, targets, _, _, _ = build_v16(candidate)
    finalist = load_json(PROJECT / "config" / candidate["frozen_core_config"])
    base = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    execution = base["execution"]
    guard = candidate["circuit_breaker"]
    kwargs = {
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": guard["gross_drift_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    return candidate, data, targets, execution, kwargs


def exact_benchmark(item: dict, cost: float, start=None, end=None):
    data = item["data"]
    targets = item["targets"]
    if start is not None:
        data = FuturesData(
            frames={k: v.loc[start:end].copy() for k, v in data.frames.items()},
            funding=data.funding.loc[start:end].copy(),
            symbols=data.symbols,
        )
        targets = targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    result = exact_fast(data, targets, cost_per_side=cost, **item["kwargs"])
    return stats(result.equity)


def directional_features(raw: pd.DataFrame, close: pd.DataFrame):
    gross = raw.abs().sum(axis=1).replace(0.0, np.nan)
    share = raw.abs().div(gross, axis=0).fillna(0.0)
    sign = np.sign(raw)
    signed24 = sign * close.pct_change(24, fill_method=None)
    signed72 = sign * close.pct_change(72, fill_method=None)
    return share, signed24, signed72


def concentrated_adverse(raw: pd.DataFrame, close: pd.DataFrame, p: dict):
    share, signed24, signed72 = directional_features(raw, close)
    bad = (share >= p["share_trigger"]) & (
        (signed24 <= -p["adverse24"]) | (signed72 <= -p["adverse72"])
    )
    if p["cut_cooldown"] > 1:
        bad = bad.astype(float).rolling(p["cut_cooldown"], min_periods=1).max().gt(0)
    factor = pd.DataFrame(1.0, index=raw.index, columns=raw.columns).mask(bad, p["cut_scale"])
    cut = raw * factor * p["gross_multiplier"]
    return cap(cut, p["gross_cap"]), bad


def stress_mask(shadow: pd.Series, btc: pd.Series, p: dict):
    dd = shadow / shadow.cummax() - 1.0
    threshold = -abs(p["dd_trigger"])
    cross = (dd <= threshold) & (dd.shift(1).fillna(0.0) > threshold)
    r24 = btc.pct_change(24, fill_method=None)
    r72 = btc.pct_change(72, fill_method=None)
    if p["market_level"] == 2:
        shock = (r24 <= -0.035) | (r72 <= -0.07)
    else:
        shock = (r24 <= -0.045) | (r72 <= -0.09)
    raw = (cross | shock.fillna(False)).astype(float)
    return raw.rolling(p["hedge_cooldown"], min_periods=1).max().gt(0)


def surgical_targets(raw: pd.DataFrame, shadow: pd.Series, close: pd.DataFrame, p: dict):
    targets, bad = concentrated_adverse(raw, close, p)
    portfolio_bad = bad.any(axis=1)
    stress = stress_mask(shadow, close["BTCUSDT"], p)
    active = portfolio_bad & stress
    net = targets.sum(axis=1)
    direction = -np.sign(net).where(net.abs() >= p["min_net"], 0.0)
    out = targets.copy()
    if "BTCUSDT" not in out.columns:
        raise RuntimeError("BTCUSDT missing from V15 universe")
    out["BTCUSDT"] = out["BTCUSDT"] + active.astype(float) * direction * p["hedge_size"]
    return cap(out, p["gross_cap"]), bad, active


def exact_candidate(data, raw, ex, guard, base_gross, cost, p):
    shadow = run(data, raw, ex, cost, base_gross, guard).equity
    targets, bad, active = surgical_targets(raw, shadow, data.close, p)
    equity = run(data, targets, ex, cost, p["gross_cap"], guard).equity
    return equity, shadow, bad, active


def candidate_slice(data, raw, ex, guard, base_gross, cost, p, start, end):
    d = sdata(data, start, end)
    r = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    equity, shadow, _, _ = exact_candidate(d, r, ex, guard, base_gross, cost, p)
    return stats(equity), stats(shadow)


def envelope(benchmark_rows: dict[str, dict]) -> dict:
    return {
        "return": max(x["return"] for x in benchmark_rows.values()),
        "max_drawdown_abs": min(abs(x["max_drawdown"]) for x in benchmark_rows.values()),
        "worst_day_abs": min(abs(x["worst_day"]) for x in benchmark_rows.values()),
        "best_return_engine": max(benchmark_rows, key=lambda k: benchmark_rows[k]["return"]),
        "best_drawdown_engine": min(benchmark_rows, key=lambda k: abs(benchmark_rows[k]["max_drawdown"])),
        "best_worst_day_engine": min(benchmark_rows, key=lambda k: abs(benchmark_rows[k]["worst_day"])),
    }


def main():
    cand, data, raw, _, _, quarantined, metadata = build_v15()
    v14_parent = load_json(PROJECT / "config" / cand["parent_candidate_config"])
    finalist = load_json(PROJECT / "config" / v14_parent["frozen_core_config"])
    base = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    ex = base["execution"]
    guard = v14_parent["circuit_breaker"]
    base_gross = float(v14_parent["allocation"]["gross_drift_guard_cap"])
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    v15_equity = run(data, raw, ex, base_cost, base_gross, guard).equity
    v15_severe_equity = run(data, raw, ex, severe_cost, base_gross, guard).equity
    v15 = stats(v15_equity)
    v15_severe = stats(v15_severe_equity)
    base_screen = stats(screen(data, raw, cost_per_side=base_cost).equity)

    v13_c, v13_d, v13_t, v13_ex, v13_kw = build_v13_benchmark()
    v14_c, v14_d, v14_t, v14_ex, v14_kw = build_v14_benchmark()
    v16_c, v16_d, v16_t, v16_ex, v16_kw = build_v16_benchmark()
    benchmarks = {
        "v13": {"candidate": v13_c, "data": v13_d, "targets": v13_t, "execution": v13_ex, "kwargs": v13_kw},
        "v14": {"candidate": v14_c, "data": v14_d, "targets": v14_t, "execution": v14_ex, "kwargs": v14_kw},
        "v15": {"candidate": cand, "data": data, "targets": raw, "execution": ex, "kwargs": {
            "maintenance_equity_fraction": ex["maintenance_equity_fraction"],
            "gross_guard_cap": base_gross,
            "drawdown_guard_threshold": guard["drawdown_threshold"],
            "drawdown_guard_multiplier": guard["exposure_multiplier"],
            "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
        }},
        "v16": {"candidate": v16_c, "data": v16_d, "targets": v16_t, "execution": v16_ex, "kwargs": v16_kw},
    }

    full_bench = {}
    severe_bench = {}
    for name, item in benchmarks.items():
        cost = float(item["execution"]["base_cost_per_side"])
        severe = float(item["execution"]["severe_cost_per_side"])
        full_bench[name] = exact_benchmark(item, cost)
        severe_bench[name] = exact_benchmark(item, severe)
    full_env = envelope(full_bench)
    severe_env = envelope(severe_bench)

    rows = []
    grid = itertools.product(
        (0.55, 0.65),
        ((0.02, 0.04), (0.03, 0.06)),
        (0.25, 0.50),
        (6, 12),
        (0.08, 0.10),
        (2, 3),
        (0.15, 0.25),
        (24, 48),
        (1.00, 1.05),
    )
    shadow_screen = screen(data, raw, cost_per_side=base_cost).equity
    for i, (share, adverse, cut, cut_cd, dd, market, hedge, hedge_cd, gm) in enumerate(grid, 1):
        p = {
            "share_trigger": share,
            "adverse24": adverse[0],
            "adverse72": adverse[1],
            "cut_scale": cut,
            "cut_cooldown": cut_cd,
            "dd_trigger": dd,
            "market_level": market,
            "hedge_size": hedge,
            "hedge_cooldown": hedge_cd,
            "min_net": 0.10,
            "gross_multiplier": gm,
            "gross_cap": 1.90,
        }
        targets, bad, active = surgical_targets(raw, shadow_screen, data.close, p)
        s = stats(screen(data, targets, cost_per_side=base_cost).equity)
        wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + base_screen["return"])
        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, abs(base_screen["max_drawdown"]))
        worst_ratio = abs(s["worst_day"]) / max(1e-12, abs(base_screen["worst_day"]))
        score = (
            5.0 * np.log(max(wealth, 1e-12))
            + 7.0 * max(0.0, 1.0 - dd_ratio)
            - 9.0 * max(0.0, dd_ratio - 1.0)
            - 5.0 * max(0.0, worst_ratio - 1.0)
            - 0.5 * float(active.mean())
        )
        rows.append({
            "params": p,
            "screen": s,
            "screen_wealth_ratio": float(wealth),
            "screen_drawdown_ratio": float(dd_ratio),
            "screen_worst_day_ratio": float(worst_ratio),
            "concentrated_adverse_fraction": float(bad.to_numpy(dtype=float).mean()),
            "hedge_active_fraction": float(active.mean()),
            "screen_score": float(score),
        })
        del targets, bad, active
        if i % 32 == 0:
            gc.collect()

    rows.sort(key=lambda z: z["screen_score"], reverse=True)
    split = int(len(v15_equity) * 0.60)
    hold_start = v15_equity.index[min(split + 1, len(v15_equity) - 1)]
    v15_hold = stats(v15_equity.loc[hold_start:])
    exact_rows = []
    for row in rows[:40]:
        p = row["params"]
        eq, _, bad, active = exact_candidate(data, raw, ex, guard, base_gross, base_cost, p)
        s = stats(eq)
        hold = stats(eq.loc[hold_start:])
        wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + v15["return"])
        hold_wealth = (1.0 + hold["return"]) / max(1e-12, 1.0 + v15_hold["return"])
        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_ratio = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        score = (
            6.0 * np.log(max(wealth, 1e-12))
            + 4.0 * np.log(max(hold_wealth, 1e-12))
            + 8.0 * max(0.0, 1.0 - dd_ratio)
            - 12.0 * max(0.0, dd_ratio - 1.0)
            - 7.0 * max(0.0, worst_ratio - 1.0)
        )
        exact_rows.append({
            **row,
            "summary": s,
            "holdout": hold,
            "wealth_ratio_to_v15": float(wealth),
            "holdout_wealth_ratio_to_v15": float(hold_wealth),
            "drawdown_ratio_to_full_envelope": float(dd_ratio),
            "worst_day_ratio_to_full_envelope": float(worst_ratio),
            "exact_hedge_active_fraction": float(active.mean()),
            "exact_score": float(score),
        })
        del eq, bad, active
        gc.collect()

    exact_rows.sort(key=lambda z: z["exact_score"], reverse=True)
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    finalists = []
    for row in exact_rows[:10]:
        p = row["params"]
        isolated = {}
        isolated_benchmarks = {}
        envelope_rows = {}
        envelope_wins = {}
        material_wins = {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            candidate_stats, _ = candidate_slice(data, raw, ex, guard, base_gross, base_cost, p, start, common_end)
            bench_rows = {}
            for name, item in benchmarks.items():
                bench_rows[name] = exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
            env = envelope(bench_rows)
            k = str(days)
            isolated[k] = candidate_stats
            isolated_benchmarks[k] = bench_rows
            envelope_rows[k] = env
            envelope_wins[k] = {
                "return": candidate_stats["return"] >= env["return"],
                "drawdown": abs(candidate_stats["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(candidate_stats["worst_day"]) <= env["worst_day_abs"],
            }
            material_wins[k] = {
                "return": candidate_stats["return"] >= env["return"] + metric_margin(env["return"]),
                "drawdown": abs(candidate_stats["max_drawdown"]) <= env["max_drawdown_abs"] * 0.95,
                "worst_day": abs(candidate_stats["worst_day"]) <= env["worst_day_abs"] * 0.95,
            }

        sev_eq, _, _, sev_active = exact_candidate(data, raw, ex, guard, base_gross, severe_cost, p)
        sev = stats(sev_eq)
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_risk_pass = (
            abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
            and abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        )
        all_envelope = all(all(v.values()) for v in envelope_wins.values())
        all_material = all(all(v.values()) for v in material_wins.values())
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_risk_pass = (
            abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
            and abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        )
        dominant_gate = bool(
            all_material
            and full_return_pass
            and full_risk_pass
            and row["holdout_wealth_ratio_to_v15"] >= 1.10
            and severe_return_pass
            and severe_risk_pass
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_benchmarks": isolated_benchmarks,
            "isolated_envelope": envelope_rows,
            "envelope_wins": envelope_wins,
            "material_envelope_wins": material_wins,
            "all_envelope_dimensions_won": all_envelope,
            "all_material_envelope_dimensions_won": all_material,
            "severe_cost": sev,
            "severe_envelope": severe_env,
            "severe_return_pass": severe_return_pass,
            "severe_risk_pass": severe_risk_pass,
            "full_return_pass": full_return_pass,
            "full_risk_pass": full_risk_pass,
            "severe_hedge_active_fraction": float(sev_active.mean()),
            "dominant_gate_passed": dominant_gate,
        })
        del sev_eq, sev_active
        gc.collect()

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["all_material_envelope_dimensions_won"],
            z["all_envelope_dimensions_won"],
            sum(sum(x.values()) for x in z["material_envelope_wins"].values()),
            sum(sum(x.values()) for x in z["envelope_wins"].values()),
            z["holdout_wealth_ratio_to_v15"],
            z["wealth_ratio_to_v15"],
            -z["drawdown_ratio_to_full_envelope"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None
    out = {
        "study": "V99 R35 surgical dual-brake benchmark envelope",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "preserve the aggressive V15 core, cut only concentrated positions moving materially against their requested direction, and add a small opposite-net BTC hedge only when that concentrated adverse condition overlaps independent portfolio/market stress",
        "benchmark_policy": "candidate must beat the best return and the best downside metric available across V13/V14/V15/V16 for each isolated horizon; dominant gate also requires a material margin, holdout strength, full-history envelope dominance and severe-cost envelope dominance",
        "material_margin": {"return": "best benchmark + max(1 percentage point, 5% of benchmark return)", "drawdown_abs": "at least 5% lower than best benchmark", "worst_day_abs": "at least 5% lower than best benchmark"},
        "grid_size": len(rows),
        "exact_screen_size": len(exact_rows),
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "top_exact": exact_rows[:25],
        "top_screen": rows[:50],
        "disclosure": "Historical research only. All directional, concentration, drawdown and market-shock inputs are causal. Candidate orders are evaluated on the next-open replay. Isolated candidate replays reset execution/equity state and intentionally do not borrow prior P&L. No real-order path is enabled. A historical winner still requires frozen forward paper.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "grid_size": len(rows), "full_envelope": full_env, "severe_envelope": severe_env, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    main()
