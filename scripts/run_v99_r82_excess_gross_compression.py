from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r81_early_dd_gross_brake as r81

REPORT = PROJECT / "reports" / "candidate_v99_r82_excess_gross_compression.json"
r36 = r81.r36

DD_LO = r81.DD_LO
DD_HI = r81.DD_HI
GROSS_THRESHOLD = r81.GROSS_THRESHOLD
EXCESS_KEEP = 0.50  # predeclared structural action: retain half of gross above the R80 danger threshold
HOLDOUT_START = r81.HOLDOUT_START
HORIZONS = r81.HORIZONS
ALT_HORIZONS = r81.ALT_HORIZONS


def build_variant(data, raw, ex, guard, gross, cost, apply_compression: bool):
    parent, parent_targets, parent_diag = r81.r75.build_variant(data, raw, ex, guard, gross, cost, False)
    shadow_eq = parent.equity.astype(float)
    shadow_dd = -(shadow_eq / shadow_eq.cummax() - 1.0)
    shadow_gross = parent_targets.abs().sum(axis=1)
    raw_gate = (
        (shadow_dd >= DD_LO)
        & (shadow_dd < DD_HI)
        & (shadow_gross >= GROSS_THRESHOLD)
    )
    gate, gate_diag = r81.daily_hold_gate(raw_gate)

    targets = parent_targets.copy()
    applied_scale = pd.Series(1.0, index=targets.index, dtype=float)
    if apply_compression:
        current_gross = targets.abs().sum(axis=1)
        excess = (current_gross - GROSS_THRESHOLD).clip(lower=0.0)
        compressed_gross = GROSS_THRESHOLD + EXCESS_KEEP * excess
        scale = (compressed_gross / current_gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
        applied_scale.loc[gate] = scale.loc[gate]
        targets.loc[gate, :] = targets.loc[gate, :].mul(scale.loc[gate], axis=0)

    result = r36.run(data, targets, ex, cost, float(r81.r67.P15["gross_cap"]), guard)
    diag = {
        **parent_diag,
        **gate_diag,
        "dd_lo": DD_LO,
        "dd_hi": DD_HI,
        "gross_threshold": GROSS_THRESHOLD,
        "excess_keep": EXCESS_KEEP,
        "gate_mean_shadow_dd": float(shadow_dd.loc[gate].mean()) if gate.any() else 0.0,
        "gate_mean_shadow_gross": float(shadow_gross.loc[gate].mean()) if gate.any() else 0.0,
        "gate_mean_scale": float(applied_scale.loc[gate].mean()) if gate.any() else 1.0,
        "gate_min_scale": float(applied_scale.loc[gate].min()) if gate.any() else 1.0,
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

    benchmarks = r81.r55.benchmark_items(cand_cfg, data, raw, ex, guard, gross)
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
        "study": "V99 R82 R73 early-DD excess-gross compression",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "instead of scaling the whole R73 book by 10%, preserve gross up to the R80 train-only threshold and compress only half of the excess above it while the shadow R73 path is in 5-12% drawdown; daily decision held 24h",
        "gate": {
            "dd_range": [DD_LO, DD_HI],
            "gross_threshold": GROSS_THRESHOLD,
            "threshold_source": "R80 first-60% early-DD training block, selected without holdout",
            "excess_keep": EXCESS_KEEP,
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
        "disclosure": "Historical research only. R82 does not tune the R80 predictive threshold. The intervention is structurally predeclared as 50% compression of gross excess above that threshold. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"study":out["study"],"parent":out["parent_r73"],"candidate":out["candidate"],"ratios":out["ratios_vs_parent"],"strict":out["strict_parent_gate_passed"]},indent=2),flush=True)


if __name__ == "__main__":
    main()
