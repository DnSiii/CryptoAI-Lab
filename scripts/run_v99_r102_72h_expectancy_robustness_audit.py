from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r101_position_winner_continuation_audit as r101

r98 = r101.r98
r36 = r101.r36
REPORT = PROJECT / "reports" / "v99_r102_72h_expectancy_robustness_audit.json"
R101_SIGNED72_THRESHOLD = 0.08569082521404564
HOLD_HOURS = (12, 24, 48, 72)
TRAIN_FRACTION = 0.60
FOLDS = 5


def remove_top_fraction(values: pd.Series, frac: float) -> pd.Series:
    z = values.dropna().sort_values()
    if not len(z):
        return z
    keep = max(1, int(np.floor(len(z) * (1.0 - frac))))
    return z.iloc[:keep]


def summary(values: pd.Series) -> dict:
    z = values.dropna().astype(float)
    top1 = remove_top_fraction(z, 0.01)
    top5 = remove_top_fraction(z, 0.05)
    return {
        "rows": int(len(z)),
        "mean": float(z.mean()) if len(z) else 0.0,
        "median": float(z.median()) if len(z) else 0.0,
        "positive_rate": float((z > 0.0).mean()) if len(z) else 0.0,
        "p10": float(z.quantile(0.10)) if len(z) else 0.0,
        "p90": float(z.quantile(0.90)) if len(z) else 0.0,
        "mean_without_top1pct": float(top1.mean()) if len(top1) else 0.0,
        "mean_without_top5pct": float(top5.mean()) if len(top5) else 0.0,
        "top1_removed": int(len(z) - len(top1)),
        "top5_removed": int(len(z) - len(top5)),
    }


def forward_net(data, side: pd.DataFrame, hold: int, cost: float) -> pd.DataFrame:
    opened = data.frames["open"].reindex(index=side.index, columns=side.columns)
    funding = data.funding.reindex(index=side.index, columns=side.columns).fillna(0.0)
    entry = opened.shift(-1)
    exit_ = opened.shift(-(hold + 1))
    price_ret = exit_.div(entry).sub(1.0)
    funding_forward = sum(funding.shift(-k) for k in range(2, hold + 2))
    return side * price_ret - 2.0 * cost - side * funding_forward


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    severe = float(ex["severe_cost_per_side"])
    super_severe = severe * 1.5

    targets, diag = r101.build_r98_targets(data, raw, ex, guard, gross, severe)
    close = data.close.reindex(index=targets.index, columns=targets.columns)
    side = np.sign(targets)
    signed72 = side * close.pct_change(72, fill_method=None)
    active = targets.abs().gt(1e-12)
    qualified = active & signed72.ge(R101_SIGNED72_THRESHOLD)

    sample_idx = targets.index[::24]
    dates = pd.Index(sample_idx)
    split = max(1, min(len(dates) - 1, int(len(dates) * TRAIN_FRACTION)))
    train_end = dates[split - 1]
    hold_start = dates[split]

    tests = {}
    for label, cost in (("severe", severe), ("super_severe_1p5x", super_severe)):
        tests[label] = {}
        for hold in HOLD_HOURS:
            net = forward_net(data, side, hold, cost)
            vals = net.where(qualified).reindex(sample_idx).stack().dropna()
            if len(vals):
                ts = vals.index.get_level_values(0)
                train_vals = vals.loc[ts <= train_end]
                hold_vals = vals.loc[ts >= hold_start]
            else:
                train_vals = vals
                hold_vals = vals
            tests[label][str(hold)] = {
                "cost_per_side": cost,
                "train": summary(train_vals),
                "holdout": summary(hold_vals),
            }

    # Temporal stability for the canonical 24h severe-cost label, with the R101
    # threshold frozen. No fold refits and no fold-specific selection.
    net24 = forward_net(data, side, 24, severe)
    vals24 = net24.where(qualified).reindex(sample_idx).stack().dropna()
    fold_edges = np.linspace(0, len(dates), FOLDS + 1, dtype=int)
    folds = []
    fold_mean_positive = fold_top1_positive = fold_top5_positive = 0
    for i in range(FOLDS):
        lo, hi = int(fold_edges[i]), int(fold_edges[i + 1])
        if hi <= lo:
            continue
        lo_ts, hi_ts = dates[lo], dates[hi - 1]
        ts = vals24.index.get_level_values(0)
        z = vals24.loc[(ts >= lo_ts) & (ts <= hi_ts)]
        s = summary(z)
        if s["rows"] >= 100 and s["mean"] > 0.0:
            fold_mean_positive += 1
        if s["rows"] >= 100 and s["mean_without_top1pct"] > 0.0:
            fold_top1_positive += 1
        if s["rows"] >= 100 and s["mean_without_top5pct"] > 0.0:
            fold_top5_positive += 1
        folds.append({"fold": i + 1, "start": lo_ts.isoformat(), "end": hi_ts.isoformat(), **s})

    severe_rows = tests["severe"]
    super_rows = tests["super_severe_1p5x"]
    severe_train_positive = sum(int(severe_rows[str(h)]["train"]["mean"] > 0.0) for h in HOLD_HOURS)
    severe_hold_positive = sum(int(severe_rows[str(h)]["holdout"]["mean"] > 0.0) for h in HOLD_HOURS)
    severe_train_top1_positive = sum(int(severe_rows[str(h)]["train"]["mean_without_top1pct"] > 0.0) for h in HOLD_HOURS)
    severe_hold_top1_positive = sum(int(severe_rows[str(h)]["holdout"]["mean_without_top1pct"] > 0.0) for h in HOLD_HOURS)
    severe_hold_top5_positive = sum(int(severe_rows[str(h)]["holdout"]["mean_without_top5pct"] > 0.0) for h in HOLD_HOURS)
    super_hold_positive = sum(int(super_rows[str(h)]["holdout"]["mean"] > 0.0) for h in HOLD_HOURS)
    super_hold_top1_positive = sum(int(super_rows[str(h)]["holdout"]["mean_without_top1pct"] > 0.0) for h in HOLD_HOURS)

    primary_hold = severe_rows["24"]["holdout"]
    passed = bool(
        severe_train_positive >= 3
        and severe_hold_positive >= 3
        and severe_train_top1_positive >= 3
        and severe_hold_top1_positive >= 3
        and severe_hold_top5_positive >= 2
        and super_hold_positive >= 3
        and super_hold_top1_positive >= 2
        and primary_hold["rows"] >= 300
        and primary_hold["mean"] > 0.0
        and fold_mean_positive >= 4
        and fold_top1_positive >= 4
        and fold_top5_positive >= 3
    )

    out = {
        "study": "V99 R102 frozen 72h-position expectancy robustness audit",
        "status": "DIAGNOSTIC_ONLY_NO_SLEEVE_PROMOTION",
        "objective": (
            "follow up the R101 observation that high 72h directional alignment had positive average expectancy despite a sub-50% hit rate; "
            "freeze the exact R101 train threshold and test whether expectancy survives multiple holding periods, severe/super-severe friction, "
            "chronological folds and removal of the largest 1-5% winners"
        ),
        "frozen_rule": {
            "feature": "requested-position signed trailing 72h return",
            "direction": "high",
            "threshold": R101_SIGNED72_THRESHOLD,
            "threshold_source": "R101 first-60% train q75; no refit in R102",
            "decision_cadence_hours": 24,
        },
        "sample_boundary": {
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "daily_decision_rows": int(len(sample_idx)),
            "qualified_fraction_all_hour_asset_cells": float(qualified.to_numpy(dtype=float).mean()),
        },
        "friction_tests": tests,
        "chronological_folds_24h_severe": folds,
        "summary_counts": {
            "severe_train_positive_horizons": severe_train_positive,
            "severe_holdout_positive_horizons": severe_hold_positive,
            "severe_train_positive_after_top1_removal": severe_train_top1_positive,
            "severe_holdout_positive_after_top1_removal": severe_hold_top1_positive,
            "severe_holdout_positive_after_top5_removal": severe_hold_top5_positive,
            "supersevere_holdout_positive_horizons": super_hold_positive,
            "supersevere_holdout_positive_after_top1_removal": super_hold_top1_positive,
            "fold_positive_mean": fold_mean_positive,
            "fold_positive_after_top1_removal": fold_top1_positive,
            "fold_positive_after_top5_removal": fold_top5_positive,
        },
        "expectancy_robustness_pass": passed,
        "next_candidate_policy": (
            "Only if pass=true may R103 build a segregated additive sleeve from this exact frozen 72h rule. "
            "R103 must not reduce or share the R98 core breaker and must face full portfolio-level validation."
        ),
        "r98_diagnostics": diag,
        "disclosure": (
            "Historical diagnostic only. R102 intentionally tests new robustness dimensions after R101 and does not claim a fresh untouched holdout. "
            "Passing only authorizes a segregated research-sleeve candidate; Frozen V99, Paper and R98 remain unchanged."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "rule": out["frozen_rule"],
        "counts": out["summary_counts"],
        "primary_24h_severe_holdout": primary_hold,
        "passed": passed,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
