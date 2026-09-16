from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase12_bhv_state_conditioned_gate as p12
import run_v99_r106_phase18_blv_structure_router as p18

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase20_broad_long_position_quality_audit.json"
EPS = 1e-12
MIN_FOLD_ACTIVE_HOURS = 24 * 2
MIN_TRAIN_ACTIVE_HOURS = 24 * 10

BUCKETS = (
    "LEADER_ACCEL",
    "LEADER_DECEL",
    "LAGGARD_ACCEL",
    "LAGGARD_DECEL",
)


def causal_quality_buckets(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Fixed cross-sectional taxonomy, fully known at t-1.

    Leader/laggard uses the cross-sectional median split of 168h momentum.
    Acceleration/deceleration compares the 24h percentile rank with the 168h
    percentile rank. No fitted numeric thresholds and no holdout information.
    """
    r24 = close.pct_change(24, fill_method=None)
    r168 = close.pct_change(168, fill_method=None)
    rank24 = r24.rank(axis=1, pct=True, method="average").shift(1)
    rank168 = r168.rank(axis=1, pct=True, method="average").shift(1)

    valid = rank24.notna() & rank168.notna()
    leader = valid & rank168.ge(0.5)
    laggard = valid & rank168.lt(0.5)
    accel = valid & rank24.ge(rank168)
    decel = valid & rank24.lt(rank168)

    return {
        "LEADER_ACCEL": leader & accel,
        "LEADER_DECEL": leader & decel,
        "LAGGARD_ACCEL": laggard & accel,
        "LAGGARD_DECEL": laggard & decel,
    }


def isolated_long_bucket_targets(f7_targets: pd.DataFrame, broad: pd.Series, bucket: pd.DataFrame) -> pd.DataFrame:
    long_only = f7_targets.clip(lower=0.0)
    mask = bucket.reindex(index=f7_targets.index, columns=f7_targets.columns).fillna(False)
    mask = mask & broad.reindex(f7_targets.index).fillna(False).to_numpy()[:, None]
    return long_only.where(mask, 0.0)


def robust_mean_without_top1pct(equity: pd.Series, active: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    r = equity.pct_change(fill_method=None).fillna(0.0)
    window = pd.Series((r.index >= start) & (r.index <= end), index=r.index)
    use = active.reindex(r.index).fillna(False) & window
    values = r.loc[use].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return 0.0
    cutoff = np.quantile(values, 0.99)
    kept = values[values <= cutoff]
    return float(kept.mean()) if len(kept) else 0.0


def bucket_row(result, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    active = result.gross_exposure.gt(EPS)
    row = p4.segment_metrics(result.equity, active, start, end)
    row["robust_mean_without_top1pct"] = robust_mean_without_top1pct(result.equity, active, start, end)
    return row


def bucket_diagnostics(result, folds, train_start, train_end) -> dict:
    train = bucket_row(result, train_start, train_end)
    fold_rows = []
    valid = healthy = harmful = 0
    for i, (lo, hi) in enumerate(folds, 1):
        row = bucket_row(result, lo, hi)
        eligible = int(row["active_hours"]) >= MIN_FOLD_ACTIVE_HOURS
        good = bad = False
        if eligible:
            valid += 1
            good = bool(
                float(row["roi"]) > 0.0
                and float(row["profit_factor"]) > 1.0
                and float(row["robust_mean_without_top1pct"]) > 0.0
            )
            bad = bool(
                float(row["roi"]) < 0.0
                and float(row["profit_factor"]) < 1.0
                and float(row["robust_mean_without_top1pct"]) < 0.0
            )
            healthy += int(good)
            harmful += int(bad)
        fold_rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "eligible": eligible,
            "healthy": good,
            "harmful": bad,
            **row,
        })

    train_healthy = bool(
        int(train["active_hours"]) >= MIN_TRAIN_ACTIVE_HOURS
        and float(train["roi"]) > 0.0
        and float(train["profit_factor"]) > 1.0
        and float(train["robust_mean_without_top1pct"]) > 0.0
    )
    train_harmful = bool(
        int(train["active_hours"]) >= MIN_TRAIN_ACTIVE_HOURS
        and float(train["roi"]) < 0.0
        and float(train["profit_factor"]) < 1.0
        and float(train["robust_mean_without_top1pct"]) < 0.0
    )
    stable_healthy = bool(train_healthy and valid >= 3 and healthy >= 3)
    stable_harmful = bool(train_harmful and valid >= 3 and harmful >= 3)
    return {
        "train": train,
        "valid_folds": valid,
        "healthy_folds": healthy,
        "harmful_folds": harmful,
        "stable_healthy": stable_healthy,
        "stable_harmful": stable_harmful,
        "folds": fold_rows,
    }


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    direction, vol_state, _ = audit.classify_regimes(data.close)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    enable_bhv_veto, phase7_diag = p12.choose_short_veto(
        data, raw, ex, guard, gross, direction, vol_state, base_cost
    )
    f7_targets, f7_result, _, r98_diag, _ = p12.build_f7_core(
        data, raw, ex, guard, gross, base_cost, enable_bhv_veto
    )

    broad = p18.blv_substates(data.close, direction, vol_state)["BROAD_ADVANCE"]
    buckets = causal_quality_buckets(data.close.astype(float))
    folds = p4.fold_bounds(data.close.index, common_start, train_end)

    bucket_results = {}
    diagnostics = {}
    coverage_hours = {}
    for name in BUCKETS:
        target = isolated_long_bucket_targets(f7_targets, broad, buckets[name])
        result = p1.run_targets(data, target, ex, guard, base_cost, p1.GROSS_CAP)
        bucket_results[name] = result
        diagnostics[name] = bucket_diagnostics(result, folds, common_start, train_end)
        coverage_hours[name] = int(result.gross_exposure.gt(EPS).loc[common_start:train_end].sum())

    # Audit the complete long-only BROAD_ADVANCE book for reference.
    broad_long_targets = f7_targets.clip(lower=0.0).where(broad, 0.0)
    broad_long_result = p1.run_targets(data, broad_long_targets, ex, guard, base_cost, p1.GROSS_CAP)
    broad_long_diag = bucket_diagnostics(broad_long_result, folds, common_start, train_end)

    stable_harmful = [name for name, row in diagnostics.items() if row["stable_harmful"]]
    stable_healthy = [name for name, row in diagnostics.items() if row["stable_healthy"]]

    # Holdout is descriptive only. It never selects a bucket in phase20.
    holdout = {
        name: bucket_row(result, hold_start, common_end)
        for name, result in bucket_results.items()
    }
    broad_long_holdout = bucket_row(broad_long_result, hold_start, common_end)

    f7_analysis = audit.analyze_result(f7_result, data, direction, vol_state, common_start, common_end)
    broad_state_train = p18.state_row(f7_result, broad, common_start, train_end)
    broad_state_holdout = p18.state_row(f7_result, broad, hold_start, common_end)

    actionable = bool(stable_harmful and stable_healthy)
    out = {
        "study": "V99 R106 phase 20 — BROAD_ADVANCE F7 long-position quality audit",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "determine whether F7 long losses in causal BULL+LOW_VOL BROAD_ADVANCE are concentrated in a fixed cross-sectional position-quality class",
            "buckets": list(BUCKETS),
            "leader_definition": "168h cross-sectional percentile rank >= 0.5, using t-1 information",
            "laggard_definition": "168h cross-sectional percentile rank < 0.5, using t-1 information",
            "acceleration_definition": "24h percentile rank >= 168h percentile rank, using t-1 information",
            "deceleration_definition": "24h percentile rank < 168h percentile rank, using t-1 information",
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "no_numeric_threshold_grid": True,
            "features_causal_t_minus_1": True,
            "strategy_change_in_phase20": False,
            "stable_harmful_rule": "aggregate ROI<0/PF<1/tail-robust-mean<0 and >=3 harmful eligible train folds",
            "stable_healthy_rule": "aggregate ROI>0/PF>1/tail-robust-mean>0 and >=3 healthy eligible train folds",
            "next_candidate_allowed_only_if": "at least one stable harmful class and one stable healthy class coexist; otherwise no class veto is justified",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "phase7_short_veto_enabled": enable_bhv_veto,
        "phase7_side_train": phase7_diag,
        "broad_advance_f7": {
            "train": broad_state_train,
            "holdout": broad_state_holdout,
            "broad_long_reference_train": broad_long_diag,
            "broad_long_reference_holdout": broad_long_holdout,
        },
        "bucket_diagnostics": diagnostics,
        "bucket_holdout_descriptive_only": holdout,
        "stable_harmful_buckets": stable_harmful,
        "stable_healthy_buckets": stable_healthy,
        "actionable_for_next_phase": actionable,
        "coverage_hours_train": coverage_hours,
        "f7_global": f7_analysis["global"],
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "research_gate": {
            "accepted": False,
            "reason": "phase20 is diagnostic only; it cannot promote or alter the strategy",
        },
        "disclosure": "Historical research with chronological untouched holdout. Holdout is descriptive only in phase20. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "stable_harmful_buckets": stable_harmful,
        "stable_healthy_buckets": stable_healthy,
        "actionable_for_next_phase": actionable,
        "broad_long_reference_train": broad_long_diag,
        "bucket_train_summary": {
            name: {
                "train": row["train"],
                "valid_folds": row["valid_folds"],
                "healthy_folds": row["healthy_folds"],
                "harmful_folds": row["harmful_folds"],
                "stable_healthy": row["stable_healthy"],
                "stable_harmful": row["stable_harmful"],
            }
            for name, row in diagnostics.items()
        },
        "holdout_descriptive_only": holdout,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
