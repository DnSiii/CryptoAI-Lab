from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r88_selective_exposure_expansion as r88

r36 = r88.r36
cap = r88.cap
REPORT = PROJECT / "reports" / "candidate_v99_r95_selective_no_reallocation_expansion.json"
R93_ABS_TARGET_THRESHOLD = 0.4169397245236464
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)


def build_variant(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r88.r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)

    # Frozen R88 reference.
    r88_targets = parent_targets.copy()
    if gate.any():
        r88_targets.loc[gate, :] = r88_targets.loc[gate, :] * r88.SCALE
    r88_targets = cap(r88_targets, float(r88.r86.P15["gross_cap"]))
    r88_result = r36.run(data, r88_targets, ex, cost, float(r88.r86.P15["gross_cap"]), guard)

    # R95: apply the same +10% only to positions whose absolute parent target
    # passes the frozen R93 train-only threshold. No unused sleeve is
    # redistributed, so concentration cannot exceed the local 1.10 scale.
    targets = parent_targets.copy()
    eligible = parent_targets.abs() >= R93_ABS_TARGET_THRESHOLD
    apply = eligible.mul(gate, axis=0)
    targets = targets.where(~apply, targets * r88.SCALE)
    targets = cap(targets, float(r88.r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r88.r86.P15["gross_cap"]), guard)

    active = parent_targets.abs() > 1e-12
    selected_cells = int((apply & active).to_numpy().sum())
    active_gate_cells = int((active.mul(gate, axis=0)).to_numpy().sum())
    gate_rows = int(gate.sum())
    rows_with_selection = int((apply.any(axis=1) & gate).sum())

    diag = {
        **pdiag,
        **gdiag,
        "allocation_feature": "abs(parent_r73_target)",
        "allocation_threshold": R93_ABS_TARGET_THRESHOLD,
        "threshold_source": "R93 first-60% train only; 5/5 positive contribution/lift folds",
        "scale": r88.SCALE,
        "allocation_rule": "apply 1.10 only to eligible positions; unused incremental budget is not reallocated",
        "gate_rows": gate_rows,
        "rows_with_selection": rows_with_selection,
        "rows_with_selection_fraction": float(rows_with_selection / gate_rows) if gate_rows else 0.0,
        "selected_position_fraction_within_gate": float(selected_cells / active_gate_cells) if active_gate_cells else 0.0,
        "effective_extra_gross_mean": float((targets.abs().sum(axis=1) - parent_targets.abs().sum(axis=1)).clip(lower=0.0).loc[gate].mean()) if gate.any() else 0.0,
        "r88_extra_gross_mean": float((r88_targets.abs().sum(axis=1) - parent_targets.abs().sum(axis=1)).clip(lower=0.0).loc[gate].mean()) if gate.any() else 0.0,
        "turnover_delta_vs_r73": float(result.turnover.sum() - parent.turnover.sum()),
        "turnover_delta_vs_r88": float(result.turnover.sum() - r88_result.turnover.sum()),
        "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
    }
    return result, r88_result, parent, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    c, g, p, _ = build_variant(d, rr, ex, guard, gross, cost)
    return r36.stats(c.equity), r36.stats(g.equity), r36.stats(p.equity)


def wealth_ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base = float(ex["base_cost_per_side"])
    severe = float(ex["severe_cost_per_side"])

    cand, growth, parent, diag = build_variant(data, raw, ex, guard, gross, base)
    cand_sev, growth_sev, parent_sev, sev_diag = build_variant(data, raw, ex, guard, gross, severe)

    cs, gs, ps = r36.stats(cand.equity), r36.stats(growth.equity), r36.stats(parent.equity)
    csev, gsev, psev = r36.stats(cand_sev.equity), r36.stats(growth_sev.equity), r36.stats(parent_sev.equity)

    hold_idx = cand.equity.index[cand.equity.index > r88.TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else cand.equity.index[-1]
    ch = r36.stats(cand.equity.loc[hold_start:])
    gh = r36.stats(growth.equity.loc[hold_start:])
    ph = r36.stats(parent.equity.loc[hold_start:])

    end = data.close.index[-1]
    earliest = data.close.index[0]
    isolated = {}
    wins_parent = {}
    wins_r88 = {}
    for days in HORIZONS:
        start = end - pd.Timedelta(days=int(days))
        c, g, p = eval_slice(data, raw, ex, guard, gross, base, start, end)
        k = str(days)
        isolated[k] = {"candidate": c, "r88_growth": g, "r73_parent": p}
        wins_parent[k] = {
            "return": c["return"] >= p["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(p["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(p["worst_day"]),
        }
        wins_r88[k] = {
            "return": c["return"] >= g["return"],
            "drawdown": abs(c["max_drawdown"]) <= abs(g["max_drawdown"]),
            "worst_day": abs(c["worst_day"]) <= abs(g["worst_day"]),
        }
        gc.collect()

    alternative = {}
    for days in ALT_HORIZONS:
        start = end - pd.Timedelta(days=int(days))
        if start < earliest:
            continue
        c, g, p = eval_slice(data, raw, ex, guard, gross, base, start, end)
        alternative[str(days)] = {
            "candidate": c,
            "r88_growth": g,
            "r73_parent": p,
            "wealth_vs_r88": wealth_ratio(c, g),
            "wealth_vs_r73": wealth_ratio(c, p),
            "dd_win_vs_r88": abs(c["max_drawdown"]) <= abs(g["max_drawdown"]),
            "worst_win_vs_r88": abs(c["worst_day"]) <= abs(g["worst_day"]),
        }
        gc.collect()

    parent_dims = int(sum(sum(v.values()) for v in wins_parent.values()))
    r88_dims = int(sum(sum(v.values()) for v in wins_r88.values()))

    full_parent_dom = cs["return"] >= ps["return"] and abs(cs["max_drawdown"]) <= abs(ps["max_drawdown"]) and abs(cs["worst_day"]) <= abs(ps["worst_day"])
    hold_parent_dom = ch["return"] >= ph["return"] and abs(ch["max_drawdown"]) <= abs(ph["max_drawdown"]) and abs(ch["worst_day"]) <= abs(ph["worst_day"])
    severe_parent_dom = csev["return"] >= psev["return"] and abs(csev["max_drawdown"]) <= abs(psev["max_drawdown"]) and abs(csev["worst_day"]) <= abs(psev["worst_day"])

    out = {
        "study": "V99 R95 selective no-reallocation R88 expansion",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "preserve frozen R88 timing and 1.10 local scale, but add incremental exposure only to parent positions above the frozen R93 train-only absolute-target threshold; leave unused sleeve unused rather than concentrating it",
        "design": {
            "r88_strategy_r72_threshold": r88.STRATEGY_R72_THRESHOLD,
            "r88_scale": r88.SCALE,
            "allocation_feature": "abs(parent_r73_target)",
            "allocation_threshold": R93_ABS_TARGET_THRESHOLD,
            "allocation_threshold_source": "R93 first-60% train only",
            "allocation_rule": "eligible positions x1.10, ineligible positions unchanged; no reallocation",
            "new_fitted_parameters": 0,
        },
        "r73_parent": {"summary": ps, "holdout": ph, "severe": psev},
        "r88_growth_parent": {"summary": gs, "holdout": gh, "severe": gsev},
        "candidate": {"summary": cs, "holdout": ch, "severe": csev, "diagnostics": diag, "severe_diagnostics": sev_diag},
        "ratios": {
            "full_wealth_vs_r88": wealth_ratio(cs, gs),
            "holdout_wealth_vs_r88": wealth_ratio(ch, gh),
            "severe_wealth_vs_r88": wealth_ratio(csev, gsev),
            "full_wealth_vs_r73": wealth_ratio(cs, ps),
            "holdout_wealth_vs_r73": wealth_ratio(ch, ph),
            "severe_wealth_vs_r73": wealth_ratio(csev, psev),
            "full_dd_ratio_vs_r88": float(abs(cs["max_drawdown"]) / max(1e-12, abs(gs["max_drawdown"]))),
            "holdout_dd_ratio_vs_r88": float(abs(ch["max_drawdown"]) / max(1e-12, abs(gh["max_drawdown"]))),
            "severe_dd_ratio_vs_r88": float(abs(csev["max_drawdown"]) / max(1e-12, abs(gsev["max_drawdown"]))),
            "full_worst_ratio_vs_r88": float(abs(cs["worst_day"]) / max(1e-12, abs(gs["worst_day"]))),
        },
        "isolated": isolated,
        "parent_horizon_wins": wins_parent,
        "r88_horizon_wins": wins_r88,
        "alternative_horizons": alternative,
        "requested_parent_dimension_wins": parent_dims,
        "requested_r88_dimension_wins": r88_dims,
        "full_parent_dominance": bool(full_parent_dom),
        "holdout_parent_dominance": bool(hold_parent_dom),
        "severe_parent_dominance": bool(severe_parent_dom),
        "strict_r73_gate_passed": bool(full_parent_dom and hold_parent_dom and severe_parent_dom and parent_dims == 15),
        "disclosure": "Historical research only. R95 uses only the precommitted R93 train-selected threshold; no unused sleeve is reallocated and no new numeric parameter is fitted. R88 remains research growth parent until a challenger proves superior. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "r73": out["r73_parent"], "r88": out["r88_growth_parent"], "candidate": out["candidate"], "ratios": out["ratios"], "strict_r73": out["strict_r73_gate_passed"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
