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
from paper_once_v15 import build_v15
from paper_once_v16 import build_v16

r36 = r88.r36
r86 = r88.r86
cap = r88.cap
REPORT = PROJECT / "reports" / "v99_r100_cross_engine_consensus_audit.json"
V16_CONFIG = PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json"
SHADOW_SCALE = 1.05
FOLDS = 5
TRAIN_FRACTION = 0.60


def stat(frame: pd.DataFrame, mask: pd.Series) -> dict:
    z = frame.loc[mask]
    base_pos = float((frame["advantage"] > 0.0).mean()) if len(frame) else 0.0
    pos = float((z["advantage"] > 0.0).mean()) if len(z) else 0.0
    return {
        "rows": int(len(frame)),
        "selected": int(len(z)),
        "coverage": float(len(z) / max(1, len(frame))),
        "base_positive_rate": base_pos,
        "selected_positive_rate": pos,
        "lift": float(pos / max(1e-12, base_pos)) if base_pos > 0 else 0.0,
        "mean_advantage": float(z["advantage"].mean()) if len(z) else 0.0,
        "median_advantage": float(z["advantage"].median()) if len(z) else 0.0,
    }


def cosine_rows(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    aa = a.to_numpy(dtype=float)
    bb = b.to_numpy(dtype=float)
    dot = (aa * bb).sum(axis=1)
    den = np.sqrt((aa * aa).sum(axis=1) * (bb * bb).sum(axis=1))
    out = np.divide(dot, den, out=np.full(len(a), np.nan), where=den > 1e-12)
    return pd.Series(out, index=a.index)


def weighted_sign_agreement(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    aa = a.to_numpy(dtype=float)
    bb = b.to_numpy(dtype=float)
    overlap = np.minimum(np.abs(aa), np.abs(bb))
    same = (np.sign(aa) == np.sign(bb)) & (np.abs(aa) > 1e-12) & (np.abs(bb) > 1e-12)
    num = (overlap * same.astype(float)).sum(axis=1)
    den = overlap.sum(axis=1)
    out = np.divide(num, den, out=np.full(len(a), np.nan), where=den > 1e-12)
    return pd.Series(out, index=a.index)


def normalized_l1_disagreement(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    aa = a.to_numpy(dtype=float)
    bb = b.to_numpy(dtype=float)
    num = np.abs(aa - bb).sum(axis=1)
    den = np.abs(aa).sum(axis=1) + np.abs(bb).sum(axis=1)
    out = np.divide(num, den, out=np.full(len(a), np.nan), where=den > 1e-12)
    return pd.Series(out, index=a.index)


def main():
    # R98/R73 research boundary. The action under test is only a mild expansion
    # of the R73 parent in rows where the already-frozen R88/R98 gate is OFF.
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    severe_cost = float(ex["severe_cost_per_side"])
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(
        data, raw, ex, guard, gross, severe_cost
    )
    gate, gdiag = r88.daily_gate(parent.equity)
    off = ~gate

    shadow_targets = parent_targets.copy()
    shadow_targets.loc[off, :] = shadow_targets.loc[off, :] * SHADOW_SCALE
    shadow_targets = cap(shadow_targets, float(r86.P15["gross_cap"]))
    shadow = r36.run(
        data, shadow_targets, ex, severe_cost, float(r86.P15["gross_cap"]), guard
    )

    # Structural sensors only. V15 and V16 are not used as replacement engines;
    # their target-vector agreement/disagreement is observed causally at close t.
    _, v15_data, v15_targets, _, _, _, _ = build_v15()
    v16_candidate = json.loads(V16_CONFIG.read_text(encoding="utf-8"))
    v16_data, v16_targets, _, _, _ = build_v16(v16_candidate)

    common_start = max(
        parent_targets.index[0], v15_targets.index[0], v16_targets.index[0]
    )
    common_end = min(
        parent_targets.index[-1], v15_targets.index[-1], v16_targets.index[-1],
        v15_data.close.index[-1], v16_data.close.index[-1]
    )
    idx = parent_targets.loc[common_start:common_end].index
    idx = idx.intersection(v15_targets.index).intersection(v16_targets.index)
    cols = parent_targets.columns.intersection(v15_targets.columns).intersection(v16_targets.columns)
    if len(idx) < 24 * 365 or len(cols) < 3:
        raise RuntimeError("Insufficient common V15/V16/R73 target history for R100")

    pt = parent_targets.reindex(index=idx, columns=cols).fillna(0.0)
    t15 = v15_targets.reindex(index=idx, columns=cols).fillna(0.0)
    t16 = v16_targets.reindex(index=idx, columns=cols).fillna(0.0)

    peq = parent.equity.reindex(idx).astype(float)
    seq = shadow.equity.reindex(idx).astype(float)
    off = off.reindex(idx).fillna(False).astype(bool)
    gate = gate.reindex(idx).fillna(False).astype(bool)
    protect = protect.reindex(idx).fillna(False).astype(bool)

    advantage = (seq.shift(-24) / seq) / (peq.shift(-24) / peq) - 1.0

    f = pd.DataFrame(index=idx)
    f["v15_v16_cosine"] = cosine_rows(t15, t16)
    f["v15_v16_weighted_sign_agreement"] = weighted_sign_agreement(t15, t16)
    f["v15_v16_l1_disagreement"] = normalized_l1_disagreement(t15, t16)
    # Parent-v16 alignment is an action-alignment sensor, not a third independent vote.
    f["parent_v16_cosine"] = cosine_rows(pt, t16)

    # One daily observation, matching the causal decision cadence used throughout
    # the R73/R88/R98 family. No future value enters a feature.
    sample_idx = idx[::24]
    frame = f.reindex(sample_idx).copy()
    frame["advantage"] = advantage.reindex(sample_idx)
    frame["gate_off"] = off.reindex(sample_idx).astype(bool)
    frame = frame.loc[frame["gate_off"]].drop(columns=["gate_off"])
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_index()

    split = int(len(frame) * TRAIN_FRACTION)
    split = max(1, min(len(frame) - 1, split))
    train = frame.iloc[:split].copy()
    hold = frame.iloc[split:].copy()

    # Predeclared economically-motivated consensus rules only. We do NOT search
    # both directions for every feature as in R99; agreement must be high or
    # disagreement low. Thresholds are fitted on train only.
    specs = (
        ("v15_v16_cosine", "high", 0.75),
        ("v15_v16_weighted_sign_agreement", "high", 0.75),
        ("v15_v16_l1_disagreement", "low", 0.25),
        ("parent_v16_cosine", "high", 0.75),
    )
    candidates = []
    for feature, direction, q in specs:
        threshold = float(train[feature].quantile(q))
        tm = train[feature] <= threshold if direction == "low" else train[feature] >= threshold
        hm = hold[feature] <= threshold if direction == "low" else hold[feature] >= threshold
        ts = stat(train, tm)
        hs = stat(hold, hm)
        if ts["selected"] < 40:
            continue
        score = float(
            ts["mean_advantage"] * np.sqrt(max(0.0, ts["coverage"]))
            + 0.00025 * max(0.0, ts["lift"] - 1.0)
        )
        candidates.append({
            "feature": feature,
            "direction": direction,
            "quantile": q,
            "threshold_train_only": threshold,
            "train": ts,
            "holdout": hs,
            "train_score": score,
        })

    eligible = [
        x for x in candidates
        if x["train"]["mean_advantage"] > 0.0 and x["train"]["lift"] > 1.0
    ]
    eligible.sort(key=lambda x: x["train_score"], reverse=True)
    selected = eligible[0] if eligible else None

    folds = []
    positive_mean = 0
    positive_lift = 0
    if selected:
        feat = selected["feature"]
        threshold = float(selected["threshold_train_only"])
        direction = selected["direction"]
        edges = np.linspace(0, len(frame), FOLDS + 1, dtype=int)
        for i in range(FOLDS):
            z = frame.iloc[edges[i]:edges[i + 1]].copy()
            m = z[feat] <= threshold if direction == "low" else z[feat] >= threshold
            s = stat(z, m)
            if s["selected"] >= 15 and s["mean_advantage"] > 0.0:
                positive_mean += 1
            if s["selected"] >= 15 and s["lift"] > 1.0:
                positive_lift += 1
            folds.append({
                "fold": i + 1,
                "start": z.index[0].isoformat() if len(z) else None,
                "end": z.index[-1].isoformat() if len(z) else None,
                **s,
            })

    passed = bool(
        selected
        and selected["train"]["coverage"] >= 0.10
        and selected["holdout"]["coverage"] >= 0.08
        and selected["holdout"]["selected"] >= 30
        and selected["holdout"]["mean_advantage"] > 0.0
        and selected["holdout"]["lift"] > 1.05
        and positive_mean >= 4
        and positive_lift >= 4
    )

    out = {
        "study": "V99 R100 cross-engine structural consensus audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "test whether target-structure consensus between V15 and V16 identifies gate-off states "
            "where a mild 1.05x expansion of the R73/R98 parent remains positive net of severe costs; "
            "V15/V16 are sensors only and never replace or reduce the R98 core"
        ),
        "shadow_label": {
            "scale": SHADOW_SCALE,
            "cost_per_side": severe_cost,
            "advantage": "next-24h relative wealth of gate-off 1.05 shadow vs R73 parent",
            "shadow_is_not_candidate": True,
        },
        "sample": {
            "common_symbols": int(len(cols)),
            "common_start": idx[0].isoformat(),
            "common_end": idx[-1].isoformat(),
            "gate_off_daily_rows": int(len(frame)),
            "train_rows": int(len(train)),
            "holdout_rows": int(len(hold)),
            "train_end": train.index[-1].isoformat(),
            "holdout_start": hold.index[0].isoformat(),
        },
        "selection_policy": {
            "predeclared_rules": [
                {"feature": f, "direction": d, "train_quantile": q} for f, d, q in specs
            ],
            "thresholds_train_only": True,
            "one_rule_selected_by_train_only": True,
            "holdout_or_folds_cannot_change_selection": True,
            "r99_market_feature_family_reused": False,
            "v15_v16_are_structural_sensors_not_independent_votes_with_parent": True,
        },
        "all_predeclared_candidates": candidates,
        "selected_train_only": selected,
        "selected_temporal_stability": {
            "folds": folds,
            "positive_mean_folds": positive_mean,
            "positive_lift_folds": positive_lift,
        },
        "cross_engine_consensus_signal_pass": passed,
        "parent_summary_severe": r36.stats(parent.equity),
        "shadow_summary_severe": r36.stats(shadow.equity),
        "diagnostics": {
            **pdiag,
            **gdiag,
            "gate_off_fraction_common": float(off.mean()),
            "protect_fraction_common": float(protect.mean()),
        },
        "next_candidate_policy": (
            "Only if pass=true may R101 apply exactly the frozen R100 train-selected rule as a 1.05 gate-off "
            "top-up on top of R98 and then face full R98-level base/severe/super-severe/horizon/fold/random-window validation."
        ),
        "disclosure": (
            "Historical research only. Passing R100 would authorize only a new research candidate test, not live trading. "
            "Frozen V99/Paper and R98 remain untouched."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "sample": out["sample"],
        "selected": selected,
        "folds_positive_mean": positive_mean,
        "folds_positive_lift": positive_lift,
        "passed": passed,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
