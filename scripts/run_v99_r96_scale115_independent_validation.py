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
r86 = r88.r86
cap = r88.cap

REPORT = PROJECT / "reports" / "candidate_v99_r96_scale115_independent_validation.json"
SCALE_PARENT = 1.10
SCALE_CANDIDATE = 1.15
PERTURB_SCALES = (1.125, 1.175)
RNG_SEED = 99096
WINDOW_DAYS = (30, 90, 180, 365)
SAMPLES_PER_DURATION = 10
FOLDS = 5
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
TRAIN_END = r88.TRAIN_END


def wealth_ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def risk_ratio(a: dict, b: dict, key: str) -> float:
    return float(abs(a[key]) / max(1e-12, abs(b[key])))


def apply_scale(data, ex, guard, cost, parent_targets: pd.DataFrame, gate: pd.Series, scale: float):
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * float(scale)
    targets = cap(targets, float(r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r86.P15["gross_cap"]), guard)
    return result, targets


def run_bundle(data, raw, ex, guard, gross, cost, scales=(SCALE_PARENT, SCALE_CANDIDATE)):
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    results = {}
    targets_by_scale = {}
    for scale in scales:
        result, targets = apply_scale(data, ex, guard, cost, parent_targets, gate, float(scale))
        results[str(scale)] = result
        targets_by_scale[str(scale)] = targets
    diag = {
        **pdiag,
        **gdiag,
        "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
        "gate_active_fraction": float(gate.mean()),
        "parent_mean_gross_when_scaled": float(parent_targets.abs().sum(axis=1).loc[gate].mean()) if gate.any() else 0.0,
    }
    return parent, results, targets_by_scale, diag


def eval_slice_pair(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    parent, results, _, _ = run_bundle(d, rr, ex, guard, gross, cost)
    c115 = r36.stats(results[str(SCALE_CANDIDATE)].equity)
    c110 = r36.stats(results[str(SCALE_PARENT)].equity)
    p = r36.stats(parent.equity)
    return c115, c110, p


def compare_stats(a: dict, b: dict) -> dict:
    return {
        "wealth_ratio": wealth_ratio(a, b),
        "return_win": bool(a["return"] >= b["return"]),
        "dd_ratio": risk_ratio(a, b, "max_drawdown"),
        "dd_win": bool(abs(a["max_drawdown"]) <= abs(b["max_drawdown"])),
        "worst_ratio": risk_ratio(a, b, "worst_day"),
        "worst_day_win": bool(abs(a["worst_day"]) <= abs(b["worst_day"])),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_severe_cost = float(severe_cost * 1.5)

    costs = {
        "base": base_cost,
        "severe": severe_cost,
        "super_severe_1p5x": super_severe_cost,
    }
    cost_results = {}
    for label, cost in costs.items():
        parent, results, _, diag = run_bundle(data, raw, ex, guard, gross, cost)
        s115 = r36.stats(results[str(SCALE_CANDIDATE)].equity)
        s110 = r36.stats(results[str(SCALE_PARENT)].equity)
        ps = r36.stats(parent.equity)
        cost_results[label] = {
            "scale_115": s115,
            "scale_110_r88": s110,
            "parent_r73": ps,
            "vs_r88": compare_stats(s115, s110),
            "vs_r73": compare_stats(s115, ps),
            "cost_per_side": float(cost),
            "diagnostics": diag,
        }
        del parent, results
        gc.collect()

    parent_base, base_results, _, base_diag = run_bundle(
        data, raw, ex, guard, gross, base_cost,
        scales=(SCALE_PARENT, SCALE_CANDIDATE, *PERTURB_SCALES),
    )
    base_115 = base_results[str(SCALE_CANDIDATE)]
    base_110 = base_results[str(SCALE_PARENT)]

    hold_idx = base_115.equity.index[base_115.equity.index > TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else base_115.equity.index[-1]
    hold115 = r36.stats(base_115.equity.loc[hold_start:])
    hold110 = r36.stats(base_110.equity.loc[hold_start:])
    hold_parent = r36.stats(parent_base.equity.loc[hold_start:])

    perturbation = {}
    for scale in PERTURB_SCALES:
        ss = r36.stats(base_results[str(scale)].equity)
        perturbation[str(scale)] = {
            "stats": ss,
            "vs_r88": compare_stats(ss, r36.stats(base_110.equity)),
        }

    common_end = data.close.index[-1]
    isolated = {}
    alternative = {}
    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        c115, c110, p = eval_slice_pair(data, raw, ex, guard, gross, base_cost, start, common_end)
        isolated[str(days)] = {
            "scale_115": c115,
            "scale_110_r88": c110,
            "parent_r73": p,
            "vs_r88": compare_stats(c115, c110),
            "vs_r73": compare_stats(c115, p),
        }
        gc.collect()

    for days in ALT_HORIZONS:
        start = common_end - pd.Timedelta(days=int(days))
        if start < data.close.index[0]:
            continue
        c115, c110, p = eval_slice_pair(data, raw, ex, guard, gross, base_cost, start, common_end)
        alternative[str(days)] = {
            "scale_115": c115,
            "scale_110_r88": c110,
            "parent_r73": p,
            "vs_r88": compare_stats(c115, c110),
            "vs_r73": compare_stats(c115, p),
        }
        gc.collect()

    idx = data.close.index
    rng = np.random.default_rng(RNG_SEED)
    random_windows = {}
    for days in WINDOW_DAYS:
        span = int(days) * 24
        valid_positions = np.arange(0, max(0, len(idx) - span - 1), 24, dtype=int)
        chosen = np.sort(rng.choice(valid_positions, size=min(SAMPLES_PER_DURATION, len(valid_positions)), replace=False)) if len(valid_positions) else []
        rows = []
        for pos in chosen:
            start = idx[int(pos)]
            end = idx[int(pos + span)]
            c115, c110, p = eval_slice_pair(data, raw, ex, guard, gross, base_cost, start, end)
            cmp = compare_stats(c115, c110)
            rows.append({
                "start": start.isoformat(),
                "end": end.isoformat(),
                "scale_115": c115,
                "scale_110_r88": c110,
                "parent_r73": p,
                "vs_r88": cmp,
            })
            gc.collect()
        wr = np.array([x["vs_r88"]["wealth_ratio"] for x in rows], dtype=float)
        random_windows[str(days)] = {
            "samples": int(len(rows)),
            "return_win_rate_vs_r88": float(np.mean([x["vs_r88"]["return_win"] for x in rows])) if rows else 0.0,
            "dd_win_rate_vs_r88": float(np.mean([x["vs_r88"]["dd_win"] for x in rows])) if rows else 0.0,
            "worst_day_win_rate_vs_r88": float(np.mean([x["vs_r88"]["worst_day_win"] for x in rows])) if rows else 0.0,
            "median_wealth_ratio_vs_r88": float(np.median(wr)) if len(wr) else 0.0,
            "p10_wealth_ratio_vs_r88": float(np.quantile(wr, 0.10)) if len(wr) else 0.0,
            "windows": rows,
        }

    n = len(idx)
    bounds = np.linspace(0, n, FOLDS + 1, dtype=int)
    chronological_folds = []
    for i in range(FOLDS):
        lo = int(bounds[i])
        hi = int(bounds[i + 1] - 1)
        if hi <= lo:
            continue
        start = idx[lo]
        end = idx[hi]
        c115, c110, p = eval_slice_pair(data, raw, ex, guard, gross, base_cost, start, end)
        chronological_folds.append({
            "fold": i + 1,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "scale_115": c115,
            "scale_110_r88": c110,
            "parent_r73": p,
            "vs_r88": compare_stats(c115, c110),
        })
        gc.collect()

    full_cmp = cost_results["base"]["vs_r88"]
    severe_cmp = cost_results["severe"]["vs_r88"]
    super_cmp = cost_results["super_severe_1p5x"]["vs_r88"]
    hold_cmp = compare_stats(hold115, hold110)

    perturb_pass = all(
        x["vs_r88"]["wealth_ratio"] > 1.0 and x["vs_r88"]["dd_ratio"] <= 1.05
        for x in perturbation.values()
    )
    main_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in isolated.values())
    alt_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in alternative.values())
    fold_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in chronological_folds)
    all_window_medians_positive = all(v["median_wealth_ratio_vs_r88"] > 1.0 for v in random_windows.values())
    short_window_consistency = all(v["return_win_rate_vs_r88"] >= 0.50 for v in random_windows.values())
    long_window_consistency = all(random_windows[str(d)]["return_win_rate_vs_r88"] >= 0.60 for d in (180, 365))

    gates = {
        "full_growth_pass": bool(full_cmp["wealth_ratio"] >= 1.03),
        "full_risk_pass": bool(full_cmp["dd_ratio"] <= 1.03 and full_cmp["worst_ratio"] <= 1.05),
        "holdout_pass": bool(hold_cmp["wealth_ratio"] > 1.0 and hold_cmp["dd_ratio"] <= 1.05),
        "severe_pass": bool(severe_cmp["wealth_ratio"] >= 1.02 and severe_cmp["dd_ratio"] <= 1.05),
        "super_severe_pass": bool(super_cmp["wealth_ratio"] > 1.0 and super_cmp["dd_ratio"] <= 1.07),
        "perturbation_plateau_pass": bool(perturb_pass),
        "main_horizon_pass": bool(main_return_wins >= 3),
        "alternative_horizon_pass": bool(alt_return_wins >= max(1, int(np.ceil(0.60 * len(alternative))))),
        "chronological_fold_pass": bool(fold_return_wins >= 4),
        "random_window_pass": bool(all_window_medians_positive and short_window_consistency and long_window_consistency),
    }
    gates["r96_growth_candidate_pass"] = bool(all(gates.values()))

    out = {
        "study": "V99 R96 precommitted 1.15 scale validation against frozen R88 1.10",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "test whether the R90-observed 1.15 local scale is a genuine growth improvement over frozen R88 1.10 rather than a full-path sensitivity artifact, using fixed scale, fresh deterministic isolated windows, chronological folds, multiple costs, horizon checks and local scale perturbations",
        "precommitment": {
            "threshold": r88.STRATEGY_R72_THRESHOLD,
            "r88_scale": SCALE_PARENT,
            "candidate_scale": SCALE_CANDIDATE,
            "perturbation_scales": list(PERTURB_SCALES),
            "scale_source": "R90 diagnostic sensitivity; selected before R96 execution",
            "new_market_data": False,
            "important_caveat": "R96 uses the same historical market dataset as prior research, so this is a fresh adversarial test battery, not a truly untouched future out-of-sample period.",
            "no_parameter_selection_inside_r96": True,
        },
        "cost_tests": cost_results,
        "holdout": {
            "start": hold_start.isoformat(),
            "scale_115": hold115,
            "scale_110_r88": hold110,
            "parent_r73": hold_parent,
            "vs_r88": hold_cmp,
        },
        "perturbation": perturbation,
        "isolated_horizons": isolated,
        "alternative_horizons": alternative,
        "random_isolated_windows": {
            "seed": RNG_SEED,
            "samples_per_duration": SAMPLES_PER_DURATION,
            "durations_days": list(WINDOW_DAYS),
            "results": random_windows,
        },
        "chronological_folds": chronological_folds,
        "summary_counts": {
            "main_horizon_return_wins_vs_r88": int(main_return_wins),
            "main_horizon_total": int(len(isolated)),
            "alternative_horizon_return_wins_vs_r88": int(alt_return_wins),
            "alternative_horizon_total": int(len(alternative)),
            "chronological_fold_return_wins_vs_r88": int(fold_return_wins),
            "chronological_fold_total": int(len(chronological_folds)),
        },
        "gates": gates,
        "diagnostics": base_diag,
        "disclosure": "Historical research only. R96 does not alter Frozen V99 or official paper. Passing R96 would justify a new research growth parent only; it would not guarantee future returns or authorize live trading.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "base_vs_r88": full_cmp,
        "holdout_vs_r88": hold_cmp,
        "severe_vs_r88": severe_cmp,
        "super_severe_vs_r88": super_cmp,
        "summary_counts": out["summary_counts"],
        "gates": gates,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
