from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r55_low_hedge_amplitude_frontier as r55
import run_v99_r66_hedge_amplitude_regime_audit as r66

REPORT = PROJECT / "reports" / "v99_r74_fresh_aligned_alpha_audit.json"


def flatten_feature(frame: pd.DataFrame, sample_idx: pd.DatetimeIndex, active: pd.DataFrame, name: str) -> pd.DataFrame:
    f = frame.reindex(sample_idx)
    a = active.reindex(sample_idx).fillna(False)
    s = f.where(a).stack(dropna=True).rename(name)
    return s.to_frame()


def forward_directional(close: pd.DataFrame, raw: pd.DataFrame, hours: int) -> pd.DataFrame:
    future = close.shift(-hours) / close - 1.0
    return np.sign(raw) * future


def gate_by_threshold(values: pd.Series, labels: pd.Series, threshold: float, direction: str) -> dict:
    return r66.gated_stats(values, labels, threshold, direction)


def temporal_stability(df: pd.DataFrame, feature: str, label: str, threshold: float, direction: str) -> dict:
    times = pd.DatetimeIndex(df.index.get_level_values(0).unique()).sort_values()
    folds = np.array_split(times, 5)
    out = []
    for i, fold in enumerate(folds, 1):
        if len(fold) == 0:
            continue
        sub = df.loc[df.index.get_level_values(0).isin(fold), [feature, label]].dropna()
        if sub.empty:
            continue
        mask = sub[feature] >= threshold if direction == "high" else sub[feature] <= threshold
        base = float(sub[label].mean())
        rate = float(sub.loc[mask, label].mean()) if mask.any() else 0.0
        adv = float(sub.loc[mask, "fwd72"].mean()) if "fwd72" in sub.columns and mask.any() else None
        out.append({
            "fold": i,
            "start": fold[0].isoformat(),
            "end": fold[-1].isoformat(),
            "rows": int(len(sub)),
            "selected": int(mask.sum()),
            "coverage": float(mask.mean()),
            "base_rate": base,
            "selected_rate": rate,
            "lift": float(rate / base) if base > 0 else 0.0,
        })
    return {
        "folds": out,
        "positive_lift_folds": int(sum(x["lift"] > 1.0 for x in out)),
        "fold_count": int(len(out)),
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    close = data.close.reindex(raw.index).reindex(columns=raw.columns)
    raw = raw.reindex(index=close.index, columns=close.columns).fillna(0.0)
    active = raw.abs() > 1e-9

    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    r168 = close.pct_change(168, fill_method=None)
    ema = close.ewm(span=336, adjust=False, min_periods=336).mean()
    sign = np.sign(raw)

    directional24 = sign * r24
    directional72 = sign * r72
    directional168 = sign * r168
    directional_ema = sign * (close / ema - 1.0)
    directional_min = pd.DataFrame(np.minimum(directional24.to_numpy(), directional72.to_numpy()), index=close.index, columns=close.columns)
    directional_mean = (directional24 + directional72) / 2.0
    pos_abs = raw.abs()

    # Cross-sectional ranks are causal and scale-free.
    rank24 = directional24.rank(axis=1, pct=True)
    rank72 = directional72.rank(axis=1, pct=True)
    rank_min = pd.DataFrame(np.minimum(rank24.to_numpy(), rank72.to_numpy()), index=close.index, columns=close.columns)

    fwd24 = forward_directional(close, raw, 24)
    fwd72 = forward_directional(close, raw, 72)
    label24 = fwd24 > 0.002
    label72 = fwd72 > 0.004

    # One observation per day, matching the successful R66/R71 anti-overlap protocol.
    sample_idx = close.index[::24]
    pieces = []
    features = {
        "dir24": directional24,
        "dir72": directional72,
        "dir168": directional168,
        "dir_ema": directional_ema,
        "dir_min24_72": directional_min,
        "dir_mean24_72": directional_mean,
        "rank24": rank24,
        "rank72": rank72,
        "rank_min24_72": rank_min,
        "position_abs": pos_abs,
    }
    for name, frame in features.items():
        pieces.append(flatten_feature(frame, sample_idx, active, name))

    df = pieces[0]
    for p in pieces[1:]:
        df = df.join(p, how="outer")
    df = df.join(flatten_feature(fwd24, sample_idx, active, "fwd24"), how="left")
    df = df.join(flatten_feature(fwd72, sample_idx, active, "fwd72"), how="left")
    df = df.join(flatten_feature(label24.astype(float), sample_idx, active, "label24"), how="left")
    df = df.join(flatten_feature(label72.astype(float), sample_idx, active, "label72"), how="left")
    df["label24"] = df["label24"].astype(bool)
    df["label72"] = df["label72"].astype(bool)
    df = df.replace([np.inf, -np.inf], np.nan)

    times = pd.DatetimeIndex(df.index.get_level_values(0).unique()).sort_values()
    split = int(len(times) * 0.60)
    train_times = times[:split]
    hold_times = times[split:]
    train_mask = df.index.get_level_values(0).isin(train_times)
    hold_mask = df.index.get_level_values(0).isin(hold_times)

    rankings = {}
    for label_name in ("label24", "label72"):
        rows = []
        for name in features:
            tr = df.loc[train_mask, [name, label_name]].dropna()
            ho = df.loc[hold_mask, [name, label_name]].dropna()
            if len(tr) < 500 or len(ho) < 250:
                continue
            atr = r66.auc(tr[name], tr[label_name])
            aho = r66.auc(ho[name], ho[label_name])
            direction = "high" if atr >= 0.5 else "low"
            q = 0.80 if direction == "high" else 0.20
            threshold = float(tr[name].quantile(q))
            gtr = gate_by_threshold(tr[name], tr[label_name], threshold, direction)
            gho = gate_by_threshold(ho[name], ho[label_name], threshold, direction)
            selected_hold = ho[name] >= threshold if direction == "high" else ho[name] <= threshold
            hold_forward = df.loc[ho.index, "fwd72" if label_name == "label72" else "fwd24"]
            mean_adv = float(hold_forward.loc[selected_hold].mean()) if selected_hold.any() else 0.0
            rows.append({
                "feature": name,
                "direction": direction,
                "threshold_train_only": threshold,
                "train_auc": float(atr),
                "holdout_auc": float(aho),
                "train_gate": gtr,
                "holdout_gate": gho,
                "holdout_selected_mean_directional_forward_return": mean_adv,
            })
        rows.sort(key=lambda z: (
            min(z["train_gate"]["lift"], z["holdout_gate"]["lift"]),
            z["holdout_selected_mean_directional_forward_return"],
            min(z["train_auc"], z["holdout_auc"]),
        ), reverse=True)
        rankings[label_name] = rows

    stability = {}
    for label_name in ("label24", "label72"):
        for row in rankings[label_name][:5]:
            key = f"{label_name}:{row['feature']}"
            stability[key] = temporal_stability(df, row["feature"], label_name, row["threshold_train_only"], row["direction"])

    out = {
        "study": "V99 R74 fresh aligned-position alpha audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "relearn from scratch, with a chronological 60/40 split, which causal position-alignment features predict positive future directional returns strongly enough to justify a future small exposure boost; no R28 fitted threshold is reused",
        "sample_policy": "active requested positions only, one observation every 24h; chronological 60/40 split by observation date",
        "labels": {
            "label24": "position-directional 24h forward return > +0.20%",
            "label72": "position-directional 72h forward return > +0.40%",
        },
        "daily_observation_dates": int(len(times)),
        "position_rows": int(len(df)),
        "train_end": train_times[-1].isoformat() if len(train_times) else None,
        "holdout_start": hold_times[0].isoformat() if len(hold_times) else None,
        "rankings": rankings,
        "top_feature_temporal_stability": stability,
        "disclosure": "Diagnostic historical research only. Future returns appear only in labels. Feature thresholds are fitted on the first 60% of chronological observation dates and then frozen for holdout evaluation. The old R28 boost thresholds/scales are not reused. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "train_end": out["train_end"], "top24": rankings["label24"][:5], "top72": rankings["label72"][:5], "stability": stability}, indent=2), flush=True)


if __name__ == "__main__":
    main()
