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

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase13_crash_long_quality_audit.json"
EPS = 1e-12
HORIZON = 3
TRAIN_FOLDS = 4


def forward_sum_frame(frame: pd.DataFrame, hours: int) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=frame.index, columns=frame.columns)
    for k in range(1, hours + 1):
        out = out.add(frame.shift(-k), fill_value=0.0)
    return out


def net_asset_pnl(result) -> pd.DataFrame:
    return result.asset_gross.fillna(0.0) - result.asset_fees.fillna(0.0) - result.asset_funding.fillna(0.0)


def trim_top(values: np.ndarray, q: float = 0.99) -> float:
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return 0.0
    cutoff = np.quantile(values, q)
    use = values[values <= cutoff]
    return float(use.mean()) if len(use) else 0.0


def eval_rule(rule: pd.DataFrame, eligible: pd.DataFrame, future: pd.DataFrame, start, end):
    rowmask = (eligible.index >= start) & (eligible.index <= end)
    e = eligible.loc[rowmask]
    r = rule.loc[rowmask] & e
    f = future.loc[rowmask]
    vals = f.where(r).stack().dropna().to_numpy(dtype=float)
    base_vals = f.where(e).stack().dropna().to_numpy(dtype=float)
    selected = int(r.to_numpy().sum())
    total = int(e.to_numpy().sum())
    mean = float(vals.mean()) if len(vals) else 0.0
    median = float(np.median(vals)) if len(vals) else 0.0
    hit = float((vals > 0.0).mean()) if len(vals) else 0.0
    base_hit = float((base_vals > 0.0).mean()) if len(base_vals) else 0.0
    base_mean = float(base_vals.mean()) if len(base_vals) else 0.0
    return {
        "eligible_asset_hours": total,
        "selected_asset_hours": selected,
        "coverage": float(selected / total) if total else 0.0,
        "mean_future_net_pnl": mean,
        "median_future_net_pnl": median,
        "positive_rate": hit,
        "base_positive_rate": base_hit,
        "hit_lift": float(hit / base_hit) if base_hit > EPS else 0.0,
        "mean_lift": float(mean - base_mean),
        "mean_without_top1pct": trim_top(vals, 0.99),
    }


def fold_bounds(index, start, end):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo, hi = int(cuts[i]), int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    crash = p4.bear_high_vol_substates(data.close, direction, vol)["CRASH_CONTINUATION"]

    enable_short_veto, phase7_diag = p12.choose_short_veto(data, raw, ex, guard, gross, direction, vol, cost)
    _, f7_result, _, _, _ = p12.build_f7_core(data, raw, ex, guard, gross, cost, enable_short_veto)

    pos = f7_result.open_positions.fillna(0.0)
    pnl = net_asset_pnl(f7_result)
    future = forward_sum_frame(pnl, HORIZON)
    eligible = (pos > EPS).mul(crash.reindex(pos.index).fillna(False), axis=0)

    close = data.close.reindex(index=pos.index, columns=pos.columns).astype(float)
    # Predict t+1..t+3 using information available by t. No future values enter features.
    recent3 = pnl.rolling(3, min_periods=3).sum()
    recent6 = pnl.rolling(6, min_periods=6).sum()
    r3 = close.pct_change(3, fill_method=None)
    r6 = close.pct_change(6, fill_method=None)
    r24 = close.pct_change(24, fill_method=None)
    rel3 = r3.sub(r3.median(axis=1), axis=0)
    rel24 = r24.sub(r24.median(axis=1), axis=0)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None)
    rel_btc24 = r24.sub(btc24, axis=0)

    # Small, economically distinct rule menu. No numeric threshold grid.
    rules = {
        "recent3_pnl_positive": recent3 > 0.0,
        "recent6_pnl_positive": recent6 > 0.0,
        "price3_up": r3 > 0.0,
        "relative3_positive": rel3 > 0.0,
        "relative24_positive": rel24 > 0.0,
        "outperform_btc24": rel_btc24 > 0.0,
        "recent3_positive_and_relative3_positive": (recent3 > 0.0) & (rel3 > 0.0),
        "recent3_positive_and_relative24_positive": (recent3 > 0.0) & (rel24 > 0.0),
    }

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, end)
    hold_idx = pos.index[(pos.index > p1.TRAIN_END) & (pos.index <= end)]
    hold_start = hold_idx[0] if len(hold_idx) else end

    train = {n: eval_rule(r, eligible, future, start, train_end) for n, r in rules.items()}
    candidates = [
        (n, x) for n, x in train.items()
        if x["selected_asset_hours"] >= 200 and 0.10 <= x["coverage"] <= 0.90
    ]
    candidates.sort(
        key=lambda x: (
            x[1]["mean_without_top1pct"],
            x[1]["mean_lift"],
            x[1]["hit_lift"],
        ),
        reverse=True,
    )
    selected = candidates[0][0] if candidates else None

    holdout = {n: eval_rule(r, eligible, future, hold_start, end) for n, r in rules.items()}
    fold_rows = {}
    for i, (lo, hi) in enumerate(fold_bounds(pos.index, start, train_end), 1):
        fold_rows[str(i)] = {n: eval_rule(r, eligible, future, lo, hi) for n, r in rules.items()}

    sr_train = train.get(selected, {}) if selected else {}
    sr_hold = holdout.get(selected, {}) if selected else {}
    selected_folds = [fold_rows[k].get(selected, {}) for k in sorted(fold_rows)] if selected else []
    valid_folds = [r for r in selected_folds if r.get("selected_asset_hours", 0) >= 30]
    positive_folds = sum(
        int(
            r.get("mean_without_top1pct", 0.0) > 0.0
            and r.get("mean_lift", 0.0) > 0.0
            and r.get("hit_lift", 0.0) >= 1.0
        )
        for r in valid_folds
    )

    passed = bool(
        selected
        and sr_train.get("mean_without_top1pct", 0.0) > 0.0
        and sr_train.get("mean_lift", 0.0) > 0.0
        and sr_train.get("hit_lift", 0.0) > 1.0
        and len(valid_folds) >= 3
        and positive_folds >= 3
        and sr_hold.get("mean_without_top1pct", 0.0) > 0.0
        and sr_hold.get("mean_lift", 0.0) > 0.0
        and sr_hold.get("hit_lift", 0.0) >= 1.0
    )

    out = {
        "study": "V99 R106 phase 13 — crash-continuation long quality audit on F7 core",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "context": "F7-core LONG positions during causal CRASH_CONTINUATION after BHV short veto",
            "future_horizon_hours": HORIZON,
            "candidate_rules": list(rules),
            "no_numeric_threshold_grid": True,
            "selection_uses_train_only": True,
            "holdout_role": "validation only after train-selected rule is frozen",
            "tail_robustness": "positive selected mean after removing top 1% outcomes",
            "fold_gate": ">=3 eligible chronological train folds must have robust mean>0, mean lift>0 and hit lift>=1",
        },
        "phase7_short_veto_enabled": enable_short_veto,
        "phase7_side_train": phase7_diag,
        "selected_rule": selected,
        "selected_passed": passed,
        "train": train,
        "holdout": holdout,
        "folds": fold_rows,
        "selected_summary": {
            "train": sr_train,
            "holdout": sr_hold,
            "eligible_folds": len(valid_folds),
            "positive_folds": positive_folds,
        },
        "data": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "quarantined_symbols": quarantined,
        "metadata": metadata,
        "disclosure": "Diagnostic future-label study only. No strategy changes or real orders.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")
    print(json.dumps({
        "selected_rule": selected,
        "selected_passed": passed,
        "selected_summary": out["selected_summary"],
        "all_train": train,
        "all_holdout": holdout,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
