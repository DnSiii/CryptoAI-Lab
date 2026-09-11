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
REPORT = PROJECT / "reports" / "candidate_v99_r98_friction_aware_hybrid.json"

R88_SCALE = 1.10
R96_SCALE = 1.15
R97_GROSS_THRESHOLD = 1.35
TRAIN_END = r88.TRAIN_END
HORIZONS = (7, 30, 90, 180, 365)
ALT_HORIZONS = (14, 21, 45, 60, 120, 240, 540)
WINDOW_DAYS = (30, 90, 180, 365)
SAMPLES_PER_DURATION = 10
RNG_SEED = 99098
FOLDS = 5


def wealth_ratio(a: dict, b: dict) -> float:
    return float((1.0 + a["return"]) / max(1e-12, 1.0 + b["return"]))


def compare(a: dict, b: dict) -> dict:
    return {
        "wealth_ratio": wealth_ratio(a, b),
        "return_win": bool(a["return"] >= b["return"]),
        "dd_ratio": float(abs(a["max_drawdown"]) / max(1e-12, abs(b["max_drawdown"]))),
        "dd_win": bool(abs(a["max_drawdown"]) <= abs(b["max_drawdown"])),
        "worst_ratio": float(abs(a["worst_day"]) / max(1e-12, abs(b["worst_day"]))),
        "worst_day_win": bool(abs(a["worst_day"]) <= abs(b["worst_day"])),
    }


def build_all(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    parent_gross = parent_targets.abs().sum(axis=1)
    high = gate & parent_gross.ge(R97_GROSS_THRESHOLD)

    t88 = parent_targets.copy()
    if gate.any():
        t88.loc[gate, :] = t88.loc[gate, :] * R88_SCALE
    t88 = cap(t88, float(r86.P15["gross_cap"]))

    t96 = parent_targets.copy()
    if gate.any():
        t96.loc[gate, :] = t96.loc[gate, :] * R96_SCALE
    t96 = cap(t96, float(r86.P15["gross_cap"]))

    t98 = parent_targets.copy()
    if gate.any():
        t98.loc[gate, :] = t98.loc[gate, :] * R88_SCALE
    if high.any():
        # Replace the 1.10 gate scaling with the frozen R97-qualified 1.15 scaling.
        t98.loc[high, :] = parent_targets.loc[high, :] * R96_SCALE
    t98 = cap(t98, float(r86.P15["gross_cap"]))

    r73 = parent
    r88res = r36.run(data, t88, ex, cost, float(r86.P15["gross_cap"]), guard)
    r96res = r36.run(data, t96, ex, cost, float(r86.P15["gross_cap"]), guard)
    r98res = r36.run(data, t98, ex, cost, float(r86.P15["gross_cap"]), guard)

    diag = {
        **pdiag,
        **gdiag,
        "r88_scale": R88_SCALE,
        "qualified_scale": R96_SCALE,
        "r97_gross_threshold": R97_GROSS_THRESHOLD,
        "r97_rule": "gate active AND parent gross_current >= 1.35",
        "r88_gate_fraction": float(gate.mean()),
        "qualified_high_fraction_all_rows": float(high.mean()),
        "qualified_fraction_within_gate": float(high.sum() / max(1, gate.sum())),
        "protect_overlap_high_fraction": float((high & protect.reindex(high.index).fillna(False)).mean()),
        "turnover_delta_r98_vs_r88": float(r98res.turnover.sum() - r88res.turnover.sum()),
        "turnover_delta_r98_vs_r96": float(r98res.turnover.sum() - r96res.turnover.sum()),
        "turnover_delta_r98_vs_r73": float(r98res.turnover.sum() - r73.turnover.sum()),
    }
    return r98res, r88res, r96res, r73, diag


def eval_slice(data, raw, ex, guard, gross, cost, start, end):
    d = r36.sdata(data, start, end)
    rr = raw.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    a, b, c, p, _ = build_all(d, rr, ex, guard, gross, cost)
    return r36.stats(a.equity), r36.stats(b.equity), r36.stats(c.equity), r36.stats(p.equity)


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = float(severe_cost * 1.5)

    cost_tests = {}
    base_objects = None
    for label, cost in (("base", base_cost), ("severe", severe_cost), ("super_severe_1p5x", super_cost)):
        r98res, r88res, r96res, r73res, diag = build_all(data, raw, ex, guard, gross, cost)
        s98 = r36.stats(r98res.equity)
        s88 = r36.stats(r88res.equity)
        s96 = r36.stats(r96res.equity)
        s73 = r36.stats(r73res.equity)
        cost_tests[label] = {
            "r98": s98,
            "r88": s88,
            "r96": s96,
            "r73": s73,
            "vs_r88": compare(s98, s88),
            "vs_r96": compare(s98, s96),
            "vs_r73": compare(s98, s73),
            "cost_per_side": cost,
            "diagnostics": diag,
        }
        if label == "base":
            base_objects = (r98res, r88res, r96res, r73res, diag)
        else:
            del r98res, r88res, r96res, r73res
        gc.collect()

    r98base, r88base, r96base, r73base, base_diag = base_objects
    hold_idx = r98base.equity.index[r98base.equity.index > TRAIN_END]
    hold_start = hold_idx[0] if len(hold_idx) else r98base.equity.index[-1]
    h98 = r36.stats(r98base.equity.loc[hold_start:])
    h88 = r36.stats(r88base.equity.loc[hold_start:])
    h96 = r36.stats(r96base.equity.loc[hold_start:])
    h73 = r36.stats(r73base.equity.loc[hold_start:])
    holdout = {
        "start": hold_start.isoformat(),
        "r98": h98,
        "r88": h88,
        "r96": h96,
        "r73": h73,
        "vs_r88": compare(h98, h88),
        "vs_r96": compare(h98, h96),
        "vs_r73": compare(h98, h73),
    }

    end = data.close.index[-1]
    isolated, alternative = {}, {}
    for days in HORIZONS:
        start = end - pd.Timedelta(days=int(days))
        s98, s88, s96, s73 = eval_slice(data, raw, ex, guard, gross, base_cost, start, end)
        isolated[str(days)] = {
            "r98": s98, "r88": s88, "r96": s96, "r73": s73,
            "vs_r88": compare(s98, s88), "vs_r96": compare(s98, s96), "vs_r73": compare(s98, s73),
        }
        gc.collect()
    for days in ALT_HORIZONS:
        start = end - pd.Timedelta(days=int(days))
        if start < data.close.index[0]:
            continue
        s98, s88, s96, s73 = eval_slice(data, raw, ex, guard, gross, base_cost, start, end)
        alternative[str(days)] = {
            "r98": s98, "r88": s88, "r96": s96, "r73": s73,
            "vs_r88": compare(s98, s88), "vs_r96": compare(s98, s96), "vs_r73": compare(s98, s73),
        }
        gc.collect()

    idx = data.close.index
    rng = np.random.default_rng(RNG_SEED)
    random_windows = {}
    for days in WINDOW_DAYS:
        span = int(days) * 24
        valid = np.arange(72, max(73, len(idx) - span - 1), 24, dtype=int)
        chosen = np.sort(rng.choice(valid, size=min(SAMPLES_PER_DURATION, len(valid)), replace=False)) if len(valid) else []
        rows = []
        for pos in chosen:
            start, stop = idx[int(pos)], idx[int(pos + span)]
            s98, s88, s96, s73 = eval_slice(data, raw, ex, guard, gross, base_cost, start, stop)
            rows.append({
                "start": start.isoformat(), "end": stop.isoformat(),
                "r98": s98, "r88": s88, "r96": s96, "r73": s73,
                "vs_r88": compare(s98, s88), "vs_r96": compare(s98, s96),
            })
            gc.collect()
        wr = np.array([x["vs_r88"]["wealth_ratio"] for x in rows], dtype=float)
        random_windows[str(days)] = {
            "samples": len(rows),
            "return_win_rate_vs_r88": float(np.mean([x["vs_r88"]["return_win"] for x in rows])) if rows else 0.0,
            "dd_win_rate_vs_r88": float(np.mean([x["vs_r88"]["dd_win"] for x in rows])) if rows else 0.0,
            "median_wealth_ratio_vs_r88": float(np.median(wr)) if len(wr) else 0.0,
            "p10_wealth_ratio_vs_r88": float(np.quantile(wr, 0.10)) if len(wr) else 0.0,
            "windows": rows,
        }

    bounds = np.linspace(0, len(idx), FOLDS + 1, dtype=int)
    folds = []
    for i in range(FOLDS):
        lo, hi = int(bounds[i]), int(bounds[i + 1] - 1)
        if hi <= lo:
            continue
        start, stop = idx[lo], idx[hi]
        s98, s88, s96, s73 = eval_slice(data, raw, ex, guard, gross, base_cost, start, stop)
        folds.append({
            "fold": i + 1, "start": start.isoformat(), "end": stop.isoformat(),
            "r98": s98, "r88": s88, "r96": s96, "r73": s73,
            "vs_r88": compare(s98, s88), "vs_r96": compare(s98, s96),
        })
        gc.collect()

    base_cmp = cost_tests["base"]["vs_r88"]
    sev_cmp = cost_tests["severe"]["vs_r88"]
    super_cmp = cost_tests["super_severe_1p5x"]["vs_r88"]
    hold_cmp = holdout["vs_r88"]
    main_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in isolated.values())
    alt_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in alternative.values())
    fold_return_wins = sum(int(v["vs_r88"]["return_win"]) for v in folds)
    medians_positive = all(v["median_wealth_ratio_vs_r88"] >= 1.0 for v in random_windows.values())
    short_consistency = all(v["return_win_rate_vs_r88"] >= 0.50 for v in random_windows.values())
    long_consistency = all(random_windows[str(d)]["return_win_rate_vs_r88"] >= 0.60 for d in (180, 365))

    # Predeclared promotion gate: meaningful growth, no material cost/tail regression, and broad consistency.
    gates = {
        "full_growth_pass": bool(base_cmp["wealth_ratio"] >= 1.02),
        "full_risk_pass": bool(base_cmp["dd_ratio"] <= 1.02 and base_cmp["worst_ratio"] <= 1.03),
        "holdout_pass": bool(hold_cmp["wealth_ratio"] >= 1.01 and hold_cmp["dd_ratio"] <= 1.03),
        "severe_pass": bool(sev_cmp["wealth_ratio"] >= 1.0 and sev_cmp["dd_ratio"] <= 1.03),
        "super_severe_pass": bool(super_cmp["wealth_ratio"] >= 0.99 and super_cmp["dd_ratio"] <= 1.04),
        "main_horizon_pass": bool(main_return_wins >= 3),
        "alternative_horizon_pass": bool(alt_return_wins >= max(1, int(np.ceil(0.60 * len(alternative))))),
        "chronological_fold_pass": bool(fold_return_wins >= 4),
        "random_window_pass": bool(medians_positive and short_consistency and long_consistency),
    }
    gates["r98_growth_candidate_pass"] = bool(all(gates.values()))

    r96_base_wr = cost_tests["base"]["vs_r96"]["wealth_ratio"]
    r96_sev_wr = cost_tests["severe"]["vs_r96"]["wealth_ratio"]
    out = {
        "study": "V99 R98 friction-aware hybrid: R88 1.10 floor plus frozen R97-qualified 1.15",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "retain the validated R88 1.10 expansion whenever its gate is active, and elevate only the R97 severe-cost-qualified high-gross states to 1.15, attempting to preserve R96 growth while recovering cost and random-window robustness",
        "precommitment": {
            "r88_threshold": r88.STRATEGY_R72_THRESHOLD,
            "r88_scale": R88_SCALE,
            "qualified_scale": R96_SCALE,
            "r97_feature": "parent gross_current",
            "r97_direction": "high",
            "r97_threshold": R97_GROSS_THRESHOLD,
            "r97_threshold_source": "R97 first-60% train-only q80; holdout positive; 4/5 positive mean/lift folds",
            "no_refit_inside_r98": True,
        },
        "cost_tests": cost_tests,
        "holdout": holdout,
        "isolated_horizons": isolated,
        "alternative_horizons": alternative,
        "random_isolated_windows": {"seed": RNG_SEED, "samples_per_duration": SAMPLES_PER_DURATION, "results": random_windows},
        "chronological_folds": folds,
        "summary_counts": {
            "main_horizon_return_wins_vs_r88": main_return_wins,
            "main_horizon_total": len(isolated),
            "alternative_horizon_return_wins_vs_r88": alt_return_wins,
            "alternative_horizon_total": len(alternative),
            "chronological_fold_return_wins_vs_r88": fold_return_wins,
            "chronological_fold_total": len(folds),
        },
        "diagnostics": base_diag,
        "r98_vs_r96_context": {
            "base_wealth_ratio": r96_base_wr,
            "severe_wealth_ratio": r96_sev_wr,
            "interpretation": "R98 is not required to beat R96 nominally; it must beat R88 robustly while materially recovering R96's cost failure.",
        },
        "gates": gates,
        "disclosure": "Historical research only. Passing creates a research growth parent, not a guarantee of future returns and not authorization for live trading. Frozen V99/Paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "base_vs_r88": base_cmp,
        "holdout_vs_r88": hold_cmp,
        "severe_vs_r88": sev_cmp,
        "super_severe_vs_r88": super_cmp,
        "vs_r96_context": out["r98_vs_r96_context"],
        "summary_counts": out["summary_counts"],
        "random_window_summary": {k: {kk: vv for kk, vv in v.items() if kk != "windows"} for k, v in random_windows.items()},
        "gates": gates,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
