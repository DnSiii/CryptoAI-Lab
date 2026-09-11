from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r86_tristate_hedge_router as r86

REPORT = PROJECT / "reports" / "v99_r87_exposure_expansion_audit.json"
SCALE = 1.10  # predeclared mild expansion used only to construct labels
MATERIAL = 0.002


def gate_stats(frame: pd.DataFrame, gate: pd.Series) -> dict:
    g = gate.reindex(frame.index).fillna(False).astype(bool)
    y = frame["material_win"].astype(bool)
    base = float(y.mean()) if len(y) else 0.0
    if not g.any():
        return {"rows": int(len(frame)), "selected": 0, "coverage": 0.0, "base_rate": base, "event_rate": 0.0, "lift": 0.0, "mean_advantage": 0.0, "event_capture": 0.0}
    rate = float(y.loc[g].mean())
    return {
        "rows": int(len(frame)),
        "selected": int(g.sum()),
        "coverage": float(g.mean()),
        "base_rate": base,
        "event_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
        "mean_advantage": float(frame.loc[g, "advantage"].mean()),
        "event_capture": float(y.loc[g].sum() / max(1, int(y.sum()))),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r86.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, targets, protect, pdiag, _ = r86.build_parent_r73(data, raw, ex, guard, gross, cost)
    expanded_targets = r86.cap(targets * SCALE, float(r86.P15["gross_cap"]))
    expanded = r86.r36.run(data, expanded_targets, ex, cost, float(r86.P15["gross_cap"]), guard)

    idx = parent.equity.index.intersection(expanded.equity.index)
    peq = parent.equity.reindex(idx).astype(float)
    xeq = expanded.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    targ = targets.reindex(index=idx, columns=close.columns).fillna(0.0)
    protect = protect.reindex(idx).fillna(False).astype(bool)

    advantage = (xeq.shift(-24) / xeq) / (peq.shift(-24) / peq) - 1.0
    coin24 = close.pct_change(24, fill_method=None)
    coin72 = close.pct_change(72, fill_method=None)
    btc = close["BTCUSDT"]
    gross_s = targ.abs().sum(axis=1)
    net_s = targ.sum(axis=1)
    long_g = targ.clip(lower=0.0).sum(axis=1)
    short_g = (-targ.clip(upper=0.0)).sum(axis=1)
    dominant = pd.concat([long_g, short_g], axis=1).max(axis=1)

    f = pd.DataFrame(index=idx)
    f["strategy_r24"] = peq.pct_change(24, fill_method=None)
    f["strategy_r72"] = peq.pct_change(72, fill_method=None)
    f["strategy_dd"] = 1.0 - peq / peq.cummax()
    f["btc_r24"] = btc.pct_change(24, fill_method=None)
    f["btc_r72"] = btc.pct_change(72, fill_method=None)
    f["market_med24"] = coin24.median(axis=1)
    f["market_abs24"] = coin24.abs().median(axis=1)
    f["cross_vol24"] = coin24.std(axis=1)
    f["breadth24"] = (coin24 > 0.0).mean(axis=1)
    f["breadth72"] = (coin72 > 0.0).mean(axis=1)
    f["parent_gross"] = gross_s
    f["parent_net_abs"] = net_s.abs()
    f["dominant_side_share"] = dominant / gross_s.replace(0.0, np.nan)
    f["protect_active"] = protect.astype(float)
    f["net_btc_alignment24"] = np.sign(net_s) * f["btc_r24"]

    sample_idx = idx[::24]
    frame = f.reindex(sample_idx).copy()
    frame["advantage"] = advantage.reindex(sample_idx)
    frame["material_win"] = frame["advantage"] > MATERIAL
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().sort_index()

    split = int(len(frame) * 0.60)
    train = frame.iloc[:split]
    hold = frame.iloc[split:]
    features = list(f.columns)

    candidates = []
    for feature in features:
        for direction, q in (("low", 0.20), ("high", 0.80)):
            threshold = float(train[feature].quantile(q))
            tg = train[feature] <= threshold if direction == "low" else train[feature] >= threshold
            hg = hold[feature] <= threshold if direction == "low" else hold[feature] >= threshold
            tr = gate_stats(train, tg)
            ho = gate_stats(hold, hg)
            if tr["selected"] < 30:
                continue
            score = tr["lift"] + 100.0 * max(0.0, tr["mean_advantage"]) + 0.25 * tr["event_capture"]
            candidates.append({
                "feature": feature,
                "direction": direction,
                "threshold_train_only": threshold,
                "train": tr,
                "holdout": ho,
                "train_selection_score": float(score),
            })

    eligible = [x for x in candidates if x["train"]["mean_advantage"] > 0.0 and x["train"]["lift"] > 1.0]
    eligible.sort(key=lambda x: (x["train_selection_score"], x["train"]["lift"], x["train"]["event_capture"]), reverse=True)
    selected = eligible[0] if eligible else None

    temporal = None
    if selected:
        feature = selected["feature"]
        direction = selected["direction"]
        threshold = selected["threshold_train_only"]
        edges = np.linspace(0, len(frame), 6, dtype=int)
        folds = []
        for i in range(5):
            z = frame.iloc[edges[i]:edges[i+1]]
            g = z[feature] <= threshold if direction == "low" else z[feature] >= threshold
            folds.append({
                "fold": i + 1,
                "start": z.index[0].isoformat() if len(z) else None,
                "end": z.index[-1].isoformat() if len(z) else None,
                **gate_stats(z, g),
            })
        temporal = {
            "folds": folds,
            "positive_mean_folds": int(sum(1 for z in folds if z["selected"] >= 10 and z["mean_advantage"] > 0.0)),
            "positive_lift_folds": int(sum(1 for z in folds if z["selected"] >= 10 and z["lift"] > 1.0)),
        }

    passed = bool(
        selected
        and selected["holdout"]["selected"] >= 20
        and selected["holdout"]["mean_advantage"] > 0.0
        and selected["holdout"]["lift"] > 1.10
        and temporal
        and temporal["positive_mean_folds"] >= 4
        and temporal["positive_lift_folds"] >= 4
    )

    out = {
        "study": "V99 R87 fresh R73 exposure-expansion opportunity audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "using a predeclared 1.10x capped shadow expansion only to create labels, identify on the first 60% one simple causal daily regime where greater R73 exposure adds next-24h wealth; validate unchanged on the final 40% and five chronological folds",
        "label_variant": {
            "scale": SCALE,
            "gross_cap": float(r86.P15["gross_cap"]),
            "material_advantage": MATERIAL,
            "candidate_not_promoted": True,
        },
        "parent_summary": r86.r36.stats(peq),
        "expanded_shadow_summary": r86.r36.stats(xeq),
        "parent_diagnostics": pdiag,
        "daily_rows": int(len(frame)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "selection_policy": "15 generic causal features; q20/q80 thresholds fit on first 60% only; selected only from train statistics; holdout and folds never alter the threshold",
        "selected_train_only": selected,
        "selected_temporal_stability": temporal,
        "expansion_signal_pass": passed,
        "top_train_candidates": eligible[:12],
        "disclosure": "Diagnostic only. The 1.10x expanded path is used only to construct causal forward labels and is not a candidate. Future returns never enter features. Any rule must survive holdout/folds before a separate candidate is built. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "selected": selected, "temporal": temporal, "passed": passed}, indent=2), flush=True)


if __name__ == "__main__":
    main()
