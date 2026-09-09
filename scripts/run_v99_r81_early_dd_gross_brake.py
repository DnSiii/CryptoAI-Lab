from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55
import run_v99_r67_dynamic_hedge_router as r67
import run_v99_r75_hedged_recovery_alpha as r75

REPORT = PROJECT / "reports" / "candidate_v99_r81_early_dd_gross_brake.json"
r36 = r67.r36

DD_LO = 0.05
DD_HI = 0.12
GROSS_THRESHOLD = 1.0908627968606097  # R80 train-only q80
BRAKE_MULTIPLIER = 0.90
HOLDOUT_START = pd.Timestamp("2024-04-11T00:00:00+00:00")
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def daily_hold_gate(raw_gate: pd.Series) -> tuple[pd.Series, dict]:
    decision = pd.Series(np.nan, index=raw_gate.index, dtype=float)
    positions = np.arange(0, len(raw_gate), 24, dtype=int)
    if len(positions):
        decision.iloc[positions] = raw_gate.iloc[positions].astype(float).to_numpy()
    held = decision.ffill(limit=23).fillna(0.0).gt(0.0)
    return held, {
        "decision_count": int(len(positions)),
        "raw_gate_fraction": float(raw_gate.mean()),
        "daily_held_gate_fraction": float(held.mean()),
    }


def build_variant(data, raw, ex, guard, gross, cost, apply_brake: bool):
    parent, parent_targets, parent_diag = r75.build_variant(data, raw, ex, guard, gross, cost, False)
    shadow_eq = parent.equity.astype(float)
    shadow_dd = -(shadow_eq / shadow_eq.cummax() - 1.0)
    shadow_gross = parent_targets.abs().sum(axis=1)
    raw_gate = (
        (shadow_dd >= DD_LO)
        & (shadow_dd < DD_HI)
        & (shadow_gross >= GROSS_THRESHOLD)
    )
    gate, gate_diag = daily_hold_gate(raw_gate)
    targets = parent_targets.copy()
    if apply_brake:
        targets.loc[gate, :] = targets.loc[gate, :] * BRAKE_MULTIPLIER
    result = r36.run(data, targets, ex, cost, float(r67.P15["gross_cap"]), guard)
    diag = {
        **parent_diag,
        **gate_diag,
        "dd_lo": DD_LO,
        "dd_hi": DD_HI,
        "gross_threshold": GROSS_THRESHOLD,
        "brake_multiplier": BRAKE_MULTIPLIER,
        "gate_mean_shadow_dd": float(shadow_dd.loc[gate].mean()) if gate.any() else 0.0,
        "gate_mean_shadow_gross": float(shadow_gross.loc[gate].mean()) if gate.any() else 0.0,
        "turnover_delta_vs_parent": float(result.turnover.sum() - parent.turnover.sum()),
    }
    return result, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    cand, parent, _ = build_variant(d, rr, ex, guard, gross, cost, True)
    return r36.stats(cand.equity), r36.stats(parent.equity)


def main():
    cand_cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])

    cand, parent, diag = build_variant(data, raw, ex, guard, gross, base_cost, True)
    cand_sev, parent_sev, sev_diag = build_variant(data, raw, ex, guard, gross, severe_cost, True)
    cs, ps = r36.stats(cand.equity), r36.stats(parent.equity)
    csev, psev = r36.stats(cand_sev.equity), r36.stats(parent_sev.equity)

    hold_idx = cand.equity.index[cand.equity.index >= HOLDOUT_START]
    ch = r36.stats(cand.equity.loc[hold_idx])
    ph = r36.stats(parent.equity.loc[hold_idx])

    benchmarks = r55.benchmark_items(cand_cfg, data, raw, ex, guard, gross)
    full_bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"])) for n, x in benchmarks.items()}
    severe_bench = {n: r36.exact_benchmark(x, float(x["execution"]["severe_cost_per_side"])) for n, x in benchmarks.items()}
    common_end = min(x["data"].close.index[-1] for x in benchmarks.values())
    earliest = max(x["data"].close.index[0] for x in benchmarks.values())

    iso, iso_parent, parent_wins, env_wins = {}, {}, {}, {}
    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        c, p = eval_slice(data, raw, ex, guard, gross, base_cost, start, common_end)
        bench = {n: r36.exact_benchmark(x, float(x["execution"]["base_cost_per_side"]), start, common_end) for n, x in benchmarks.items()}
        env = r36.envelope(bench)
        k = str(days)
        iso[k], iso_parent[k] = c, p
        parent_wins[k] = {
            "return": c["return"] >= p["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }
        env_wins[k] = {
            "return": c["return"] >= env["return"],
            "drawdown": abs(c["max_drawdown"]) <= env["max_drawdown_abs"],
            "worst_day": abs(c["worst_day"]) <= env["worst_day_abs"],
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
    dim_wins = int(sum(sum(v.values()) for v in parent_wins.values()))

    out = {
        "study": "V99 R81 R73 early-drawdown selective gross brake",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "apply one predeclared mild 10% gross reduction only when the independent shadow R73 path is in 5-12% drawdown and its requested gross exceeds the R80 train-only threshold 1.0908628; evaluate once daily and hold for 24h",
        "gate": {
            "dd_range": [DD_LO, DD_HI],
            "gross_threshold": GROSS_THRESHOLD,
            "threshold_source": "R80 first-60% early-DD training block, selected without holdout",
            "R80_train_lift": 1.7647058823529411,
            "R80_holdout_lift": 1.4870244565217392,
            "R80_positive_lift_folds": "4/5",
            "brake_multiplier": BRAKE_MULTIPLIER,
            "decision_cadence_hours": 24,
            "gate_source": "independent shadow R73 equity and targets",
        },
        "parent_r73": {"summary": ps, "holdout_after_r80_train": ph, "severe": psev},
        "candidate": {"summary": cs, "holdout_after_r80_train": ch, "severe": csev, "diagnostics": diag, "severe_diagnostics": sev_diag},
        "ratios_vs_parent": {
            "full_wealth": float((1+cs["return"])/max(1e-12,1+ps["return"])),
            "holdout_wealth": float((1+ch["return"])/max(1e-12,1+ph["return"])),
            "severe_wealth": float((1+csev["return"])/max(1e-12,1+psev["return"])),
            "full_dd": float(abs(cs["max_drawdown"])/max(1e-12,abs(ps["max_drawdown"]))),
            "full_worst": float(abs(cs["worst_day"])/max(1e-12,abs(ps["worst_day"]))),
        },
        "isolated": iso,
        "isolated_parent_r73": iso_parent,
        "parent_horizon_wins": parent_wins,
        "envelope_wins": env_wins,
        "alternative_horizons": alt,
        "full_parent_dominance": bool(full_dom),
        "holdout_parent_dominance": bool(hold_dom),
        "severe_parent_dominance": bool(severe_dom),
        "requested_parent_dimension_wins": dim_wins,
        "strict_parent_gate_passed": bool(full_dom and hold_dom and severe_dom and dim_wins == 15),
        "full_benchmarks": full_bench,
        "severe_benchmarks": severe_bench,
        "disclosure": "Historical research only. R81 introduces no fitted action size: 10% was predeclared before reading R80's result. The predictive threshold is training-only and the gate uses a shadow parent so the intervention cannot change its own trigger. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"study":out["study"],"parent":out["parent_r73"],"candidate":out["candidate"],"ratios":out["ratios_vs_parent"],"strict":out["strict_parent_gate_passed"]},indent=2),flush=True)


if __name__ == "__main__":
    main()
