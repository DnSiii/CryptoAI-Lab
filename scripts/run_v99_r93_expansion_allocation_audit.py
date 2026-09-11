from __future__ import annotations

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
REPORT = PROJECT / "reports" / "v99_r93_expansion_allocation_audit.json"


def gate_stats(x: pd.DataFrame, feature: str, threshold: float, direction: str) -> dict:
    z = x[[feature, "future_contribution", "positive_label"]].dropna()
    if z.empty:
        return {"rows": 0, "selected": 0, "coverage": 0.0, "base_rate": 0.0, "selected_rate": 0.0, "lift": 0.0, "mean_contribution": 0.0, "median_contribution": 0.0}
    if direction == "high":
        g = z[feature] >= threshold
    else:
        g = z[feature] <= threshold
    y = z["positive_label"].astype(bool)
    base = float(y.mean())
    rate = float(y.loc[g].mean()) if g.any() else 0.0
    vals = z.loc[g, "future_contribution"] if g.any() else pd.Series(dtype=float)
    return {
        "rows": int(len(z)),
        "selected": int(g.sum()),
        "coverage": float(g.mean()),
        "base_rate": base,
        "selected_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
        "mean_contribution": float(vals.mean()) if len(vals) else 0.0,
        "median_contribution": float(vals.median()) if len(vals) else 0.0,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, parent_targets, protect, pdiag, _ = r88.r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gate_diag = r88.daily_gate(parent.equity)

    idx = parent_targets.index
    close = data.close.reindex(idx)
    targets = parent_targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    ema336 = close.ewm(span=336, adjust=False, min_periods=336).mean()
    fwd24 = close.shift(-24) / close - 1.0

    decision_positions = np.arange(0, len(idx), 24, dtype=int)
    rows = []
    for pos in decision_positions:
        if not bool(gate.iloc[pos]):
            continue
        ts = idx[pos]
        t = targets.iloc[pos]
        sgn = np.sign(t)
        active = t.abs() > 1e-12
        for sym in close.columns[active.to_numpy()]:
            tv = float(t[sym])
            px = float(close.at[ts, sym]) if pd.notna(close.at[ts, sym]) else np.nan
            e = float(ema336.at[ts, sym]) if pd.notna(ema336.at[ts, sym]) else np.nan
            mom24 = float(r24.at[ts, sym]) if pd.notna(r24.at[ts, sym]) else np.nan
            mom72 = float(r72.at[ts, sym]) if pd.notna(r72.at[ts, sym]) else np.nan
            fr = float(fwd24.at[ts, sym]) if pd.notna(fwd24.at[ts, sym]) else np.nan
            sign = float(np.sign(tv))
            future_contribution = float(abs(tv) * sign * fr) if np.isfinite(fr) else np.nan
            rows.append({
                "timestamp": ts,
                "symbol": sym,
                "target": tv,
                "abs_target": abs(tv),
                "signed_mom24": sign * mom24 if np.isfinite(mom24) else np.nan,
                "signed_mom72": sign * mom72 if np.isfinite(mom72) else np.nan,
                "signed_trend_distance": sign * (px / e - 1.0) if np.isfinite(px) and np.isfinite(e) and e != 0 else np.nan,
                "momentum_acceleration": sign * (mom24 - mom72 / 3.0) if np.isfinite(mom24) and np.isfinite(mom72) else np.nan,
                "future_contribution": future_contribution,
                "positive_label": bool(future_contribution > 0.0) if np.isfinite(future_contribution) else False,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No R88 expansion-position rows")
    df = df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
    unique_ts = pd.Index(sorted(df["timestamp"].drop_duplicates()))
    split = int(len(unique_ts) * 0.60)
    train_ts = unique_ts[:split]
    hold_ts = unique_ts[split:]
    train = df[df["timestamp"].isin(train_ts)].copy()
    hold = df[df["timestamp"].isin(hold_ts)].copy()

    features = ["signed_mom24", "signed_mom72", "signed_trend_distance", "momentum_acceleration", "abs_target"]
    candidates = []
    for feature in features:
        series = train[feature].dropna()
        if len(series) < 100:
            continue
        for direction, q in (("high", 0.80), ("low", 0.20)):
            threshold = float(series.quantile(q))
            tr = gate_stats(train, feature, threshold, direction)
            ho = gate_stats(hold, feature, threshold, direction)
            score = float(tr["lift"] * max(0.0, tr["mean_contribution"]) * np.sqrt(max(1, tr["selected"])))
            candidates.append({
                "feature": feature,
                "direction": direction,
                "threshold_train_only": threshold,
                "train": tr,
                "holdout": ho,
                "train_score": score,
            })

    candidates.sort(key=lambda z: (z["train_score"], z["train"]["lift"], z["train"]["mean_contribution"]), reverse=True)
    selected = candidates[0]

    fold_edges = np.linspace(0, len(unique_ts), 6, dtype=int)
    folds = []
    positive_mean_folds = 0
    positive_lift_folds = 0
    for i in range(5):
        ts_fold = unique_ts[fold_edges[i]:fold_edges[i+1]]
        block = df[df["timestamp"].isin(ts_fold)]
        s = gate_stats(block, selected["feature"], selected["threshold_train_only"], selected["direction"])
        if s["mean_contribution"] > 0:
            positive_mean_folds += 1
        if s["lift"] > 1.0:
            positive_lift_folds += 1
        folds.append({
            "fold": i + 1,
            "start": ts_fold[0].isoformat() if len(ts_fold) else None,
            "end": ts_fold[-1].isoformat() if len(ts_fold) else None,
            **s,
        })

    signal_pass = bool(
        selected["train"]["mean_contribution"] > 0
        and selected["holdout"]["mean_contribution"] > 0
        and selected["train"]["lift"] > 1.0
        and selected["holdout"]["lift"] > 1.0
        and positive_mean_folds >= 4
        and positive_lift_folds >= 4
    )

    out = {
        "study": "V99 R93 fresh allocation audit inside frozen R88 expansion episodes",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "within frozen R88 expansion episodes, identify on the first 60% one simple causal per-position state where incremental exposure has better next-24h directional contribution; validate unchanged on final 40% and five chronological folds before any allocation candidate exists",
        "r88_rule": {
            "strategy_r72_threshold": r88.STRATEGY_R72_THRESHOLD,
            "scale": r88.SCALE,
            "decision_cadence_hours": 24,
            "hold_hours": 24,
        },
        "label": "abs(parent_target) * sign(parent_target) * next-24h symbol return; future data is label only",
        "features": features,
        "daily_expansion_decisions": int(len(unique_ts)),
        "position_rows": int(len(df)),
        "train_decisions": int(len(train_ts)),
        "holdout_decisions": int(len(hold_ts)),
        "selection_policy": "five generic causal features; q20/q80 thresholds fit on first 60% expansion decisions only; one rule selected solely by train score; holdout/folds cannot change selection",
        "selected_train_only": selected,
        "selected_temporal_stability": {
            "folds": folds,
            "positive_mean_folds": int(positive_mean_folds),
            "positive_lift_folds": int(positive_lift_folds),
        },
        "allocation_signal_pass": signal_pass,
        "top_train_candidates": candidates[:10],
        "parent_diagnostics": pdiag,
        "gate_diagnostics": gate_diag,
        "disclosure": "Diagnostic historical research only. R93 does not alter R88 and does not reuse historical R28 thresholds. Future symbol returns appear only in labels; all features are available at decision time. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": selected, "stability": out["selected_temporal_stability"], "pass": signal_pass}, indent=2), flush=True)


if __name__ == "__main__":
    main()
