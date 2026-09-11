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
r86 = r88.r86
cap = r88.cap
REPORT = PROJECT / "reports" / "v99_r97_scale115_friction_audit.json"
SCALE_BASE = 1.10
SCALE_HIGH = 1.15
FOLDS = 5


def apply_scale(data, ex, guard, cost, parent_targets, gate, scale):
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * float(scale)
    targets = cap(targets, float(r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r86.P15["gross_cap"]), guard)
    return result, targets


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    if den <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / den)


def rule_stats(df: pd.DataFrame, mask: pd.Series) -> dict:
    sub = df.loc[mask]
    base_pos = float((df["delta_logret_24"] > 0).mean()) if len(df) else 0.0
    sel_pos = float((sub["delta_logret_24"] > 0).mean()) if len(sub) else 0.0
    return {
        "rows": int(len(df)),
        "selected": int(len(sub)),
        "coverage": float(len(sub) / max(1, len(df))),
        "base_positive_rate": base_pos,
        "selected_positive_rate": sel_pos,
        "lift": float(sel_pos / max(1e-12, base_pos)) if base_pos > 0 else 0.0,
        "mean_delta_logret_24": float(sub["delta_logret_24"].mean()) if len(sub) else 0.0,
        "median_delta_logret_24": float(sub["delta_logret_24"].median()) if len(sub) else 0.0,
        "mean_delta_simple_24": float(sub["delta_simple_24"].mean()) if len(sub) else 0.0,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["severe_cost_per_side"])

    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    res110, tgt110 = apply_scale(data, ex, guard, cost, parent_targets, gate, SCALE_BASE)
    res115, tgt115 = apply_scale(data, ex, guard, cost, parent_targets, gate, SCALE_HIGH)

    idx = parent_targets.index
    rows = []
    decision_positions = np.arange(0, len(idx) - 24, 24, dtype=int)
    for pos in decision_positions:
        if pos < 72 or not bool(gate.iloc[pos]):
            continue
        t = idx[pos]
        cur = parent_targets.iloc[pos].astype(float).to_numpy()
        lag24 = parent_targets.iloc[pos - 24].astype(float).to_numpy()
        lag72 = parent_targets.iloc[pos - 72].astype(float).to_numpy()
        abs_cur = np.abs(cur)
        abs24 = np.abs(lag24)
        gross_cur = float(abs_cur.sum())
        gross24 = float(abs24.sum())
        gross72 = float(np.abs(lag72).sum())
        l1_24 = float(np.abs(cur - lag24).sum())
        l1_72 = float(np.abs(cur - lag72).sum())
        active = (abs_cur > 1e-9) | (abs24 > 1e-9)
        if active.any():
            flips = np.sign(cur[active]) != np.sign(lag24[active])
            flip_fraction = float(np.mean(flips))
        else:
            flip_fraction = 0.0
        concentration = float(np.sum((abs_cur / max(1e-12, gross_cur)) ** 2)) if gross_cur > 0 else 0.0
        stability24 = float(1.0 - l1_24 / max(1e-12, gross_cur + gross24))
        stability72 = float(1.0 - l1_72 / max(1e-12, gross_cur + gross72))
        future_pos = pos + 24
        eq110_t = float(res110.equity.iloc[pos])
        eq110_f = float(res110.equity.iloc[future_pos])
        eq115_t = float(res115.equity.iloc[pos])
        eq115_f = float(res115.equity.iloc[future_pos])
        r110 = eq110_f / max(1e-12, eq110_t) - 1.0
        r115 = eq115_f / max(1e-12, eq115_t) - 1.0
        log110 = np.log(max(1e-12, eq110_f) / max(1e-12, eq110_t))
        log115 = np.log(max(1e-12, eq115_f) / max(1e-12, eq115_t))
        rows.append({
            "time": t,
            "target_l1_change_24": l1_24,
            "target_l1_change_72": l1_72,
            "target_stability_24": stability24,
            "target_stability_72": stability72,
            "target_cosine_24": cosine(cur, lag24),
            "target_cosine_72": cosine(cur, lag72),
            "sign_flip_fraction_24": flip_fraction,
            "gross_change_24": abs(gross_cur - gross24),
            "gross_current": gross_cur,
            "concentration_hhi": concentration,
            "delta_logret_24": float(log115 - log110),
            "delta_simple_24": float(r115 - r110),
        })

    df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
    if len(df) < 50:
        raise RuntimeError(f"not enough R97 observations: {len(df)}")
    cut = max(1, min(len(df) - 1, int(np.floor(len(df) * 0.60))))
    train = df.iloc[:cut].copy()
    hold = df.iloc[cut:].copy()

    features = [
        "target_l1_change_24",
        "target_l1_change_72",
        "target_stability_24",
        "target_stability_72",
        "target_cosine_24",
        "target_cosine_72",
        "sign_flip_fraction_24",
        "gross_change_24",
        "gross_current",
        "concentration_hhi",
    ]
    candidates = []
    for feature in features:
        for q, direction in ((0.20, "low"), (0.80, "high")):
            threshold = float(train[feature].quantile(q))
            train_mask = train[feature] <= threshold if direction == "low" else train[feature] >= threshold
            hold_mask = hold[feature] <= threshold if direction == "low" else hold[feature] >= threshold
            ts = rule_stats(train, train_mask)
            hs = rule_stats(hold, hold_mask)
            score = float(ts["mean_delta_logret_24"] * np.sqrt(max(0.0, ts["coverage"])))
            candidates.append({
                "feature": feature,
                "direction": direction,
                "quantile": q,
                "threshold_train_only": threshold,
                "train": ts,
                "holdout": hs,
                "train_score": score,
            })

    candidates.sort(key=lambda x: x["train_score"], reverse=True)
    selected = candidates[0]
    feature = selected["feature"]
    threshold = float(selected["threshold_train_only"])
    direction = selected["direction"]

    folds = []
    bounds = np.linspace(0, len(df), FOLDS + 1, dtype=int)
    for i in range(FOLDS):
        part = df.iloc[bounds[i]:bounds[i + 1]].copy()
        if direction == "low":
            mask = part[feature] <= threshold
        else:
            mask = part[feature] >= threshold
        stat = rule_stats(part, mask)
        folds.append({
            "fold": i + 1,
            "start": part["time"].iloc[0].isoformat() if len(part) else None,
            "end": part["time"].iloc[-1].isoformat() if len(part) else None,
            **stat,
        })

    positive_mean_folds = int(sum(x["mean_delta_logret_24"] > 0 for x in folds))
    positive_lift_folds = int(sum(x["lift"] > 1.0 for x in folds))
    overall_delta = float(df["delta_logret_24"].mean())
    signal_pass = bool(
        selected["train"]["mean_delta_logret_24"] > 0
        and selected["holdout"]["mean_delta_logret_24"] > 0
        and selected["holdout"]["lift"] > 1.0
        and selected["train"]["coverage"] >= 0.10
        and selected["holdout"]["coverage"] >= 0.08
        and positive_mean_folds >= 4
        and positive_lift_folds >= 4
    )

    out = {
        "study": "V99 R97 severe-cost friction audit for R88 1.10 to R96 1.15 increment",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "identify on the first 60% of R88 gate decisions a simple causal target-stability/turnover state where the incremental 1.10-to-1.15 exposure remains net-positive over the next 24h under severe costs, then validate the unchanged rule on the final 40% and five chronological folds",
        "context": {
            "r96_full_wealth_ratio_vs_r88": 1.067124953726378,
            "r96_holdout_wealth_ratio_vs_r88": 1.0620721534555617,
            "r96_severe_wealth_ratio_vs_r88": 0.9995899669212348,
            "r96_super_severe_wealth_ratio_vs_r88": 0.941079747620243,
            "problem_to_solve": "retain R96 growth alpha while avoiding the states where the extra 0.05 scale cannot pay its friction",
        },
        "policy": {
            "threshold_source": "first 60% only",
            "candidate_features": features,
            "thresholds": "q20/q80 per feature fitted only on first 60%",
            "selection": "single rule chosen only by train mean severe-cost delta times sqrt coverage",
            "holdout_and_folds_cannot_change_rule": True,
            "future_returns_are_labels_only": True,
        },
        "observations": {
            "gate_decisions": int(len(df)),
            "train": int(len(train)),
            "holdout": int(len(hold)),
            "train_end": train["time"].iloc[-1].isoformat(),
            "holdout_start": hold["time"].iloc[0].isoformat(),
            "overall_mean_delta_logret_24_115_minus_110": overall_delta,
        },
        "selected_train_only": selected,
        "selected_temporal_stability": {
            "folds": folds,
            "positive_mean_folds": positive_mean_folds,
            "positive_lift_folds": positive_lift_folds,
        },
        "friction_signal_pass": signal_pass,
        "top_train_candidates": candidates[:10],
        "diagnostics": {
            **pdiag,
            **gdiag,
            "severe_cost_per_side": cost,
            "scale_base": SCALE_BASE,
            "scale_high": SCALE_HIGH,
            "protect_overlap_fraction": float((gate & protect.reindex(gate.index).fillna(False)).mean()),
        },
        "next_candidate_policy": "Only if friction_signal_pass=true may a future R98 keep R88 1.10 as the gate floor and elevate to 1.15 exclusively when the frozen R97 rule is true. No second-best rule may be selected after seeing holdout.",
        "disclosure": "Historical research only. R97 is diagnostic and does not modify Frozen V99, official paper, R73 or R88.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "observations": out["observations"],
        "selected": selected,
        "folds_positive_mean": positive_mean_folds,
        "folds_positive_lift": positive_lift_folds,
        "friction_signal_pass": signal_pass,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
