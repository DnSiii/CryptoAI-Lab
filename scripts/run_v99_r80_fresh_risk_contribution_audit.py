from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r62_asset_damage_precursor_audit as r62
import run_v99_r66_hedge_amplitude_regime_audit as r66
import run_v99_r67_dynamic_hedge_router as r67
import run_v99_r75_hedged_recovery_alpha as r75

REPORT = PROJECT / "reports" / "v99_r80_fresh_risk_contribution_audit.json"
r36 = r67.r36

COHORTS = {
    "early_dd_5_to_12": (0.05, 0.12),
    "mid_dd_8_to_18": (0.08, 0.18),
}
LABELS = ("deepen_7d_5pp", "deepen_14d_8pp")


def target_features(targets: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    idx = targets.index
    t = targets.abs().fillna(0.0)
    gross = t.sum(axis=1).replace(0.0, np.nan)
    share = t.div(gross, axis=0).fillna(0.0)
    sorted_share = np.sort(share.to_numpy(dtype=float), axis=1)

    r1 = close.pct_change(1, fill_method=None)
    vol24 = r1.rolling(24, min_periods=12).std().reindex_like(targets).fillna(0.0)
    vol72 = r1.rolling(72, min_periods=24).std().reindex_like(targets).fillna(0.0)
    risk24 = t * vol24
    risk72 = t * vol72
    risk24_sum = risk24.sum(axis=1).replace(0.0, np.nan)
    risk72_sum = risk72.sum(axis=1).replace(0.0, np.nan)
    risk24_share = risk24.div(risk24_sum, axis=0).fillna(0.0)
    risk72_share = risk72.div(risk72_sum, axis=0).fillna(0.0)

    signed = np.sign(targets)
    d24 = signed * close.pct_change(24, fill_method=None).reindex_like(targets)
    d72 = signed * close.pct_change(72, fill_method=None).reindex_like(targets)
    weighted_d24 = (share * d24).sum(axis=1)
    weighted_d72 = (share * d72).sum(axis=1)

    long_gross = targets.clip(lower=0.0).sum(axis=1)
    short_gross = (-targets.clip(upper=0.0)).sum(axis=1)
    dominant_side = pd.concat([long_gross, short_gross], axis=1).max(axis=1)

    out = pd.DataFrame(index=idx)
    out["target_gross"] = gross.fillna(0.0)
    out["target_top1_share"] = share.max(axis=1)
    out["target_top2_share"] = sorted_share[:, -2:].sum(axis=1) if share.shape[1] >= 2 else sorted_share.sum(axis=1)
    out["target_top3_share"] = sorted_share[:, -3:].sum(axis=1) if share.shape[1] >= 3 else sorted_share.sum(axis=1)
    out["target_hhi"] = (share * share).sum(axis=1)
    out["target_dominant_side_share"] = (dominant_side / gross).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["risk24_top1_share"] = risk24_share.max(axis=1)
    out["risk72_top1_share"] = risk72_share.max(axis=1)
    out["risk24_hhi"] = (risk24_share * risk24_share).sum(axis=1)
    out["risk72_hhi"] = (risk72_share * risk72_share).sum(axis=1)
    out["weighted_directional_24h"] = weighted_d24
    out["weighted_directional_72h"] = weighted_d72
    out["worst_directional_24h"] = d24.min(axis=1)
    out["worst_directional_72h"] = d72.min(axis=1)
    out["adverse_weight_share_24h"] = share.where(d24 < 0.0, 0.0).sum(axis=1)
    out["adverse_weight_share_72h"] = share.where(d72 < 0.0, 0.0).sum(axis=1)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def gate_stats(x: pd.Series, y: pd.Series, threshold: float, direction: str) -> dict:
    z = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if z.empty:
        return {"rows":0,"selected":0,"coverage":0.0,"base_rate":0.0,"event_rate":0.0,"lift":0.0,"event_capture":0.0}
    mask = z["x"] >= threshold if direction == "high" else z["x"] <= threshold
    base = float(z["y"].mean())
    rate = float(z.loc[mask, "y"].mean()) if mask.any() else 0.0
    events = int(z["y"].sum())
    cap = int(z.loc[mask, "y"].sum()) if mask.any() else 0
    return {
        "rows": int(len(z)),
        "selected": int(mask.sum()),
        "coverage": float(mask.mean()),
        "base_rate": base,
        "event_rate": rate,
        "lift": float(rate/base) if base > 0 else 0.0,
        "event_capture": float(cap/events) if events > 0 else 0.0,
    }


def rank_train(train: pd.DataFrame, hold: pd.DataFrame, features: list[str], label: str) -> list[dict]:
    rows = []
    for feature in features:
        tr = train[[feature, label]].dropna()
        ho = hold[[feature, label]].dropna()
        if len(tr) < 100 or len(ho) < 50:
            continue
        auc_tr = r66.auc(tr[feature], tr[label])
        direction = "high" if auc_tr >= 0.5 else "low"
        q = 0.80 if direction == "high" else 0.20
        threshold = float(tr[feature].quantile(q))
        gtr = gate_stats(tr[feature], tr[label], threshold, direction)
        gho = gate_stats(ho[feature], ho[label], threshold, direction)
        auc_ho = r66.auc(ho[feature], ho[label])
        train_strength = max(auc_tr, 1.0 - auc_tr)
        rows.append({
            "feature": feature,
            "direction": direction,
            "threshold_train_only": threshold,
            "train_auc": float(auc_tr),
            "holdout_auc": float(auc_ho),
            "train_strength": float(train_strength),
            "train_gate": gtr,
            "holdout_gate": gho,
            "train_selection_score": float(np.log(max(gtr["lift"],1e-12)) + 1.5*(train_strength-0.5)),
        })
    rows.sort(key=lambda z:(z["train_selection_score"], z["train_gate"]["lift"], z["train_strength"]), reverse=True)
    return rows


def fold_stability(cohort: pd.DataFrame, row: dict, label: str) -> dict:
    fold_rows = []
    for i, ids in enumerate(np.array_split(cohort.index, 5), 1):
        sub = cohort.loc[ids]
        g = gate_stats(sub[row["feature"]], sub[label], row["threshold_train_only"], row["direction"])
        g.update({"fold":i,"start":ids[0].isoformat() if len(ids) else None,"end":ids[-1].isoformat() if len(ids) else None})
        fold_rows.append(g)
    return {
        "folds": fold_rows,
        "positive_lift_folds": int(sum(x["lift"] > 1.0 for x in fold_rows)),
        "fold_count": int(len(fold_rows)),
        "minimum_fold_lift": float(min((x["lift"] for x in fold_rows), default=0.0)),
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, targets, parent_diag = r75.build_variant(data, raw, ex, guard, gross, cost, False)

    damage = r62.damage_features(parent)
    target = target_features(targets, data.close.reindex(index=targets.index, columns=targets.columns))
    labels = r62.r61.continuation_labels(parent.equity)
    frame = damage.join(target, how="left").join(labels).replace([np.inf,-np.inf],np.nan)

    # One observation per day to reduce serial duplication of 7d/14d continuation labels.
    sample = frame.iloc[::24].copy().dropna(subset=["future_dd7","future_dd14"])
    exclude = {"dd_depth","current_dd","future_dd7","future_dd14",*LABELS}
    features = [c for c in sample.columns if c not in exclude]

    results = {}
    for cohort_name, (lo,hi) in COHORTS.items():
        cohort = sample.loc[(sample["dd_depth"] >= lo) & (sample["dd_depth"] < hi)].copy()
        split = int(len(cohort)*0.60)
        train = cohort.iloc[:split]
        hold = cohort.iloc[split:]
        label_results = {}
        for label in LABELS:
            ranked = rank_train(train, hold, features, label)
            selected = ranked[0] if ranked else None
            stability = fold_stability(cohort, selected, label) if selected else None
            pass_gate = bool(
                selected
                and selected["train_gate"]["lift"] >= 1.15
                and selected["holdout_gate"]["lift"] >= 1.10
                and stability["positive_lift_folds"] >= 4
            )
            label_results[label] = {
                "selected_train_only": selected,
                "selected_temporal_stability": stability,
                "fresh_signal_pass": pass_gate,
                "top_train_ranked": ranked[:15],
            }
        results[cohort_name] = {
            "depth_range":[lo,hi],
            "rows":int(len(cohort)),
            "train_rows":int(len(train)),
            "holdout_rows":int(len(hold)),
            "train_end":train.index[-1].isoformat() if len(train) else None,
            "labels":label_results,
        }

    out = {
        "study":"V99 R80 fresh R73 risk-contribution and concentrated-damage audit",
        "status":"DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective":"select on the first 60% only a generic causal feature that predicts further R73 drawdown deepening, combining realized asset damage with target/risk concentration features; then test the frozen signal on the later 40% and five chronological folds",
        "sample_policy":"one observation every 24h; early and mid drawdown cohorts only",
        "selection_policy":"feature direction, q80/q20 threshold and feature choice use training block only; holdout never influences selected_train_only",
        "parent_r73_summary":r36.stats(parent.equity),
        "parent_diagnostics":parent_diag,
        "feature_count":int(len(features)),
        "results":results,
        "disclosure":"Diagnostic historical research only. All predictors use information available through t. Future equity appears only in continuation labels. No symbol identity is used as a predictor. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols":quarantined,
        "v15_metadata":metadata,
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"study":out["study"],"results":{c:{l:v["selected_train_only"]|{"fresh_signal_pass":v["fresh_signal_pass"],"stability":v["selected_temporal_stability"]} for l,v in x["labels"].items()} for c,x in results.items()}},indent=2),flush=True)


if __name__ == "__main__":
    main()
