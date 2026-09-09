from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55
import run_v99_r67_dynamic_hedge_router as r67
import run_v99_r73_gross_low_72h_persistence as r73

REPORT = PROJECT / "reports" / "candidate_v99_r75_hedged_recovery_alpha.json"
RECOVERY_THRESHOLD = -0.027861955338492006  # R74 train-only q20 dir_min24_72
BOOST_SCALE = 1.10
HOLDOUT_START = pd.Timestamp("2024-01-18T00:00:00+00:00")
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
ROUTER = {"name": "h15_gross_low", "rule": "gross"}

r36 = r67.r36
r37 = r67.r37
cap = r67.cap
P15 = r67.P15
P25 = r67.P25


def daily_recovery_mask(close: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    sign = np.sign(raw)
    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    d24 = sign * r24
    d72 = sign * r72
    dmin = pd.DataFrame(np.minimum(d24.to_numpy(), d72.to_numpy()), index=close.index, columns=close.columns)
    raw_gate = (dmin <= RECOVERY_THRESHOLD) & (raw.abs() > 1e-9)

    # Match R74 daily sampling exactly: one decision every 24h, then hold that
    # symbol-level decision until the next daily observation.
    decision = pd.DataFrame(np.nan, index=raw.index, columns=raw.columns)
    positions = np.arange(0, len(raw.index), 24, dtype=int)
    if len(positions):
        decision.iloc[positions, :] = raw_gate.iloc[positions, :].astype(float).to_numpy()
    held = decision.ffill(limit=23).fillna(0.0).gt(0.0)
    return held, {
        "raw_gate_fraction": float(raw_gate.to_numpy(dtype=float).mean()),
        "daily_held_gate_fraction": float(held.to_numpy(dtype=float).mean()),
        "decision_count": int(len(positions)),
        "threshold": float(RECOVERY_THRESHOLD),
        "boost_scale": float(BOOST_SCALE),
    }


def build_variant(data, raw, ex, guard, gross, cost, with_recovery: bool):
    core = r36.run(data, raw, ex, cost, gross, guard)

    # Construct the original h0.15/h0.25 targets before capping so any recovery
    # boost affects only the requested core position, never the hedge component.
    t15_uncapped, active15 = r37.r30_targets(raw, core.equity, data.close, P15)
    t25_uncapped, active25 = r37.r30_targets(raw, core.equity, data.close, P25)
    hedge15 = t15_uncapped - raw
    hedge25 = t25_uncapped - raw

    t15_base = cap(t15_uncapped, float(P15["gross_cap"]))
    t25_base = cap(t25_uncapped, float(P25["gross_cap"]))
    portfolio_gate, portfolio_diag = r73.persistent_gate_series(data, t15_base, ROUTER)

    recovery_mask, recovery_diag = daily_recovery_mask(data.close.reindex(raw.index), raw)
    effective_recovery = recovery_mask & pd.DataFrame(
        np.repeat(portfolio_gate.reindex(raw.index).fillna(False).to_numpy()[:, None], raw.shape[1], axis=1),
        index=raw.index,
        columns=raw.columns,
    )

    adjusted_raw = raw.copy()
    if with_recovery:
        adjusted_raw = adjusted_raw * (1.0 + effective_recovery.astype(float) * (BOOST_SCALE - 1.0))

    t15 = cap(adjusted_raw + hedge15, float(P15["gross_cap"]))
    t25 = cap(adjusted_raw + hedge25, float(P25["gross_cap"]))
    targets = t15.copy()
    targets.loc[portfolio_gate, :] = t25.loc[portfolio_gate, :]
    targets = cap(targets, float(P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(P15["gross_cap"]), guard)

    diag = {
        **portfolio_diag,
        **recovery_diag,
        "portfolio_persistent_gate_fraction": float(portfolio_gate.mean()),
        "effective_recovery_fraction": float(effective_recovery.to_numpy(dtype=float).mean()),
        "effective_recovery_rows_any_symbol": float(effective_recovery.any(axis=1).mean()),
        "h15_active_fraction": float(active15.mean()),
        "h25_active_fraction": float(active25.mean()),
    }
    return result, targets, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    cand, _, _ = build_variant(d, rr, ex, guard, gross, cost, True)
    parent, _, _ = build_variant(d, rr, ex, guard, gross, cost, False)
    return r36.stats(cand.equity), r36.stats(parent.equity)


def main():
    cand_cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    candidate, _, diag = build_variant(data, raw, ex, guard, gross, base_cost, True)
    parent, _, parent_diag = build_variant(data, raw, ex, guard, gross, base_cost, False)
    candidate_sev, _, sev_diag = build_variant(data, raw, ex, guard, gross, severe_cost, True)
    parent_sev, _, parent_sev_diag = build_variant(data, raw, ex, guard, gross, severe_cost, False)

    cs = r36.stats(candidate.equity)
    ps = r36.stats(parent.equity)
    csev = r36.stats(candidate_sev.equity)
    psev = r36.stats(parent_sev.equity)

    hold_idx = candidate.equity.index[candidate.equity.index >= HOLDOUT_START]
    ch = r36.stats(candidate.equity.loc[hold_idx])
    ph = r36.stats(parent.equity.loc[hold_idx])

    benchmarks = r55.benchmark_items(cand_cfg, data, raw, ex, guard, gross)
    full_bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"])) for n, x in benchmarks.items()}
    severe_bench = {n: r36.exact_benchmark(x, float(x["execution"]["severe_cost_per_side"])) for n, x in benchmarks.items()}
    full_env = r36.envelope(full_bench)
    severe_env = r36.envelope(severe_bench)

    common_end = min(x["data"].close.index[-1] for x in benchmarks.values())
    earliest = max(x["data"].close.index[0] for x in benchmarks.values())
    iso, iso_parent, envelope_wins, parent_wins = {}, {}, {}, {}
    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        c, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, common_end)
        bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"]), start, common_end) for n, x in benchmarks.items()}
        env = r36.envelope(bench)
        k = str(days)
        iso[k], iso_parent[k] = c, p
        envelope_wins[k] = {
            "return": c["return"] >= env["return"],
            "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
            "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
        }
        parent_wins[k] = {
            "return": c["return"] >= p["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }

    alt = {}
    for days in ALT_HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        if start < earliest:
            continue
        c, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, common_end)
        alt[str(days)] = {
            "candidate": c,
            "parent_r73": p,
            "return_vs_parent": c["return"] >= p["return"],
            "drawdown_vs_parent": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day_vs_parent": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }

    full_dom = cs["return"] >= ps["return"] and abs(cs["max_drawdown"]) <= abs(ps["max_drawdown"]) and abs(cs["worst_day"]) <= abs(ps["worst_day"])
    hold_dom = ch["return"] >= ph["return"] and abs(ch["max_drawdown"]) <= abs(ph["max_drawdown"])
    severe_dom = csev["return"] >= psev["return"] and abs(csev["max_drawdown"]) <= abs(psev["max_drawdown"]) and abs(csev["worst_day"]) <= abs(psev["worst_day"])
    parent_dim_wins = int(sum(sum(v.values()) for v in parent_wins.values()))

    out = {
        "study": "V99 R75 hedged recovery alpha",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "apply a fixed 1.10x boost only to positions meeting the fresh R74 train-only contrarian recovery gate, with one decision per day and only while the independently validated R73 stronger-hedge regime is active",
        "recovery_gate": {
            "feature": "dir_min24_72",
            "direction": "low",
            "threshold": RECOVERY_THRESHOLD,
            "threshold_source": "R74 first-60%-of-dates training block ending 2024-01-17",
            "R74_temporal_lift_folds": "5/5 positive",
            "boost_scale": BOOST_SCALE,
            "decision_cadence_hours": 24,
            "portfolio_condition": "R73 h15_gross_low daily trigger with 72h h0.25 persistence",
        },
        "parent_r73": {"summary": ps, "holdout_after_r74_train": ph, "severe": psev, "diagnostics": parent_diag, "severe_diagnostics": parent_sev_diag},
        "candidate": {"summary": cs, "holdout_after_r74_train": ch, "severe": csev, "diagnostics": diag, "severe_diagnostics": sev_diag},
        "ratios_vs_parent": {
            "full_wealth": float((1 + cs["return"]) / max(1e-12, 1 + ps["return"])),
            "holdout_wealth": float((1 + ch["return"]) / max(1e-12, 1 + ph["return"])),
            "severe_wealth": float((1 + csev["return"]) / max(1e-12, 1 + psev["return"])),
            "full_dd": float(abs(cs["max_drawdown"]) / max(1e-12, abs(ps["max_drawdown"]))),
            "full_worst": float(abs(cs["worst_day"]) / max(1e-12, abs(ps["worst_day"]))),
        },
        "isolated": iso,
        "isolated_parent_r73": iso_parent,
        "envelope_wins": envelope_wins,
        "parent_horizon_wins": parent_wins,
        "alternative_horizons": alt,
        "full_parent_dominance": bool(full_dom),
        "holdout_parent_dominance": bool(hold_dom),
        "severe_parent_dominance": bool(severe_dom),
        "requested_parent_dimension_wins": parent_dim_wins,
        "strict_parent_gate_passed": bool(full_dom and hold_dom and severe_dom and parent_dim_wins == 15),
        "full_benchmarks": full_bench,
        "full_envelope": full_env,
        "severe_benchmarks": severe_bench,
        "severe_envelope": severe_env,
        "disclosure": "Historical research only. R75 adds no fitted parameter beyond the R74 train-only threshold and a predeclared 1.10x boost. The recovery gate is evaluated daily and the boost is only allowed under the independently trained R73 strong-hedge regime. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "parent": out["parent_r73"], "candidate": out["candidate"], "ratios": out["ratios_vs_parent"], "strict_parent_gate_passed": out["strict_parent_gate_passed"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
