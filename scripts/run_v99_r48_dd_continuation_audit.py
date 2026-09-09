from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r39_tail_precursor_audit as r39

r36 = r39.r36
r37 = r39.r37
REPORT = PROJECT / "reports" / "v99_r48_dd_continuation_audit.json"


def future_min(series: pd.Series, hours: int) -> pd.Series:
    # At t evaluate strictly t+1 ... t+hours. This is used only as a label.
    shifted = series.shift(-1)
    return shifted.iloc[::-1].rolling(hours, min_periods=hours).min().iloc[::-1]


def causal_drawdown_age(equity: pd.Series) -> pd.Series:
    eq = equity.astype(float)
    peak = eq.cummax()
    age = np.zeros(len(eq), dtype=float)
    last_peak = 0
    vals = eq.to_numpy()
    peaks = peak.to_numpy()
    for i in range(len(eq)):
        if vals[i] >= peaks[i] * (1.0 - 1e-12):
            last_peak = i
        age[i] = float(i - last_peak)
    return pd.Series(age, index=eq.index)


def build_risk_features(
    targets: pd.DataFrame,
    close: pd.DataFrame,
    equity: pd.Series,
    hedge_active: pd.Series,
) -> pd.DataFrame:
    base = r39.feature_table(targets, close, equity).copy()
    idx = base.index
    eq = equity.reindex(idx).astype(float)
    btc = close["BTCUSDT"].reindex(idx).astype(float)

    # Re-express directional features so higher always means more continuation risk.
    base["dd_depth"] = (-base["equity_dd"]).clip(lower=0.0)
    base["equity_loss_24h"] = (-eq.pct_change(24, fill_method=None)).clip(lower=0.0).fillna(0.0)
    base["equity_loss_72h"] = (-eq.pct_change(72, fill_method=None)).clip(lower=0.0).fillna(0.0)
    base["equity_loss_168h"] = (-eq.pct_change(168, fill_method=None)).clip(lower=0.0).fillna(0.0)
    base["btc_loss_24h"] = (-btc.pct_change(24, fill_method=None)).clip(lower=0.0).fillna(0.0)
    base["btc_loss_72h"] = (-btc.pct_change(72, fill_method=None)).clip(lower=0.0).fillna(0.0)
    base["btc_abs_168h"] = btc.pct_change(168, fill_method=None).abs().fillna(0.0)
    base["dd_age_hours"] = causal_drawdown_age(eq)
    base["r30_hedge_active"] = hedge_active.reindex(idx).fillna(False).astype(float)

    # Causal persistence descriptors. They use information through t only.
    neg1 = eq.pct_change(fill_method=None).lt(0.0).astype(float)
    base["negative_hours_24"] = neg1.rolling(24, min_periods=1).sum()
    base["negative_hours_72"] = neg1.rolling(72, min_periods=1).sum()
    daily = eq.resample("1D").last().pct_change(fill_method=None)
    neg_days = daily.lt(0.0).astype(float).rolling(7, min_periods=1).sum()
    base["negative_days_7"] = neg_days.reindex(idx, method="ffill").fillna(0.0)

    return base.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def continuation_labels(equity: pd.Series) -> pd.DataFrame:
    eq = equity.astype(float)
    peak = eq.cummax()
    current_dd = eq / peak - 1.0
    min7 = future_min(eq, 168)
    min14 = future_min(eq, 336)
    future_dd7 = min7 / peak - 1.0
    future_dd14 = min14 / peak - 1.0

    out = pd.DataFrame(index=eq.index)
    out["current_dd"] = current_dd
    out["future_dd7"] = future_dd7
    out["future_dd14"] = future_dd14
    out["deepen_7d_5pp"] = future_dd7 <= (current_dd - 0.05)
    out["deepen_14d_8pp"] = future_dd14 <= (current_dd - 0.08)
    out["hit_20pct_dd_14d"] = future_dd14 <= -0.20
    return out


def auc(feature: pd.Series, label: pd.Series) -> float:
    frame = pd.concat([feature.rename("x"), label.rename("y")], axis=1).dropna()
    if frame.empty:
        return 0.5
    y = frame["y"].astype(bool)
    n1 = int(y.sum())
    n0 = int((~y).sum())
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = frame["x"].rank(method="average")
    pos_sum = float(ranks.loc[y].sum())
    return float((pos_sum - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def split_stats(sample: pd.DataFrame, feature: str, label: str) -> dict:
    if sample.empty:
        return {"n": 0, "events": 0, "event_rate": 0.0, "auc": 0.5}
    y = sample[label].astype(bool)
    event = sample.loc[y, feature]
    normal = sample.loc[~y, feature]
    return {
        "n": int(len(sample)),
        "events": int(y.sum()),
        "event_rate": float(y.mean()),
        "event_median": float(event.median()) if len(event) else 0.0,
        "normal_median": float(normal.median()) if len(normal) else 0.0,
        "auc": auc(sample[feature], y),
    }


def threshold_test(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    feature: str,
    label: str,
) -> list[dict]:
    rows = []
    for q in (0.80, 0.90, 0.95):
        threshold = float(train[feature].quantile(q))
        for split_name, sample in (("train", train), ("holdout", holdout)):
            gate = sample[feature] >= threshold
            y = sample[label].astype(bool)
            base = float(y.mean()) if len(sample) else 0.0
            gated = float(sample.loc[gate, label].mean()) if gate.any() else 0.0
            rows.append({
                "quantile": q,
                "threshold": threshold,
                "split": split_name,
                "coverage": float(gate.mean()) if len(sample) else 0.0,
                "events_captured": float((gate & y).sum() / max(1, int(y.sum()))),
                "base_event_rate": base,
                "gated_event_rate": gated,
                "lift": float(gated / max(base, 1e-12)),
            })
    return rows


def pair_test(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    f1: str,
    f2: str,
    label: str,
) -> dict:
    # Fixed q80 AND q80 diagnostic. Thresholds come from train only.
    t1 = float(train[f1].quantile(0.80))
    t2 = float(train[f2].quantile(0.80))
    out = {"features": [f1, f2], "thresholds": [t1, t2], "label": label}
    for name, sample in (("train", train), ("holdout", holdout)):
        gate = (sample[f1] >= t1) & (sample[f2] >= t2)
        y = sample[label].astype(bool)
        base = float(y.mean()) if len(sample) else 0.0
        gated = float(sample.loc[gate, label].mean()) if gate.any() else 0.0
        out[name] = {
            "coverage": float(gate.mean()) if len(sample) else 0.0,
            "event_capture": float((gate & y).sum() / max(1, int(y.sum()))),
            "base_rate": base,
            "gated_rate": gated,
            "lift": float(gated / max(base, 1e-12)),
        }
    return out


def audit_cohort(
    frame: pd.DataFrame,
    train_end: pd.Timestamp,
    min_depth: float,
    max_depth: float,
) -> dict:
    cohort = frame.loc[(frame["dd_depth"] >= min_depth) & (frame["dd_depth"] < max_depth)].copy()
    train = cohort.loc[cohort.index <= train_end]
    holdout = cohort.loc[cohort.index > train_end]

    labels = ("deepen_7d_5pp", "deepen_14d_8pp", "hit_20pct_dd_14d")
    exclude = {
        "equity_dd", "equity_r3h", "equity_r6h", "equity_r24h",
        "current_dd", "future_dd7", "future_dd14",
        *labels,
    }
    features = [c for c in cohort.columns if c not in exclude]

    rankings = {}
    thresholds = {}
    for label in labels:
        ranked = []
        for feature in features:
            tr = split_stats(train, feature, label)
            ho = split_stats(holdout, feature, label)
            ranked.append({
                "feature": feature,
                "train": tr,
                "holdout": ho,
                "stable_auc": float(min(tr["auc"], ho["auc"])),
                "mean_auc": float((tr["auc"] + ho["auc"]) / 2.0),
            })
        ranked.sort(key=lambda x: (x["stable_auc"], x["mean_auc"]), reverse=True)
        rankings[label] = ranked
        for row in ranked[:10]:
            if row["stable_auc"] >= 0.56:
                key = f"{label}:{row['feature']}"
                thresholds[key] = threshold_test(train, holdout, row["feature"], label)

    fixed_pairs = (
        ("dd_depth", "net_abs"),
        ("dd_depth", "equity_loss_72h"),
        ("equity_loss_168h", "net_abs"),
        ("net_abs", "btc_abs_72h"),
        ("gross", "cross_section_vol_1h"),
        ("dd_age_hours", "equity_loss_72h"),
    )
    pairs = []
    for label in labels:
        for f1, f2 in fixed_pairs:
            pairs.append(pair_test(train, holdout, f1, f2, label))

    return {
        "depth_range": [min_depth, max_depth],
        "rows": int(len(cohort)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(holdout)),
        "event_rates": {
            label: {
                "train": float(train[label].mean()) if len(train) else 0.0,
                "holdout": float(holdout[label].mean()) if len(holdout) else 0.0,
            }
            for label in labels
        },
        "feature_rankings": rankings,
        "threshold_stability": thresholds,
        "predeclared_pair_tests": pairs,
    }


def main() -> None:
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    r30, r30_targets, hedge_active = r37.build_r30(data, raw, ex, guard, gross, cost)

    features = build_risk_features(r30_targets, data.close, r30.equity, hedge_active)
    labels = continuation_labels(r30.equity)
    frame = features.join(labels)
    frame = frame.dropna(subset=["future_dd7", "future_dd14"])

    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]

    cohorts = {
        "early_dd_5_to_12": audit_cohort(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": audit_cohort(frame, train_end, 0.08, 0.18),
    }

    out = {
        "study": "V99 R48 R30 drawdown-continuation precursor audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "once R30 is already in a moderate drawdown, identify causal features observable at close t "
            "that predict material further deepening over the next 7 or 14 days; use a fixed chronological "
            "60/40 split so any future continuation guard can be rare and evidence-led rather than generic"
        ),
        "r30_fixed_base": r37.R30_BASE,
        "r30_summary": r36.stats(r30.equity),
        "train_end": train_end.isoformat(),
        "label_definitions": {
            "deepen_7d_5pp": "future minimum equity within next 168h implies drawdown at least 5 percentage points deeper than current drawdown, relative to the peak already known at t",
            "deepen_14d_8pp": "future minimum equity within next 336h implies drawdown at least 8 percentage points deeper than current drawdown, relative to the peak already known at t",
            "hit_20pct_dd_14d": "future minimum equity within next 336h falls to at least 20% below the peak already known at t",
        },
        "cohorts": cohorts,
        "disclosure": (
            "Diagnostic only. All features are causal and use information available through close t. "
            "Future prices appear only in labels. Thresholds are estimated on the first 60% of chronology "
            "and evaluated unchanged on the final 40%. No candidate may be promoted from this report alone."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")

    compact = {
        "study": out["study"],
        "r30_summary": out["r30_summary"],
        "train_end": out["train_end"],
        "cohorts": {
            name: {
                "event_rates": item["event_rates"],
                "top_7d": item["feature_rankings"]["deepen_7d_5pp"][:8],
                "top_14d": item["feature_rankings"]["deepen_14d_8pp"][:8],
            }
            for name, item in cohorts.items()
        },
    }
    print(json.dumps(compact, indent=2), flush=True)


if __name__ == "__main__":
    main()
