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

import run_v99_r36_safe_core_router as r36

REPORT = PROJECT / "reports" / "candidate_v99_r37_crash_shield.json"
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
R30_BASE = {
    "dd_trigger": 0.06,
    "hedge_size": 0.40,
    "cooldown": 72,
    "market_level": 1,
    "min_net": 0.10,
    "gross_cap": 1.90,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def r30_stress_mask(shadow: pd.Series, btc: pd.Series, p: dict) -> pd.Series:
    dd = shadow / shadow.cummax() - 1.0
    threshold = -abs(p["dd_trigger"])
    cross = (dd <= threshold) & (dd.shift(1).fillna(0.0) > threshold)
    r24 = btc.pct_change(24, fill_method=None)
    r72 = btc.pct_change(72, fill_method=None)
    if p["market_level"] == 1:
        shock = (r24 <= -0.025) | (r72 <= -0.05)
    elif p["market_level"] == 2:
        shock = (r24 <= -0.035) | (r72 <= -0.07)
    else:
        shock = (r24 <= -0.045) | (r72 <= -0.09)
    return (cross | shock.fillna(False)).astype(float).rolling(
        int(p["cooldown"]), min_periods=1
    ).max().gt(0.0)


def r30_targets(raw: pd.DataFrame, shadow: pd.Series, close: pd.DataFrame, p: dict):
    active = r30_stress_mask(shadow, close["BTCUSDT"], p)
    net = raw.sum(axis=1)
    direction = -np.sign(net).where(net.abs() >= p["min_net"], 0.0)
    out = raw.copy()
    if "BTCUSDT" not in out.columns:
        raise RuntimeError("BTCUSDT missing from V15 universe")
    out["BTCUSDT"] = out["BTCUSDT"] + active.astype(float) * direction * p["hedge_size"]
    return r36.cap(out, p["gross_cap"]), active


def build_r30(data, raw, ex, guard, base_gross, cost):
    shadow = r36.run(data, raw, ex, cost, base_gross, guard).equity
    targets, hedge_active = r30_targets(raw, shadow, data.close, R30_BASE)
    result = r36.run(data, targets, ex, cost, R30_BASE["gross_cap"], guard)
    return result, targets, hedge_active


def crash_signal(r30_equity: pd.Series, btc: pd.Series, p: dict) -> tuple[pd.Series, dict]:
    eq = r30_equity.astype(float)
    r6 = eq.pct_change(6, fill_method=None)
    r24 = eq.pct_change(24, fill_method=None)
    dd = eq / eq.cummax() - 1.0
    b24 = btc.pct_change(24, fill_method=None)
    b72 = btc.pct_change(72, fill_method=None)

    fast_loss = r6 <= p["r6_trigger"]
    drawdown_accel = (dd <= p["dd_trigger"]) & (r24 <= p["r24_trigger"])
    market_conflict = ((b24 <= p["btc24_trigger"]) | (b72 <= p["btc72_trigger"])) & (r6 < 0.0)
    instant = (fast_loss | drawdown_accel | market_conflict).fillna(False)
    active = instant.astype(float).rolling(int(p["cooldown"]), min_periods=1).max().gt(0.0)
    return active, {
        "instant_fraction": float(instant.mean()),
        "active_fraction": float(active.mean()),
        "mean_r6": float(r6.fillna(0.0).mean()),
        "p05_r6": float(r6.dropna().quantile(0.05)) if r6.notna().any() else 0.0,
        "minimum_drawdown": float(dd.min()),
    }


def adaptive_safe_choice(v13_equity: pd.Series, v16_equity: pd.Series) -> pd.Series:
    aligned = pd.concat([v13_equity.rename("v13"), v16_equity.rename("v16")], axis=1, join="inner").dropna()
    scores = {}
    for name in ("v13", "v16"):
        eq = aligned[name]
        ret = eq.pct_change(fill_method=None).fillna(0.0)
        downside = ret.clip(upper=0.0).rolling(720, min_periods=168).std().fillna(np.inf)
        rolling_peak = eq.rolling(720, min_periods=168).max()
        dd = (eq / rolling_peak - 1.0).abs().fillna(np.inf)
        scores[name] = downside + 0.20 * dd
    choose_v16 = scores["v16"] < scores["v13"]
    # Before enough history exists, V16 is the safer recent-horizon default.
    no_history = ~np.isfinite(scores["v13"]) & ~np.isfinite(scores["v16"])
    choose_v16 = choose_v16.mask(no_history, True)
    return choose_v16.astype(float)


def combine_shield(
    growth_equity: pd.Series,
    v13_equity: pd.Series,
    v16_equity: pd.Series,
    active: pd.Series,
    safe_weight: float,
    mode: str,
    transfer_cost_per_side: float,
) -> tuple[pd.Series, dict]:
    aligned = pd.concat(
        [
            growth_equity.rename("growth"),
            v13_equity.rename("v13"),
            v16_equity.rename("v16"),
            active.rename("active"),
        ],
        axis=1,
        join="inner",
    ).dropna(subset=["growth", "v13", "v16"])
    rg = aligned["growth"].pct_change(fill_method=None).fillna(0.0)
    r13 = aligned["v13"].pct_change(fill_method=None).fillna(0.0)
    r16 = aligned["v16"].pct_change(fill_method=None).fillna(0.0)

    safe = aligned["active"].fillna(False).astype(float).shift(1).fillna(0.0) * float(safe_weight)
    if mode == "v16":
        choose16 = pd.Series(1.0, index=aligned.index)
    elif mode == "cash":
        choose16 = pd.Series(0.0, index=aligned.index)
    elif mode == "adaptive":
        choose16 = adaptive_safe_choice(aligned["v13"], aligned["v16"]).reindex(aligned.index).fillna(1.0).shift(1).fillna(1.0)
    else:
        raise ValueError(mode)

    growth_cap = 1.0
    v13_cap = 0.0
    v16_cap = 0.0
    cash_cap = 0.0
    equity = pd.Series(index=aligned.index, dtype=float)
    realized_safe = pd.Series(index=aligned.index, dtype=float)
    equity.iloc[0] = 1.0
    realized_safe.iloc[0] = 0.0
    transfer_cost_total = 0.0
    route_changes = 0

    for i in range(1, len(aligned)):
        total = growth_cap + v13_cap + v16_cap + cash_cap
        if total <= 0.0:
            equity.iloc[i:] = 0.0
            realized_safe.iloc[i:] = 0.0
            break

        sw = float(safe.iloc[i])
        if mode == "cash":
            desired = np.array([1.0 - sw, 0.0, 0.0, sw], dtype=float)
        elif mode == "v16":
            desired = np.array([1.0 - sw, 0.0, sw, 0.0], dtype=float)
        else:
            c16 = float(choose16.iloc[i])
            desired = np.array([1.0 - sw, sw * (1.0 - c16), sw * c16, 0.0], dtype=float)

        current = np.array([growth_cap, v13_cap, v16_cap, cash_cap], dtype=float) / total
        moved = 0.5 * float(np.abs(current - desired).sum())
        if moved > 1e-10:
            route_changes += 1
            cost = total * moved * 2.0 * float(transfer_cost_per_side)
            transfer_cost_total += cost
            total = max(0.0, total - cost)
            growth_cap, v13_cap, v16_cap, cash_cap = (total * desired).tolist()

        growth_cap *= 1.0 + float(rg.iloc[i])
        v13_cap *= 1.0 + float(r13.iloc[i])
        v16_cap *= 1.0 + float(r16.iloc[i])
        total_after = growth_cap + v13_cap + v16_cap + cash_cap
        equity.iloc[i] = total_after
        realized_safe.iloc[i] = (v13_cap + v16_cap + cash_cap) / max(total_after, 1e-12)

    return equity.ffill().fillna(1.0), {
        "transfer_cost_multiple": float(transfer_cost_total),
        "route_changes": int(route_changes),
        "average_safe_weight": float(realized_safe.ffill().fillna(0.0).mean()),
        "maximum_safe_weight": float(realized_safe.ffill().fillna(0.0).max()),
    }


def slice_data(data, start, end):
    return r36.sdata(data, start, end)


def isolated_candidate(
    data, raw, ex, guard, gross, v13_item, v16_item,
    base_cost, p, start, end,
):
    d = slice_data(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    growth, _, _ = build_r30(d, rr, ex, guard, gross, base_cost)

    d13 = r36.slice_futures(v13_item["data"], start, end)
    t13 = v13_item["targets"].reindex(index=d13.close.index, columns=d13.close.columns).fillna(0.0)
    res13 = r36.exact_fast(d13, t13, cost_per_side=float(v13_item["execution"]["base_cost_per_side"]), **v13_item["kwargs"])

    d16 = r36.slice_futures(v16_item["data"], start, end)
    t16 = v16_item["targets"].reindex(index=d16.close.index, columns=d16.close.columns).fillna(0.0)
    res16 = r36.exact_fast(d16, t16, cost_per_side=float(v16_item["execution"]["base_cost_per_side"]), **v16_item["kwargs"])

    idx = growth.equity.index.intersection(res13.equity.index).intersection(res16.equity.index)
    active, _ = crash_signal(growth.equity.reindex(idx), d.close["BTCUSDT"].reindex(idx), p)
    eq, _ = combine_shield(
        growth.equity.reindex(idx), res13.equity.reindex(idx), res16.equity.reindex(idx),
        active, p["safe_weight"], p["mode"],
        max(base_cost, float(v13_item["execution"]["base_cost_per_side"]), float(v16_item["execution"]["base_cost_per_side"])),
    )
    return r36.stats(eq)


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    r30, _, r30_hedge_active = build_r30(data, raw, ex, guard, gross, base_cost)
    r30_severe, _, _ = build_r30(data, raw, ex, guard, gross, severe_cost)
    r30_stats = r36.stats(r30.equity)
    r30_severe_stats = r36.stats(r30_severe.equity)

    v13_c, v13_d, v13_t, v13_ex, v13_kw = r36.build_v13_benchmark()
    v14_c, v14_d, v14_t, v14_ex, v14_kw = r36.build_v14_benchmark()
    v16_c, v16_d, v16_t, v16_ex, v16_kw = r36.build_v16_benchmark()
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
    full_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    severe_bench = {
        name: r36.exact_benchmark(item, float(item["execution"]["severe_cost_per_side"]))
        for name, item in benchmarks.items()
    }
    full_env = r36.envelope(full_bench)
    severe_env = r36.envelope(severe_bench)

    res13 = r36.exact_fast(v13_d, v13_t, cost_per_side=float(v13_ex["base_cost_per_side"]), **v13_kw)
    res16 = r36.exact_fast(v16_d, v16_t, cost_per_side=float(v16_ex["base_cost_per_side"]), **v16_kw)
    res13_sev = r36.exact_fast(v13_d, v13_t, cost_per_side=float(v13_ex["severe_cost_per_side"]), **v13_kw)
    res16_sev = r36.exact_fast(v16_d, v16_t, cost_per_side=float(v16_ex["severe_cost_per_side"]), **v16_kw)

    common_idx = r30.equity.index.intersection(res13.equity.index).intersection(res16.equity.index)
    btc = data.close["BTCUSDT"].reindex(common_idx)

    presets = (
        {"name": "early", "r6_trigger": -0.025, "dd_trigger": -0.050, "r24_trigger": -0.040, "btc24_trigger": -0.035, "btc72_trigger": -0.070, "cooldown": 6},
        {"name": "medium", "r6_trigger": -0.035, "dd_trigger": -0.070, "r24_trigger": -0.055, "btc24_trigger": -0.045, "btc72_trigger": -0.090, "cooldown": 12},
        {"name": "deep", "r6_trigger": -0.045, "dd_trigger": -0.090, "r24_trigger": -0.070, "btc24_trigger": -0.055, "btc72_trigger": -0.110, "cooldown": 24},
    )

    split = int(len(common_idx) * 0.60)
    hold_start = common_idx[min(split + 1, len(common_idx) - 1)]
    r30_hold = r36.stats(r30.equity.reindex(common_idx).loc[hold_start:])
    rows = []
    for preset, safe_weight, mode in itertools.product(presets, (0.20, 0.35, 0.50), ("v16", "adaptive", "cash")):
        p = {**preset, "safe_weight": safe_weight, "mode": mode}
        active, signal_diag = crash_signal(r30.equity.reindex(common_idx), btc, p)
        eq, route_diag = combine_shield(
            r30.equity.reindex(common_idx),
            res13.equity.reindex(common_idx),
            res16.equity.reindex(common_idx),
            active, safe_weight, mode,
            max(base_cost, float(v13_ex["base_cost_per_side"]), float(v16_ex["base_cost_per_side"])),
        )
        s = r36.stats(eq)
        hold = r36.stats(eq.loc[hold_start:])
        wealth_to_r30 = (1.0 + s["return"]) / max(1e-12, 1.0 + r30_stats["return"])
        hold_to_r30 = (1.0 + hold["return"]) / max(1e-12, 1.0 + r30_hold["return"])
        dd_env = abs(s["max_drawdown"]) / max(1e-12, full_env["max_drawdown_abs"])
        worst_env = abs(s["worst_day"]) / max(1e-12, full_env["worst_day_abs"])
        return_env = (1.0 + s["return"]) / max(1e-12, 1.0 + full_env["return"])
        score = (
            7.0 * np.log(max(return_env, 1e-12))
            + 4.0 * np.log(max(hold_to_r30, 1e-12))
            + 10.0 * max(0.0, 1.0 - dd_env)
            - 14.0 * max(0.0, dd_env - 1.0)
            + 8.0 * max(0.0, 1.0 - worst_env)
            - 12.0 * max(0.0, worst_env - 1.0)
        )
        rows.append({
            "params": p,
            "summary": s,
            "holdout": hold,
            "wealth_ratio_to_r30": float(wealth_to_r30),
            "holdout_wealth_ratio_to_r30": float(hold_to_r30),
            "return_ratio_to_full_envelope": float(return_env),
            "drawdown_ratio_to_full_envelope": float(dd_env),
            "worst_day_ratio_to_full_envelope": float(worst_env),
            "signal": signal_diag,
            "routing": route_diag,
            "score": float(score),
        })
        gc.collect()

    rows.sort(key=lambda x: x["score"], reverse=True)
    common_end = min(item["data"].close.index[-1] for item in benchmarks.values())
    v13_item = benchmarks["v13"]
    v16_item = benchmarks["v16"]
    finalists = []

    for row in rows[:9]:
        p = row["params"]
        isolated, isolated_bench, envelopes, wins, material = {}, {}, {}, {}, {}
        for days in HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            c = isolated_candidate(data, raw, ex, guard, gross, v13_item, v16_item, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            k = str(days)
            isolated[k], isolated_bench[k], envelopes[k] = c, bench, env
            wins[k] = {
                "return": c["return"] >= env["return"],
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
            }
            material[k] = {
                "return": c["return"] >= env["return"] + r36.metric_margin(env["return"]),
                "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"] * 0.95,
                "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"] * 0.95,
            }

        alternative = {}
        earliest = max(item["data"].close.index[0] for item in benchmarks.values())
        for days in ALT_HORIZONS:
            start = common_end - pd.Timedelta(days=days)
            if start < earliest:
                continue
            c = isolated_candidate(data, raw, ex, guard, gross, v13_item, v16_item, base_cost, p, start, common_end)
            bench = {
                name: r36.exact_benchmark(item, float(item["execution"]["base_cost_per_side"]), start, common_end)
                for name, item in benchmarks.items()
            }
            env = r36.envelope(bench)
            alternative[str(days)] = {
                "candidate": c,
                "envelope": env,
                "return_win": c["return"] >= env["return"],
                "drawdown_win": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
                "worst_day_win": abs(c["worst_day"]) <= env["worst_day_abs"],
            }

        active_sev, _ = crash_signal(r30_severe.equity.reindex(common_idx), btc, p)
        sev_eq, sev_route = combine_shield(
            r30_severe.equity.reindex(common_idx),
            res13_sev.equity.reindex(common_idx),
            res16_sev.equity.reindex(common_idx),
            active_sev, p["safe_weight"], p["mode"],
            max(severe_cost, float(v13_ex["severe_cost_per_side"]), float(v16_ex["severe_cost_per_side"])),
        )
        sev = r36.stats(sev_eq)
        full_return_pass = row["summary"]["return"] >= full_env["return"]
        full_risk_pass = (
            abs(row["summary"]["max_drawdown"]) <= full_env["max_drawdown_abs"]
            and abs(row["summary"]["worst_day"]) <= full_env["worst_day_abs"]
        )
        severe_return_pass = sev["return"] >= severe_env["return"]
        severe_risk_pass = (
            abs(sev["max_drawdown"]) <= severe_env["max_drawdown_abs"]
            and abs(sev["worst_day"]) <= severe_env["worst_day_abs"]
        )
        all_wins = all(all(v.values()) for v in wins.values())
        all_material = all(all(v.values()) for v in material.values())
        alt_all = bool(alternative) and all(
            x["return_win"] and x["drawdown_win"] and x["worst_day_win"]
            for x in alternative.values()
        )
        dominant = bool(
            all_material
            and alt_all
            and full_return_pass
            and full_risk_pass
            and row["holdout_wealth_ratio_to_r30"] >= 1.05
            and severe_return_pass
            and severe_risk_pass
        )
        finalists.append({
            **row,
            "isolated": isolated,
            "isolated_benchmarks": isolated_bench,
            "isolated_envelope": envelopes,
            "envelope_wins": wins,
            "material_envelope_wins": material,
            "alternative_horizons": alternative,
            "all_envelope_dimensions_won": all_wins,
            "all_material_envelope_dimensions_won": all_material,
            "all_alternative_envelopes_won": alt_all,
            "severe_cost": sev,
            "severe_routing": sev_route,
            "full_return_pass": full_return_pass,
            "full_risk_pass": full_risk_pass,
            "severe_return_pass": severe_return_pass,
            "severe_risk_pass": severe_risk_pass,
            "dominant_gate_passed": dominant,
        })
        gc.collect()

    finalists.sort(
        key=lambda z: (
            z["dominant_gate_passed"],
            z["all_material_envelope_dimensions_won"],
            z["all_envelope_dimensions_won"],
            sum(sum(v.values()) for v in z["material_envelope_wins"].values()),
            sum(sum(v.values()) for v in z["envelope_wins"].values()),
            z["all_alternative_envelopes_won"],
            z["full_return_pass"], z["full_risk_pass"],
            z["holdout_wealth_ratio_to_r30"],
            -z["drawdown_ratio_to_full_envelope"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None

    out = {
        "study": "V99 R37 R30 crash shield",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "use the strongest defensive R30 hedge frontier as the growth engine and deploy a rare next-open crash shield into V16, adaptive V13/V16, or cash only when R30 equity deterioration accelerates; preserve normal compounding outside those episodes",
        "r30_fixed_base": R30_BASE,
        "r30_base_summary": r30_stats,
        "r30_base_severe": r30_severe_stats,
        "r30_hedge_active_fraction": float(r30_hedge_active.mean()),
        "grid_policy": "27 predeclared combinations = 3 crash severities x 3 safe weights x 3 destinations; requested horizons are validation gates, not free-form tuning inputs",
        "grid_size": len(rows),
        "common_end": common_end.isoformat(),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "selected": selected,
        "finalists": finalists,
        "all_screened": rows,
        "disclosure": "Historical research only. Crash conditions use only R30 shadow-equity and BTC information available at close t. Routing is shifted and executed before the next interval, with explicit two-sided transfer friction. V13, V16 and R30 retain independent shadow state. No real-order path is enabled. Any winner requires a frozen forward-paper period before promotion.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "r30": r30_stats, "full_envelope": full_env, "selected": selected}, indent=2), flush=True)


if __name__ == "__main__":
    main()
