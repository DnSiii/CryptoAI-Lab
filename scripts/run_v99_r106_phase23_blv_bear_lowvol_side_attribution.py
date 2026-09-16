from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r105_all_regime_structural_audit as audit
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase7_train_validated_bhv_short_veto as p7
import run_v99_r106_phase12_bhv_state_conditioned_gate as p12
import run_v99_r106_phase18_blv_structure_router as p18

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase23_bear_lowvol_side_attribution.json"
MIN_TRAIN_STATE_HOURS = 24 * 10
MIN_FOLD_STATE_HOURS = 24 * 2


def regime_mask(index: pd.DatetimeIndex, direction: pd.Series, vol_state: pd.Series) -> pd.Series:
    d = direction.shift(1).reindex(index).fillna("UNKNOWN")
    v = vol_state.shift(1).reindex(index).fillna("UNKNOWN")
    return (d.eq("BEAR") & v.eq("LOW_VOLATILITY")).fillna(False)


def side_diagnostics(result, state, folds, train_start, train_end) -> dict:
    train = p18.state_row(result, state, train_start, train_end)
    rows = []
    valid = healthy = harmful = 0
    for i, (lo, hi) in enumerate(folds, 1):
        row = p18.state_row(result, state, lo, hi)
        eligible = int(row["active_hours"]) >= MIN_FOLD_STATE_HOURS
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
        rows.append({
            "fold": i,
            "start": lo.isoformat(),
            "end": hi.isoformat(),
            "eligible": eligible,
            "healthy": good,
            "harmful": bad,
            **row,
        })

    train_healthy = bool(
        int(train["active_hours"]) >= MIN_TRAIN_STATE_HOURS
        and float(train["roi"]) > 0.0
        and float(train["profit_factor"]) > 1.0
        and float(train["robust_mean_without_top1pct"]) > 0.0
    )
    train_harmful = bool(
        int(train["active_hours"]) >= MIN_TRAIN_STATE_HOURS
        and float(train["roi"]) < 0.0
        and float(train["profit_factor"]) < 1.0
        and float(train["robust_mean_without_top1pct"]) < 0.0
    )
    return {
        "train": train,
        "valid_folds": valid,
        "healthy_folds": healthy,
        "harmful_folds": harmful,
        "stable_healthy": bool(train_healthy and valid >= 3 and healthy >= 3),
        "stable_harmful": bool(train_harmful and valid >= 3 and harmful >= 3),
        "folds": rows,
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

    state = regime_mask(data.close.index, direction, vol_state)
    long_targets = p7.isolated_side_targets(f7_targets, state, "long")
    short_targets = p7.isolated_side_targets(f7_targets, state, "short")
    long_result = p1.run_targets(data, long_targets, ex, guard, base_cost, p1.GROSS_CAP)
    short_result = p1.run_targets(data, short_targets, ex, guard, base_cost, p1.GROSS_CAP)

    folds = p4.fold_bounds(data.close.index, common_start, train_end)
    long_diag = side_diagnostics(long_result, state, folds, common_start, train_end)
    short_diag = side_diagnostics(short_result, state, folds, common_start, train_end)

    long_hold = p18.state_row(long_result, state, hold_start, common_end)
    short_hold = p18.state_row(short_result, state, hold_start, common_end)
    f7_train = p18.state_row(f7_result, state, common_start, train_end)
    f7_hold = p18.state_row(f7_result, state, hold_start, common_end)
    f7_full = p18.state_row(f7_result, state, common_start, common_end)

    actionable = bool(
        (long_diag["stable_healthy"] and short_diag["stable_harmful"])
        or (short_diag["stable_healthy"] and long_diag["stable_harmful"])
    )
    harmful_side = None
    healthy_side = None
    if long_diag["stable_harmful"] and short_diag["stable_healthy"]:
        harmful_side, healthy_side = "long", "short"
    elif short_diag["stable_harmful"] and long_diag["stable_healthy"]:
        harmful_side, healthy_side = "short", "long"

    out = {
        "study": "V99 R106 phase 23 — BEAR+LOW_VOL F7 long-vs-short attribution",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "objective": "determine whether BEAR+LOW_VOL F7 risk and weak quality are concentrated in one directional side",
            "sides": ["long", "short"],
            "selection_uses_train_only": True,
            "holdout_used_for_selection": False,
            "no_numeric_threshold_grid": True,
            "regime_features_causal_t_minus_1": True,
            "strategy_change_in_phase23": False,
            "stable_harmful_rule": "aggregate ROI<0/PF<1/tail-robust-mean<0 and >=3 harmful eligible train folds",
            "stable_healthy_rule": "aggregate ROI>0/PF>1/tail-robust-mean>0 and >=3 healthy eligible train folds",
            "next_candidate_allowed_only_if": "one side is stable harmful and the opposite side is stable healthy",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "phase7_short_veto_enabled": enable_bhv_veto,
        "phase7_side_train": phase7_diag,
        "bear_lowvol_f7": {"train": f7_train, "holdout": f7_hold, "full": f7_full},
        "long": long_diag,
        "short": short_diag,
        "holdout_descriptive_only": {"long": long_hold, "short": short_hold},
        "actionable_for_next_phase": actionable,
        "harmful_side": harmful_side,
        "healthy_side": healthy_side,
        "research_gate": {
            "accepted": False,
            "reason": "phase23 is diagnostic only; no strategy change is allowed",
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "r98_diagnostics": r98_diag,
        "disclosure": "Historical research with chronological untouched holdout. Holdout is descriptive only in phase23. No real orders. No profit guarantees.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n", encoding="utf-8")

    print(json.dumps({
        "bear_lowvol_f7": out["bear_lowvol_f7"],
        "long": {
            "train": long_diag["train"],
            "valid_folds": long_diag["valid_folds"],
            "healthy_folds": long_diag["healthy_folds"],
            "harmful_folds": long_diag["harmful_folds"],
            "stable_healthy": long_diag["stable_healthy"],
            "stable_harmful": long_diag["stable_harmful"],
        },
        "short": {
            "train": short_diag["train"],
            "valid_folds": short_diag["valid_folds"],
            "healthy_folds": short_diag["healthy_folds"],
            "harmful_folds": short_diag["harmful_folds"],
            "stable_healthy": short_diag["stable_healthy"],
            "stable_harmful": short_diag["stable_harmful"],
        },
        "holdout_descriptive_only": out["holdout_descriptive_only"],
        "actionable_for_next_phase": actionable,
        "harmful_side": harmful_side,
        "healthy_side": healthy_side,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
