from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r98_friction_aware_hybrid as r98

r36 = r98.r36
r86 = r98.r86
r88 = r98.r88
cap = r98.cap
REPORT = PROJECT / "reports" / "v99_r101_position_winner_continuation_audit.json"
TRAIN_FRACTION = 0.60
FOLDS = 5
HOLD_HOURS = 24
FEATURE_Q = 0.75


def build_r98_targets(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(
        data, raw, ex, guard, gross, cost
    )
    gate, gdiag = r88.daily_gate(parent.equity)
    parent_gross = parent_targets.abs().sum(axis=1)
    high = gate & parent_gross.ge(r98.R97_GROSS_THRESHOLD)

    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = parent_targets.loc[gate, :] * r98.R88_SCALE
    if high.any():
        targets.loc[high, :] = parent_targets.loc[high, :] * r98.R96_SCALE
    targets = cap(targets, float(r86.P15["gross_cap"]))
    diag = {
        **pdiag,
        **gdiag,
        "gate_fraction": float(gate.mean()),
        "qualified_high_fraction": float(high.mean()),
    }
    return targets, diag


def metric(frame: pd.DataFrame, mask: pd.Series) -> dict:
    selected = frame.loc[mask]
    base_pos = float((frame["net24"] > 0.0).mean()) if len(frame) else 0.0
    selected_pos = float((selected["net24"] > 0.0).mean()) if len(selected) else 0.0
    base_mean = float(frame["net24"].mean()) if len(frame) else 0.0
    selected_mean = float(selected["net24"].mean()) if len(selected) else 0.0
    return {
        "rows": int(len(frame)),
        "selected": int(len(selected)),
        "coverage": float(len(selected) / max(1, len(frame))),
        "base_positive_rate": base_pos,
        "selected_positive_rate": selected_pos,
        "lift": float(selected_pos / max(1e-12, base_pos)) if base_pos > 0 else 0.0,
        "base_mean_net24": base_mean,
        "selected_mean_net24": selected_mean,
        "mean_edge_vs_base": float(selected_mean - base_mean),
        "selected_median_net24": float(selected["net24"].median()) if len(selected) else 0.0,
        "selected_p10_net24": float(selected["net24"].quantile(0.10)) if len(selected) else 0.0,
        "selected_p90_net24": float(selected["net24"].quantile(0.90)) if len(selected) else 0.0,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    severe_cost = float(ex["severe_cost_per_side"])
    targets, diag = build_r98_targets(data, raw, ex, guard, gross, severe_cost)

    close = data.close.reindex(index=targets.index, columns=targets.columns)
    opened = data.frames["open"].reindex(index=targets.index, columns=targets.columns)
    funding = data.funding.reindex(index=targets.index, columns=targets.columns).fillna(0.0)

    side = np.sign(targets)
    ret24 = close.pct_change(24, fill_method=None)
    ret72 = close.pct_change(72, fill_method=None)
    signed24 = side * ret24
    signed72 = side * ret72
    persistent24 = (
        (side == side.shift(24))
        & side.ne(0.0)
        & side.shift(24).ne(0.0)
    )

    # Separate 24h sleeve label: signal at close t -> entry open t+1 -> exit open t+25.
    # It pays two severe transaction charges and all funding debits/credits incurred
    # while the sleeve is held. This is an alpha diagnostic, not a portfolio replay.
    entry = opened.shift(-1)
    exit_ = opened.shift(-(HOLD_HOURS + 1))
    price_ret = exit_.div(entry).sub(1.0)
    funding_forward = sum(funding.shift(-k) for k in range(2, HOLD_HOURS + 2))
    net24 = side * price_ret - (2.0 * severe_cost) - side * funding_forward

    sample_idx = targets.index[::24]
    active = targets.abs().gt(1e-12)
    records = []
    for ts in sample_idx:
        row_active = active.loc[ts]
        if not row_active.any():
            continue
        syms = row_active.index[row_active.to_numpy()]
        z = pd.DataFrame({
            "timestamp": ts,
            "symbol": syms,
            "signed24": signed24.loc[ts, syms].to_numpy(dtype=float),
            "signed72": signed72.loc[ts, syms].to_numpy(dtype=float),
            "persistent24": persistent24.loc[ts, syms].to_numpy(dtype=bool),
            "net24": net24.loc[ts, syms].to_numpy(dtype=float),
        })
        records.append(z)
    frame = pd.concat(records, ignore_index=True) if records else pd.DataFrame()
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["timestamp", "symbol"])
    if len(frame) < 2000:
        raise RuntimeError("Insufficient active-position observations for R101")

    dates = pd.Index(frame["timestamp"].drop_duplicates().sort_values())
    split = max(1, min(len(dates) - 1, int(len(dates) * TRAIN_FRACTION)))
    train_end = dates[split - 1]
    hold_start = dates[split]
    train = frame.loc[frame["timestamp"] <= train_end].copy()
    hold = frame.loc[frame["timestamp"] >= hold_start].copy()

    q24 = float(train["signed24"].quantile(FEATURE_Q))
    q72 = float(train["signed72"].quantile(FEATURE_Q))
    specs = (
        {"name": "signed24_high", "kind": "s24"},
        {"name": "signed72_high", "kind": "s72"},
        {"name": "joint_signed24_72_high", "kind": "joint"},
        {"name": "signed24_high_persistent_request", "kind": "s24_persist"},
    )

    def mask_for(df: pd.DataFrame, kind: str) -> pd.Series:
        if kind == "s24":
            return df["signed24"] >= q24
        if kind == "s72":
            return df["signed72"] >= q72
        if kind == "joint":
            return (df["signed24"] >= q24) & (df["signed72"] >= q72)
        if kind == "s24_persist":
            return (df["signed24"] >= q24) & df["persistent24"]
        raise KeyError(kind)

    candidates = []
    for spec in specs:
        tm = mask_for(train, spec["kind"])
        hm = mask_for(hold, spec["kind"])
        ts = metric(train, tm)
        hs = metric(hold, hm)
        if ts["selected"] < 500:
            continue
        score = float(
            ts["selected_mean_net24"] * np.sqrt(max(0.0, ts["coverage"]))
            + 0.00025 * max(0.0, ts["lift"] - 1.0)
            + 0.25 * max(0.0, ts["mean_edge_vs_base"])
        )
        candidates.append({
            **spec,
            "train": ts,
            "holdout": hs,
            "train_score": score,
        })

    eligible = [
        x for x in candidates
        if x["train"]["selected_mean_net24"] > 0.0
        and x["train"]["mean_edge_vs_base"] > 0.0
        and x["train"]["lift"] > 1.05
    ]
    eligible.sort(key=lambda x: x["train_score"], reverse=True)
    selected = eligible[0] if eligible else None

    folds = []
    positive_mean = positive_edge = positive_lift = 0
    if selected:
        edges = np.linspace(0, len(dates), FOLDS + 1, dtype=int)
        for i in range(FOLDS):
            lo, hi = int(edges[i]), int(edges[i + 1])
            if hi <= lo:
                continue
            lo_ts, hi_ts = dates[lo], dates[hi - 1]
            z = frame.loc[(frame["timestamp"] >= lo_ts) & (frame["timestamp"] <= hi_ts)].copy()
            m = mask_for(z, selected["kind"])
            s = metric(z, m)
            if s["selected"] >= 150 and s["selected_mean_net24"] > 0.0:
                positive_mean += 1
            if s["selected"] >= 150 and s["mean_edge_vs_base"] > 0.0:
                positive_edge += 1
            if s["selected"] >= 150 and s["lift"] > 1.0:
                positive_lift += 1
            folds.append({
                "fold": i + 1,
                "start": lo_ts.isoformat(),
                "end": hi_ts.isoformat(),
                **s,
            })

    passed = bool(
        selected
        and selected["train"]["coverage"] >= 0.05
        and selected["holdout"]["coverage"] >= 0.05
        and selected["holdout"]["selected"] >= 300
        and selected["holdout"]["selected_mean_net24"] > 0.0
        and selected["holdout"]["mean_edge_vs_base"] > 0.0
        and selected["holdout"]["selected_median_net24"] > 0.0
        and selected["holdout"]["lift"] > 1.05
        and positive_mean >= 4
        and positive_edge >= 4
        and positive_lift >= 4
    )

    out = {
        "study": "V99 R101 position-level winner continuation audit on R98",
        "status": "DIAGNOSTIC_ONLY_NO_PORTFOLIO_CANDIDATE_PROMOTION",
        "objective": (
            "test whether currently requested R98 positions that are already moving with their requested direction "
            "retain positive next-24h continuation alpha after two severe transaction charges and modeled funding; "
            "the purpose is to justify a future segregated additive winner sleeve without cutting or braking the R98 core"
        ),
        "label": {
            "decision": "close t",
            "entry": "open t+1",
            "exit": f"open t+{HOLD_HOURS + 1}",
            "hold_hours": HOLD_HOURS,
            "transaction_cost_per_side": severe_cost,
            "roundtrip_transaction_cost": 2.0 * severe_cost,
            "funding_window": "opens t+2 through t+25; signed by requested position side",
            "portfolio_breaker_not_applied_to_label": True,
            "reason": "R101 measures sleeve alpha independently before any portfolio architecture is allowed",
        },
        "r98_signal_boundary": {
            "r88_scale": r98.R88_SCALE,
            "qualified_scale": r98.R96_SCALE,
            "qualified_parent_gross_threshold": r98.R97_GROSS_THRESHOLD,
            "targets_built_under_severe_cost": True,
            "diagnostics": diag,
        },
        "sample": {
            "daily_active_position_rows": int(len(frame)),
            "unique_daily_timestamps": int(len(dates)),
            "train_rows": int(len(train)),
            "holdout_rows": int(len(hold)),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
        },
        "precommitment": {
            "feature_quantile": FEATURE_Q,
            "signed24_threshold_train_only": q24,
            "signed72_threshold_train_only": q72,
            "rules": list(specs),
            "one_rule_selected_by_train_only": True,
            "holdout_and_folds_cannot_change_rule_or_thresholds": True,
            "no_low_direction_search": True,
            "no_symbol_specific_thresholds": True,
        },
        "all_predeclared_candidates": candidates,
        "selected_train_only": selected,
        "temporal_stability": {
            "folds": folds,
            "positive_mean_folds": positive_mean,
            "positive_edge_vs_base_folds": positive_edge,
            "positive_lift_folds": positive_lift,
        },
        "winner_continuation_signal_pass": passed,
        "next_candidate_policy": (
            "Only if pass=true may R102 create a segregated additive sleeve using exactly the frozen R101 rule. "
            "R102 must preserve the R98 core and face full base/severe/super-severe, holdout, isolated-horizon, "
            "chronological-fold and random-window validation before any research-parent promotion."
        ),
        "disclosure": (
            "Historical diagnostic only. R101 is not a portfolio backtest and does not alter Frozen V99, Paper, or R98. "
            "A positive signal only authorizes construction of a separately validated research sleeve."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "sample": out["sample"],
        "thresholds": {"signed24": q24, "signed72": q72},
        "selected": selected,
        "folds_positive_mean": positive_mean,
        "folds_positive_edge": positive_edge,
        "folds_positive_lift": positive_lift,
        "passed": passed,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
