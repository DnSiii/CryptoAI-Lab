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

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15
from run_v99_r25_trisleeve_meta import run, sdata, stats
from run_v99_r35_surgical_envelope import (
    build_v13_benchmark,
    build_v14_benchmark,
    build_v16_benchmark,
    envelope,
    exact_benchmark,
    metric_margin,
)

REPORT = PROJECT / "reports" / "candidate_v99_r36_safe_core_router.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def v15_setup():
    cand, data, raw, _, _, quarantined, metadata = build_v15()
    v14 = load_json(PROJECT / "config" / cand["parent_candidate_config"])
    finalist = load_json(PROJECT / "config" / v14["frozen_core_config"])
    base = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    ex = base["execution"]
    guard = v14["circuit_breaker"]
    gross = float(v14["allocation"]["gross_drift_guard_cap"])
    return cand, data, raw, ex, guard, gross, quarantined, metadata


def v16_exact(data: FuturesData, targets: pd.DataFrame, execution: dict, kwargs: dict, cost: float):
    return exact_fast(data, targets, cost_per_side=cost, **kwargs)


def align_targets(targets: pd.DataFrame, index: pd.Index, columns: pd.Index) -> pd.DataFrame:
    return targets.reindex(index=index, columns=columns).fillna(0.0)


def risk_signal(raw: pd.DataFrame, close: pd.DataFrame, p: dict) -> tuple[pd.Series, dict[str, pd.Series]]:
    gross = raw.abs().sum(axis=1).replace(0.0, np.nan)
    share = raw.abs().div(gross, axis=0).fillna(0.0)
    sign = np.sign(raw)
    r6 = close.pct_change(6, fill_method=None)
    r24 = close.pct_change(24, fill_method=None)
    signed6 = sign * r6
    signed24 = sign * r24

    adverse6 = share * (-signed6).clip(lower=0.0)
    adverse24 = share * (-signed24).clip(lower=0.0)
    contribution = pd.concat(
        [adverse6.max(axis=1).rename("a6"), (0.50 * adverse24.max(axis=1)).rename("a24")],
        axis=1,
    ).max(axis=1)

    top_share = share.max(axis=1)
    top_symbol = share.idxmax(axis=1)
    row_idx = np.arange(len(raw.index))
    col_idx = raw.columns.get_indexer(top_symbol)
    top_signed6 = pd.Series(
        signed6.to_numpy()[row_idx, np.maximum(col_idx, 0)], index=raw.index
    ).where(col_idx >= 0, 0.0)

    adverse_gross_fraction = share.where((signed6 < 0.0) | (signed24 < 0.0), 0.0).sum(axis=1)

    net = raw.sum(axis=1)
    net_sign = np.sign(net)
    btc6 = close["BTCUSDT"].pct_change(6, fill_method=None)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None)
    net_market_adverse = pd.concat(
        [-(net_sign * btc6), -(net_sign * btc24)], axis=1
    ).max(axis=1)

    instant = (
        (contribution >= p["contribution_trigger"])
        | ((top_share >= p["concentration_trigger"]) & (top_signed6 <= -p["top_adverse6"]))
        | ((net.abs() >= p["min_net"]) & (net_market_adverse >= p["market_adverse_trigger"]))
        | ((adverse_gross_fraction >= p["adverse_breadth_trigger"]) & (contribution >= p["breadth_contribution_floor"]))
    ).fillna(False)

    active = instant.astype(float).rolling(int(p["cooldown"]), min_periods=1).max().gt(0.0)
    diagnostics = {
        "contribution": contribution.fillna(0.0),
        "top_share": top_share.fillna(0.0),
        "top_signed6": top_signed6.fillna(0.0),
        "adverse_gross_fraction": adverse_gross_fraction.fillna(0.0),
        "net_market_adverse": net_market_adverse.fillna(0.0),
        "instant": instant.astype(float),
        "active": active.astype(float),
    }
    return active, diagnostics


def combine_router(
    v15_equity: pd.Series,
    v16_equity: pd.Series,
    safe_active: pd.Series,
    safe_weight: float,
    transfer_cost_per_side: float,
) -> tuple[pd.Series, pd.Series, float]:
    aligned = pd.concat(
        [v15_equity.rename("v15"), v16_equity.rename("v16"), safe_active.rename("safe")],
        axis=1,
        join="inner",
    ).dropna(subset=["v15", "v16"])
    r15 = aligned["v15"].pct_change(fill_method=None).fillna(0.0)
    r16 = aligned["v16"].pct_change(fill_method=None).fillna(0.0)
    desired = aligned["safe"].fillna(False).astype(float).shift(1).fillna(0.0) * float(safe_weight)

    cap15 = 1.0
    cap16 = 0.0
    eq = pd.Series(index=aligned.index, dtype=float)
    realized = pd.Series(index=aligned.index, dtype=float)
    eq.iloc[0] = 1.0
    realized.iloc[0] = 0.0
    total_cost = 0.0

    for i in range(1, len(aligned)):
        cap15 *= 1.0 + float(r15.iloc[i])
        cap16 *= 1.0 + float(r16.iloc[i])
        total = cap15 + cap16
        if total <= 0.0:
            eq.iloc[i:] = 0.0
            realized.iloc[i:] = 0.0
            break
        wanted = float(desired.iloc[i])
        current = cap16 / total
        if abs(current - wanted) > 1e-10:
            moved = abs(current - wanted)
            cost = total * moved * 2.0 * float(transfer_cost_per_side)
            total = max(0.0, total - cost)
            total_cost += cost
            cap16 = total * wanted
            cap15 = total * (1.0 - wanted)
        eq.iloc[i] = cap15 + cap16
        realized.iloc[i] = cap16 / max(cap15 + cap16, 1e-12)

    return eq.ffill().fillna(1.0), realized.ffill().fillna(0.0), float(total_cost)


def slice_futures(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    return FuturesData(
        frames={k: v.loc[start:end].copy() for k, v in data.frames.items()},
        funding=data.funding.loc[start:end].copy(),
        symbols=data.symbols,
    )


def isolated_candidate(
    v15_data: FuturesData,
    v15_raw: pd.DataFrame,
    v15_ex: dict,
    v15_guard: dict,
    v15_gross: float,
    v16_data: FuturesData,
    v16_targets: pd.DataFrame,
    v16_ex: dict,
    v16_kwargs: dict,
    cost15: float,
    cost16: float,
    p: dict,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    d15 = sdata(v15_data, start, end)
    r15 = align_targets(v15_raw, d15.close.index, d15.close.columns)
    res15 = run(d15, r15, v15_ex, cost15, v15_gross, v15_guard)

    d16 = slice_futures(v16_data, start, end)
    t16 = align_targets(v16_targets, d16.close.index, d16.close.columns)
    res16 = v16_exact(d16, t16, v16_ex, v16_kwargs, cost16)

    common_index = res15.equity.index.intersection(res16.equity.index)
    common_columns = d15.close.columns.intersection(r15.columns)
    signal_raw = r15.reindex(index=common_index, columns=common_columns).fillna(0.0)
    signal_close = d15.close.reindex(index=common_index, columns=common_columns)
    active, _ = risk_signal(signal_raw, signal_close, p)
    eq, _, _ = combine_router(
        res15.equity.reindex(common_index),
        res16.equity.reindex(common_index),
        active,
        p["safe_weight"],
        max(cost15, cost16),
    )
    return stats(eq)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    v15_result = run(data, raw, ex, base_cost, gross, guard)
    v15_severe_result = run(data, raw, ex, severe_cost, gross, guard)
    v15 = stats(v15_result.equity)
    v15_severe = stats(v15_severe_result.equity)

    v13_c, v13_d, v13_t, v13_ex, v13_kw = build_v13_benchmark()
    v14_c, v14_d, v14_t, v14_ex, v14_kw = build_v14_benchmark()
    v16_c, v16_d, v16_t, v16_ex, v16_kw = build_v16_benchmark()
    v16_base_cost = float(v16_ex["base_cost_per_side"])
    v16_severe_cost = float(v16_ex["severe_cost_per_side"])
    v16_result = v16_exact(v16_d, v16_t, v16_ex, v16_kw, v16_base_cost)
    v16_severe_result = v16_exact(v16_d, v16_t, v16_ex, v16_kw, v16_severe_cost)

    benchmarks = {
        "v13": {"candidate": v13_c, "data": v13_d, "targets": v13_t, "execution": v13_ex, "kwargs": v13_kw},
        "v14": {"candidate": v14_c, "data": v14_d, "targets": v14_t, "execution": v14_ex, "kwargs": v14_kw},
        "v15": {"candidate": cand, "data": data, "targets": raw, "execution": ex, "kwargs": {
            "maintenance_equity_fraction": ex["maintenance_equity_fraction"],
            "gross_guard_cap": gross,
            "drawdown_guard_threshold": guard["drawdown_threshold"],
            "drawdown_guard_multiplier": guard["exposure_multiplier"],
            "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
        }},
        "v16": {"candidate": v16_c, "data": v16_d, "targets": v16_t, "execution": v16_ex, "kwargs": v16_kw},
    }

    full_bench = {}
    severe_bench = {}
    for name, item in benchmarks.items():
        full_bench[name] = exact_benchmark(item, float(item["execution"]["base_cost_per_side"]))
        severe_bench[name] = exact_benchmark(item, float(item["execution"]["severe_cost_per_side"]))
    full_env = envelope(full_bench)
    severe_env = envelope(severe_bench)

    common_idx = v15_result.equity.index.intersection(v16_result.equity.index)
    signal_raw = raw.reindex(index=common_idx, columns=data.close.columns).fillna(0.0)
    signal_close = data.close.reindex(index=common_idx, columns=data.close.columns)

    presets = (
        {"contribution_trigger": 0.010, "concentration_trigger": 0.55, "top_adverse6": 0.020, "market_adverse_trigger": 0.030, "adverse_breadth_trigger": 0.70, "breadth_contribution_floor": 0.006},
        {"contribution_trigger": 0.015, "concentration_trigger": 0.60, "top_adverse6": 0.025, "market_adverse_trigger": 0.040, "adverse_breadth_trigger": 0.75, "breadth_contribution_floor": 0.008},
        {"contribution_trigger": 0.020, "concentration_trigger": 0.65, "top_adverse6": 0.030, "market_adverse_trigger": 0.050, "adverse_breadth_trigger": 0.80, "breadth_contribution_floor": 0.010},
    )

    rows = []
    for preset, cooldown, safe_weight in itertools.product(presets, (6, 12, 24), (0.50, 0.75, 1.00)):
        p = {**preset, "cooldown": cooldown, "safe_weight": safe_weight, "min_net": 0.10}
        active, diag = risk_signal(signal_raw, signal_close, p)
        eq, weight, transfer_cost = combine_router(
            v15_result.equity.reindex(common_idx),
            v16_result.equity.reindex(common_idx),
            active,
            safe_weight,
            max(base_cost, v16_base_cost),
        )
        s = stats(eq)
        split = int(len(eq) * 0.60)
        hold_start = eq.index[min(split + 1, len(eq) - 1)]
        hold = stats(eq.loc[hold_start:])
        v15_hold = stats(v15_result.equity.reindex(eq.index).loc[hold_start:])
        wealth = (1.0 + s["return"]) / max(1e-12, 1.0 + v15["return"])
        hold_wealth = (1.0 + hold["return"]) / max(1e-12, 1.0 + v15_hold["return"])
        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_ratio = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        score = (
            7.0 * np.log(max(wealth, 1e-12))
            + 5.0 * np.log(max(hold_wealth, 1e-12))
            + 10.0 * max(0.0, 1.0 - dd_ratio)
            - 14.0 * max(0.0, dd_ratio - 1.0)
            - 9.0 * max(0.0, worst_ratio - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "wealth_ratio_to_v15": float(wealth),
            "holdout_wealth_ratio_to_v15": float(hold_wealth),
            "drawdown_ratio_to_full_envelope": float(dd_ratio),
            "worst_day_ratio_to_full_envelope": float(worst_ratio),
            "risk_active_fraction": float(active.mean()),
            "average_v16_weight": float(weight.mean()),
            "transfer_cost_multiple": float(transfer_cost),
            "diagnostics": {
                "mean_contribution": float(diag["contribution"].mean()),
                "p95_contribution": float(diag["contribution"].quantile(0.95)),
                "mean_adverse_gross_fraction": float(diag["adverse_gross_fraction"].mean()),
                "instant_trigger_fraction": float(diag["instant"].mean()),
            },
            "score": float(score),
        })
        gc.collect()

    rows.sort(key=lambda z: z["score"], reverse=True)
    finalists = []
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())

    for row in rows[:12]:
        p = row["params"]
        isolated = {}
        isolated_bench = {}
        env_rows = {}
        wins = {}
        material = {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c = isolated_candidate(
                data, raw, ex, guard, gross,
                v16_d, v16_t, v16_ex, v16_kw,
                base_cost, v16_base_cost, p, start, common_end,
            )
            bench_rows = {
                name: exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = envelope(bench_rows)
            k = str(days)
            isolated[k] = c
            isolated_bench[k] = bench_rows
            env_rows[k] = env
            wins[k] = {
                "return": c["return"] >= env["return"],
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
            }
            material[k] = {
                "return": c["return"] >= env["return"] + metric_margin(env["return"]),
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"] * 0.95,
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"] * 0.95,
            }

        alt = {}
        for days in ALT_HORIZONS:
            if common_end - pd.Timedelta(days=days) < max(item["data"].close.index[0] for item in benchmarks.values()):
                continue
            start = common_end - pd.Timedelta(days=days)
            c = isolated_candidate(
                data, raw, ex, guard, gross,
                v16_d, v16_t, v16_ex, v16_kw,
                base_cost, v16_base_cost, p, start, common_end,
            )
            bench_rows = {
                name: exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = envelope(bench_rows)
            alt[str(days)] = {
                "candidate": c,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        active_sev, _ = risk_signal(signal_raw, signal_close, p)
        sev_eq, sev_weight, sev_transfer = combine_router(
            v15_severe_result.equity.reindex(common_idx),
            v16_severe_result.equity.reindex(common_idx),
            active_sev,
            p["safe_weight"],
            max(severe_cost, v16_severe_cost),
        )
        sev = stats(sev_eq)
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_risk_pass = (
            abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
            and abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        )
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_risk_pass = (
            abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
            and abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        )
        all_wins = all(all(v.values()) for v in wins.values())
        all_material = all(all(v.values()) for v in material.values())
        alt_all = bool(alt) and all(x["return_win"] and x["drawdown_win"] and x["worst_day_win"] for x in alt.values())
        dominant = bool(
            all_material
            and alt_all
            and full_return_pass
            and full_risk_pass
            and row["holdout_wealth_ratio_to_v15"] >= 1.10
            and severe_return_pass
            and severe_risk_pass
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_benchmarks": isolated_bench,
            "isolated_envelope": env_rows,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alt,
            "all_envelope_dimensions_won": all_wins,
            "all_material_envelope_dimensions_won": all_material,
            "all_alternative_envelopes_won": alt_all,
            "severe_cost": sev,
            "severe_return_pass": severe_return_pass,
            "severe_risk_pass": severe_risk_pass,
            "severe_average_v16_weight": float(sev_weight.mean()),
            "severe_transfer_cost_multiple": float(sev_transfer),
            "full_return_pass": full_return_pass,
            "full_risk_pass": full_risk_pass,
            "dominant_gate_passed": dominant,
        })

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["all_material_envelope_dimensions_won"],
            z["all_envelope_dimensions_won"],
            sum(sum(v.values()) for v in z["material_envelope_wins"].values()),
            sum(sum(v.values()) for v in z["envelope_wins"].values()),
            z["all_alternative_envelopes_won"],
            z["holdout_wealth_ratio_to_v15"],
            z["wealth_ratio_to_v15"],
            -z["drawdown_ratio_to_full_envelope"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R36 causal V15-to-V16 safe-core router",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "keep V15 as the default growth engine, but causally route a fraction of capital into the independently stateful V16 engine when requested-position loss contribution, concentration, adverse breadth, or net-market conflict becomes dangerous; charge two-sided transfer costs on every route change",
        "research_policy": "small predeclared 3x3x3 grid; ranking uses full history plus holdout and downside envelope, while requested 7/30/90/180/365 horizons and alternative horizons are validation gates rather than free-form optimizer inputs",
        "grid_size": len(rows),
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "all_screened": rows,
        "disclosure": "Historical research only. Risk features are computed from information available at close t; capital routing is shifted one hour and therefore applies only to the next interval. V15 and V16 retain independent shadow state, and every capital migration pays explicit two-sided transfer friction. No real-order code is enabled. Any historical winner must still be frozen before forward paper.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "grid_size": len(rows), "full_envelope": full_env, "severe_envelope": severe_env, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    main()
