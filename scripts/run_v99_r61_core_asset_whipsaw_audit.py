from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r59_h15_mild_crash as r59

r36 = r59.r36
REPORT = PROJECT / "reports" / "v99_r61_core_asset_whipsaw_audit.json"
PARENT = r59.PARENT


def future_min(series: pd.Series, hours: int) -> pd.Series:
    shifted = series.shift(-1)
    return shifted.iloc[::-1].rolling(hours, min_periods=hours).min().iloc[::-1]


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
    return out


def auc(feature: pd.Series, label: pd.Series) -> float:
    frame = pd.concat([feature.rename("x"), label.rename("y")], axis=1).dropna()
    if frame.empty:
        return 0.5
    y = frame["y"].astype(bool)
    n1 = int(y.sum()); n0 = int((~y).sum())
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = frame["x"].rank(method="average")
    pos_sum = float(ranks.loc[y].sum())
    return float((pos_sum - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def feature_table(targets: pd.DataFrame, close: pd.DataFrame, equity: pd.Series) -> pd.DataFrame:
    idx = targets.index.intersection(close.index).intersection(equity.index)
    t = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    c = close.reindex(index=idx, columns=close.columns)
    eq = equity.reindex(idx).astype(float)

    abs_t = t.abs()
    gross = abs_t.sum(axis=1)
    gross_safe = gross.replace(0.0, np.nan)
    long_gross = t.clip(lower=0.0).sum(axis=1)
    short_gross = (-t.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    net_abs = t.sum(axis=1).abs()
    share = abs_t.div(gross_safe, axis=0).fillna(0.0)
    arr = np.sort(share.to_numpy(), axis=1)
    top1_share = pd.Series(arr[:, -1], index=idx) if arr.shape[1] else pd.Series(0.0, index=idx)
    top3_share = pd.Series(arr[:, -min(3, arr.shape[1]):].sum(axis=1), index=idx) if arr.shape[1] else pd.Series(0.0, index=idx)
    hhi = (share * share).sum(axis=1)

    btc = t["BTCUSDT"]
    eth = t["ETHUSDT"]
    btc_abs = btc.abs(); eth_abs = eth.abs()
    core_gross = btc_abs + eth_abs
    core_share = (core_gross / gross_safe).fillna(0.0)
    btc_share = (btc_abs / gross_safe).fillna(0.0)
    eth_share = (eth_abs / gross_safe).fillna(0.0)
    eth_core_share = (eth_abs / core_gross.replace(0.0, np.nan)).fillna(0.0)
    core_net_abs = (btc + eth).abs()
    core_offset = (core_gross - core_net_abs).clip(lower=0.0)

    tb_diff = btc.diff().abs().fillna(0.0)
    te_diff = eth.diff().abs().fillna(0.0)
    core_turn = tb_diff + te_diff

    sb = np.sign(btc); se = np.sign(eth)
    btc_flip = ((sb != sb.shift(1)) & (btc_abs >= 0.05) & (btc.shift(1).abs() >= 0.05)).astype(float)
    eth_flip = ((se != se.shift(1)) & (eth_abs >= 0.05) & (eth.shift(1).abs() >= 0.05)).astype(float)
    core_flip = btc_flip + eth_flip

    btc_r6 = c["BTCUSDT"].pct_change(6, fill_method=None).fillna(0.0)
    btc_r24 = c["BTCUSDT"].pct_change(24, fill_method=None).fillna(0.0)
    btc_r72 = c["BTCUSDT"].pct_change(72, fill_method=None).fillna(0.0)
    eth_r6 = c["ETHUSDT"].pct_change(6, fill_method=None).fillna(0.0)
    eth_r24 = c["ETHUSDT"].pct_change(24, fill_method=None).fillna(0.0)
    eth_r72 = c["ETHUSDT"].pct_change(72, fill_method=None).fillna(0.0)

    def adverse(weight: pd.Series, ret: pd.Series) -> pd.Series:
        return ((-np.sign(weight) * ret).clip(lower=0.0) * weight.abs()).fillna(0.0)

    out = pd.DataFrame(index=idx)
    out["dd_depth"] = (1.0 - eq / eq.cummax()).clip(lower=0.0)
    out["gross"] = gross
    out["dominant_side_gross"] = dominant
    out["net_abs"] = net_abs
    out["top1_share"] = top1_share
    out["top3_share"] = top3_share
    out["hhi"] = hhi
    out["btc_abs_weight"] = btc_abs
    out["eth_abs_weight"] = eth_abs
    out["core_gross"] = core_gross
    out["core_share"] = core_share
    out["btc_share"] = btc_share
    out["eth_share"] = eth_share
    out["eth_core_share"] = eth_core_share
    out["core_net_abs"] = core_net_abs
    out["core_offset"] = core_offset
    out["core_turnover_6h"] = core_turn.rolling(6, min_periods=1).sum()
    out["core_turnover_24h"] = core_turn.rolling(24, min_periods=1).sum()
    out["core_turnover_72h"] = core_turn.rolling(72, min_periods=1).sum()
    out["btc_flips_24h"] = btc_flip.rolling(24, min_periods=1).sum()
    out["eth_flips_24h"] = eth_flip.rolling(24, min_periods=1).sum()
    out["core_flips_24h"] = core_flip.rolling(24, min_periods=1).sum()
    out["core_flips_72h"] = core_flip.rolling(72, min_periods=1).sum()
    out["btc_adverse_6h"] = adverse(btc, btc_r6)
    out["eth_adverse_6h"] = adverse(eth, eth_r6)
    out["core_adverse_6h"] = out["btc_adverse_6h"] + out["eth_adverse_6h"]
    out["btc_adverse_24h"] = adverse(btc, btc_r24)
    out["eth_adverse_24h"] = adverse(eth, eth_r24)
    out["core_adverse_24h"] = out["btc_adverse_24h"] + out["eth_adverse_24h"]
    out["btc_adverse_72h"] = adverse(btc, btc_r72)
    out["eth_adverse_72h"] = adverse(eth, eth_r72)
    out["core_adverse_72h"] = out["btc_adverse_72h"] + out["eth_adverse_72h"]
    out["eth_flip_weighted_24h"] = out["eth_flips_24h"] * eth_abs
    out["core_flip_weighted_24h"] = out["core_flips_24h"] * core_gross
    out["core_turnover_x_share_24h"] = out["core_turnover_24h"] * core_share
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


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


def audit(frame: pd.DataFrame, train_end: pd.Timestamp, lo: float, hi: float) -> dict:
    cohort = frame.loc[(frame["dd_depth"] >= lo) & (frame["dd_depth"] < hi)].copy()
    train = cohort.loc[cohort.index <= train_end]
    hold = cohort.loc[cohort.index > train_end]
    labels = ("deepen_7d_5pp", "deepen_14d_8pp")
    exclude = {"dd_depth", "current_dd", "future_dd7", "future_dd14", *labels}
    features = [c for c in cohort.columns if c not in exclude]
    rankings = {}; thresholds = {}
    for label in labels:
        ranked = []
        for feature in features:
            tr = split_stats(train, feature, label)
            ho = split_stats(hold, feature, label)
            ranked.append({
                "feature": feature,
                "train": tr,
                "holdout": ho,
                "stable_auc": float(min(tr["auc"], ho["auc"])),
                "mean_auc": float((tr["auc"] + ho["auc"]) / 2.0),
            })
        ranked.sort(key=lambda x: (x["stable_auc"], x["mean_auc"]), reverse=True)
        rankings[label] = ranked
        for row in ranked[:15]:
            if row["stable_auc"] >= 0.56:
                thresholds[f"{label}:{row['feature']}"] = threshold_rows(train, hold, row["feature"], label)
    return {
        "depth_range": [lo, hi],
        "rows": int(len(cohort)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "event_rates": {
            label: {"train": float(train[label].mean()) if len(train) else 0.0,
                    "holdout": float(hold[label].mean()) if len(hold) else 0.0}
            for label in labels
        },
        "feature_rankings": rankings,
        "threshold_stability": thresholds,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, shadow, targets, active = r59.build_parent(data, raw, ex, guard, gross, cost)
    features = feature_table(targets, data.close, parent.equity)
    labels = continuation_labels(parent.equity)
    frame = features.join(labels).dropna(subset=["future_dd7", "future_dd14"])
    split = int(len(frame) * 0.60)
    train_end = frame.index[max(0, split - 1)]
    cohorts = {
        "early_dd_5_to_12": audit(frame, train_end, 0.05, 0.12),
        "mid_dd_8_to_18": audit(frame, train_end, 0.08, 0.18),
        "deep_dd_12_to_24": audit(frame, train_end, 0.12, 0.24),
    }
    out = {
        "study": "V99 R61 core-asset concentration / whipsaw continuation audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "test whether BTC/ETH concentration, especially ETH exposure, core turnover/sign flips, and causal adverse "
            "moves explain drawdown continuation in the R55 hedge-0.15 parent, using a fixed 60/40 chronological split"
        ),
        "parent_fixed": PARENT,
        "parent_summary": r36.stats(parent.equity),
        "train_end": train_end.isoformat(),
        "cohorts": cohorts,
        "disclosure": (
            "Diagnostic only. All features use target weights and prices available through t; future data appears only "
            "in continuation labels. Candidate construction must be a separate prospective test."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_summary": out["parent_summary"],
        "top": {
            k: {
                lab: v["feature_rankings"][lab][:12]
                for lab in ("deepen_7d_5pp", "deepen_14d_8pp")
            } for k, v in cohorts.items()
        },
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
