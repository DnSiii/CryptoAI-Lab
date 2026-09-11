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
REPORT = PROJECT / "reports" / "v99_r99_gateoff_orthogonal_alpha_audit.json"
SHADOW_SCALE = 1.05
FOLDS = 5


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


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["severe_cost_per_side"])
    parent, parent_targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    off = ~gate

    shadow_targets = parent_targets.copy()
    if off.any():
        shadow_targets.loc[off, :] = shadow_targets.loc[off, :] * SHADOW_SCALE
    shadow_targets = cap(shadow_targets, float(r86.P15["gross_cap"]))
    shadow = r36.run(data, shadow_targets, ex, cost, float(r86.P15["gross_cap"]), guard)

    idx = parent.equity.index.intersection(shadow.equity.index)
    peq = parent.equity.reindex(idx).astype(float)
    seq = shadow.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    targ = parent_targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    protect = protect.reindex(idx).fillna(False).astype(bool)
    gate = gate.reindex(idx).fillna(False).astype(bool)
    off = ~gate

    advantage = (seq.shift(-24) / seq) / (peq.shift(-24) / peq) - 1.0
    coin24 = close.pct_change(24, fill_method=None)
    coin72 = close.pct_change(72, fill_method=None)
    btc = close["BTCUSDT"].astype(float)
    gross_s = targ.abs().sum(axis=1)
    net_s = targ.sum(axis=1)
    long_g = targ.clip(lower=0.0).sum(axis=1)
    short_g = (-targ.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([long_g, short_g], axis=1).max(axis=1)

    l1_24 = targ.diff(24).abs().sum(axis=1)
    gross_lag24 = gross_s.shift(24)
    stability24 = 1.0 - l1_24 / (gross_s + gross_lag24).replace(0.0, np.nan)
    sign_now = np.sign(targ)
    sign_lag = np.sign(targ.shift(24))
    active_pair = (targ.abs() > 1e-9) | (targ.shift(24).abs() > 1e-9)
    flips = ((sign_now != sign_lag) & active_pair).sum(axis=1) / active_pair.sum(axis=1).replace(0, np.nan)

    f = pd.DataFrame(index=idx)
    # Deliberately exclude strategy_r72 and absolute gross_current: those already drive R88/R97.
    f["strategy_r24"] = peq.pct_change(24, fill_method=None)
    f["strategy_r168"] = peq.pct_change(168, fill_method=None)
    f["strategy_dd"] = 1.0 - peq / peq.cummax()
    f["btc_r24"] = btc.pct_change(24, fill_method=None)
    f["btc_r72"] = btc.pct_change(72, fill_method=None)
    f["btc_r168"] = btc.pct_change(168, fill_method=None)
    f["market_med24"] = coin24.median(axis=1)
    f["market_med72"] = coin72.median(axis=1)
    f["market_abs24"] = coin24.abs().median(axis=1)
    f["cross_vol24"] = coin24.std(axis=1)
    f["breadth24"] = (coin24 > 0.0).mean(axis=1)
    f["breadth72"] = (coin72 > 0.0).mean(axis=1)
    f["net_btc_alignment24"] = np.sign(net_s) * f["btc_r24"]
    f["net_btc_alignment72"] = np.sign(net_s) * f["btc_r72"]
    f["dominant_side_share"] = dominant / gross_s.replace(0.0, np.nan)
    f["net_abs_share"] = net_s.abs() / gross_s.replace(0.0, np.nan)
    f["target_stability24"] = stability24
    f["sign_flip_fraction24"] = flips
    f["gross_change24"] = (gross_s - gross_lag24).abs()
    f["protect_active"] = protect.astype(float)

    sample_idx = idx[::24]
    frame = f.reindex(sample_idx).copy()
    frame["advantage"] = advantage.reindex(sample_idx)
    frame["gate_off"] = off.reindex(sample_idx).astype(bool)
    frame = frame.loc[frame["gate_off"]].drop(columns=["gate_off"])
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_index()

    split = int(len(frame) * 0.60)
    split = max(1, min(len(frame)-1, split))
    train = frame.iloc[:split].copy()
    hold = frame.iloc[split:].copy()
    features = list(f.columns)

    candidates = []
    for feature in features:
        for direction, q in (("low", 0.20), ("high", 0.80)):
            threshold = float(train[feature].quantile(q))
            tm = train[feature] <= threshold if direction == "low" else train[feature] >= threshold
            hm = hold[feature] <= threshold if direction == "low" else hold[feature] >= threshold
            ts = stat(train, tm)
            hs = stat(hold, hm)
            if ts["selected"] < 40:
                continue
            score = float(ts["mean_advantage"] * np.sqrt(max(0.0, ts["coverage"])) + 0.00025 * max(0.0, ts["lift"] - 1.0))
            candidates.append({
                "feature": feature,
                "direction": direction,
                "quantile": q,
                "threshold_train_only": threshold,
                "train": ts,
                "holdout": hs,
                "train_score": score,
            })

    eligible = [x for x in candidates if x["train"]["mean_advantage"] > 0.0 and x["train"]["lift"] > 1.0]
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
            z = frame.iloc[edges[i]:edges[i+1]].copy()
            m = z[feat] <= threshold if direction == "low" else z[feat] >= threshold
            s = stat(z, m)
            if s["selected"] >= 15 and s["mean_advantage"] > 0:
                positive_mean += 1
            if s["selected"] >= 15 and s["lift"] > 1.0:
                positive_lift += 1
            folds.append({
                "fold": i+1,
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
        "study": "V99 R99 gate-off orthogonal alpha audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "inside the roughly 80% of daily states where the frozen R88/R98 72h expansion gate is off, test whether one independent causal regime supports a mild 1.05x shadow exposure increase net of severe costs; strategy_r72 and absolute gross_current are explicitly excluded to avoid rediscovering R88/R97",
        "shadow_label": {
            "scale": SHADOW_SCALE,
            "cost_per_side": cost,
            "advantage": "next-24h relative wealth of gate-off 1.05 shadow vs R73 parent",
            "shadow_is_not_candidate": True,
        },
        "sample": {
            "gate_off_daily_rows": int(len(frame)),
            "train_rows": int(len(train)),
            "holdout_rows": int(len(hold)),
            "train_end": train.index[-1].isoformat(),
            "holdout_start": hold.index[0].isoformat(),
        },
        "selection_policy": {
            "features": features,
            "explicitly_excluded": ["strategy_r72", "gross_current/parent_gross"],
            "thresholds": "q20/q80 fitted first 60% only",
            "one_rule_selected_by_train_only": True,
            "holdout_or_folds_cannot_change_selection": True,
        },
        "selected_train_only": selected,
        "selected_temporal_stability": {"folds": folds, "positive_mean_folds": positive_mean, "positive_lift_folds": positive_lift},
        "orthogonal_gateoff_signal_pass": passed,
        "top_train_candidates": eligible[:10],
        "parent_summary_severe": r36.stats(parent.equity),
        "shadow_summary_severe": r36.stats(shadow.equity),
        "diagnostics": {**pdiag, **gdiag, "gate_off_fraction": float(off.mean())},
        "next_candidate_policy": "Only if pass=true may R100 add a 1.05 gate-off sleeve using exactly the frozen R99 rule on top of R98; no second-best rule may be substituted after holdout.",
        "disclosure": "Historical research only. Future returns are labels only. Frozen V99/Paper and R98 remain untouched.",
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
