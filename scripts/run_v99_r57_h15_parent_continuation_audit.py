from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55

r36 = r55.r36
REPORT = PROJECT / "reports" / "v99_r57_h15_parent_continuation_audit.json"
PARENT = {**r55.FIXED, "hedge_size": 0.15}
FEATURES = ("gross", "dominant_side_gross", "net_abs", "cross_section_vol_1h")
LABELS = ("deepen_7d_5pp", "deepen_14d_8pp")


def future_min(s: pd.Series, hours: int) -> pd.Series:
    return s.shift(-1).iloc[::-1].rolling(hours, min_periods=hours).min().iloc[::-1]


def frame_for(targets: pd.DataFrame, close: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    idx = targets.index.intersection(close.index).intersection(equity.index)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)
    eq = equity.reindex(idx).astype(float)
    peak = eq.cummax()
    current_dd = eq / peak - 1.0
    f7 = future_min(eq, 168) / peak - 1.0
    f14 = future_min(eq, 336) / peak - 1.0
    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    out = pd.DataFrame(index=idx)
    out["dd_depth"] = (-current_dd).clip(lower=0.0)
    out["gross"] = t.abs().sum(axis=1)
    out["dominant_side_gross"] = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    out["net_abs"] = t.sum(axis=1).abs()
    out["cross_section_vol_1h"] = c.pct_change(fill_method=None).std(axis=1).fillna(0.0)
    out["future_dd7"] = f7
    out["future_dd14"] = f14
    out["deepen_7d_5pp"] = f7 <= (current_dd - 0.05)
    out["deepen_14d_8pp"] = f14 <= (current_dd - 0.08)
    return out.dropna(subset=["future_dd7", "future_dd14"])


def auc(x: pd.Series, y: pd.Series) -> float:
    f = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if f.empty:
        return 0.5
    yy = f.y.astype(bool)
    n1, n0 = int(yy.sum()), int((~yy).sum())
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = f.x.rank(method="average")
    return float((ranks.loc[yy].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def threshold_rows(train: pd.DataFrame, hold: pd.DataFrame, feature: str, label: str):
    rows = []
    for q in (0.80, 0.90, 0.95):
        th = float(train[feature].quantile(q))
        row = {"quantile": q, "threshold": th}
        for name, sample in (("train", train), ("holdout", hold)):
            gate = sample[feature] >= th
            y = sample[label].astype(bool)
            base = float(y.mean()) if len(sample) else 0.0
            gated = float(sample.loc[gate, label].mean()) if gate.any() else 0.0
            row[name] = {
                "coverage": float(gate.mean()) if len(sample) else 0.0,
                "event_capture": float((gate & y).sum() / max(1, int(y.sum()))),
                "base_rate": base,
                "gated_rate": gated,
                "lift": float(gated / max(base, 1e-12)),
            }
        rows.append(row)
    return rows


def cohort_audit(frame: pd.DataFrame, train_end: pd.Timestamp, lo: float, hi: float):
    c = frame.loc[(frame.dd_depth >= lo) & (frame.dd_depth < hi)].copy()
    train = c.loc[c.index <= train_end]
    hold = c.loc[c.index > train_end]
    rankings, tests = {}, {}
    for label in LABELS:
        ranking = []
        for feature in FEATURES:
            tr_auc = auc(train[feature], train[label]) if len(train) else 0.5
            ho_auc = auc(hold[feature], hold[label]) if len(hold) else 0.5
            ranking.append({
                "feature": feature,
                "train_auc": tr_auc,
                "holdout_auc": ho_auc,
                "stable_auc": min(tr_auc, ho_auc),
                "mean_auc": (tr_auc + ho_auc) / 2.0,
            })
            tests[f"{label}:{feature}"] = threshold_rows(train, hold, feature, label)
        ranking.sort(key=lambda z: (z["stable_auc"], z["mean_auc"]), reverse=True)
        rankings[label] = ranking
    return {
        "depth_range": [lo, hi],
        "rows": int(len(c)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "event_rates": {
            label: {
                "train": float(train[label].mean()) if len(train) else 0.0,
                "holdout": float(hold[label].mean()) if len(hold) else 0.0,
            } for label in LABELS
        },
        "feature_rankings": rankings,
        "threshold_stability": tests,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    core = r36.run(data, raw, ex, cost, gross, guard)
    parent, _, targets, active = r55.build_with_shadow(
        data, raw, ex, guard, gross, cost, PARENT, shadow=core
    )
    frame = frame_for(targets, data.close, parent.equity)
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]
    cohorts = {
        "early_dd_5_to_12": cohort_audit(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": cohort_audit(frame, train_end, 0.08, 0.18),
        "deep_dd_12_to_24": cohort_audit(frame, train_end, 0.12, 0.24),
    }
    out = {
        "study": "V99 R57 h15 parent continuation audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "validate gross/dominant-side/net continuation signals directly on the R55 hedge-0.15 parent before designing a side-specific brake",
        "parent_fixed": PARENT,
        "parent_summary": r36.stats(parent.equity),
        "hedge_active_fraction": float(active.mean()),
        "train_end": train_end.isoformat(),
        "cohorts": cohorts,
        "disclosure": "Diagnostic only. Thresholds are learned on the first 60% of chronology and evaluated unchanged on the final 40%. Future prices are used only for labels.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
