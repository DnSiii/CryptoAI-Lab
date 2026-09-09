from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r54_aggressive_parent_mild_crash as r54

r36 = r54.r36
REPORT = PROJECT / "reports" / "v99_r56_aggressive_parent_continuation_audit.json"
FEATURES = ("gross", "dominant_side_gross", "net_abs", "cross_section_vol_1h")
LABELS = ("deepen_7d_5pp", "deepen_14d_8pp")


def future_min(series: pd.Series, hours: int) -> pd.Series:
    shifted = series.shift(-1)
    return shifted.iloc[::-1].rolling(hours, min_periods=hours).min().iloc[::-1]


def build_frame(targets: pd.DataFrame, close: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    idx = targets.index.intersection(close.index).intersection(equity.index)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)
    eq = equity.reindex(idx).astype(float)

    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    gross = t.abs().sum(axis=1)
    net_abs = t.sum(axis=1).abs()

    peak = eq.cummax()
    current_dd = eq / peak - 1.0
    min7 = future_min(eq, 168)
    min14 = future_min(eq, 336)
    future_dd7 = min7 / peak - 1.0
    future_dd14 = min14 / peak - 1.0

    frame = pd.DataFrame(index=idx)
    frame["dd_depth"] = (-current_dd).clip(lower=0.0)
    frame["gross"] = gross
    frame["dominant_side_gross"] = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    frame["net_abs"] = net_abs
    frame["cross_section_vol_1h"] = c.pct_change(fill_method=None).std(axis=1).fillna(0.0)
    frame["future_dd7"] = future_dd7
    frame["future_dd14"] = future_dd14
    frame["deepen_7d_5pp"] = future_dd7 <= (current_dd - 0.05)
    frame["deepen_14d_8pp"] = future_dd14 <= (current_dd - 0.08)
    return frame.dropna(subset=["future_dd7", "future_dd14"])


def auc(feature: pd.Series, label: pd.Series) -> float:
    f = pd.concat([feature.rename("x"), label.rename("y")], axis=1).dropna()
    if f.empty:
        return 0.5
    y = f["y"].astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = f["x"].rank(method="average")
    return float((ranks.loc[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def split_stats(sample: pd.DataFrame, feature: str, label: str) -> dict:
    if sample.empty:
        return {"n": 0, "events": 0, "event_rate": 0.0, "auc": 0.5}
    y = sample[label].astype(bool)
    return {
        "n": int(len(sample)),
        "events": int(y.sum()),
        "event_rate": float(y.mean()),
        "event_median": float(sample.loc[y, feature].median()) if y.any() else 0.0,
        "normal_median": float(sample.loc[~y, feature].median()) if (~y).any() else 0.0,
        "auc": auc(sample[feature], y),
    }


def thresholds(train: pd.DataFrame, hold: pd.DataFrame, feature: str, label: str) -> list[dict]:
    rows = []
    for q in (0.80, 0.90, 0.95):
        threshold = float(train[feature].quantile(q))
        row = {"quantile": q, "threshold": threshold}
        for name, sample in (("train", train), ("holdout", hold)):
            gate = sample[feature] >= threshold
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


def audit(frame: pd.DataFrame, train_end: pd.Timestamp, lo: float, hi: float) -> dict:
    cohort = frame.loc[(frame["dd_depth"] >= lo) & (frame["dd_depth"] < hi)].copy()
    train = cohort.loc[cohort.index <= train_end]
    hold = cohort.loc[cohort.index > train_end]
    rankings, threshold_tests = {}, {}
    for label in LABELS:
        rows = []
        for feature in FEATURES:
            tr = split_stats(train, feature, label)
            ho = split_stats(hold, feature, label)
            rows.append({
                "feature": feature,
                "train": tr,
                "holdout": ho,
                "stable_auc": float(min(tr["auc"], ho["auc"])),
                "mean_auc": float((tr["auc"] + ho["auc"]) / 2.0),
            })
            threshold_tests[f"{label}:{feature}"] = thresholds(train, hold, feature, label)
        rows.sort(key=lambda x: (x["stable_auc"], x["mean_auc"]), reverse=True)
        rankings[label] = rows
    return {
        "depth_range": [lo, hi],
        "rows": int(len(cohort)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "event_rates": {
            label: {
                "train": float(train[label].mean()) if len(train) else 0.0,
                "holdout": float(hold[label].mean()) if len(hold) else 0.0,
            }
            for label in LABELS
        },
        "feature_rankings": rankings,
        "threshold_stability": threshold_tests,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, shadow, targets, hedge_active, parent_diag = r54.build_aggressive_parent(
        data, raw, ex, guard, gross, cost
    )
    frame = build_frame(targets, data.close, parent.equity)
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]

    cohorts = {
        "early_dd_5_to_12": audit(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": audit(frame, train_end, 0.08, 0.18),
        "deep_dd_12_to_24": audit(frame, train_end, 0.12, 0.24),
    }

    out = {
        "study": "V99 R56 aggressive-parent drawdown-continuation audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "verify on the fixed aggressive R30 parent whether dominant-side gross, total gross and net exposure "
            "causally predict further drawdown deepening before designing a side-specific brake; thresholds are "
            "learned only on the first 60% and evaluated unchanged on the last 40%"
        ),
        "parent_fixed": r54.AGGRESSIVE_PARENT,
        "parent_summary": r36.stats(parent.equity),
        "parent_diagnostics": parent_diag,
        "train_end": train_end.isoformat(),
        "cohorts": cohorts,
        "disclosure": (
            "Diagnostic only. Exposure features use target weights and market history available through t; "
            "future data is used only to label continuation outcomes. No candidate is promoted by this report."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_summary": out["parent_summary"],
        "top": {
            cohort: {
                label: body["feature_rankings"][label]
                for label in LABELS
            }
            for cohort, body in cohorts.items()
        },
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
