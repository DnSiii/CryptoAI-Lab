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

REPORT = PROJECT / "reports" / "v99_r85_selective_release_audit.json"
GROSS_THRESHOLD = 0.4478403629219058


def gate_stats(frame: pd.DataFrame, gate: pd.Series) -> dict:
    x = frame.copy()
    g = gate.reindex(x.index).fillna(False).astype(bool)
    y = x["release_material"].astype(bool)
    base = float(y.mean()) if len(y) else 0.0
    if not g.any():
        return {"rows": int(len(x)), "selected": 0, "coverage": 0.0, "base_rate": base, "event_rate": 0.0, "lift": 0.0, "mean_release_advantage": 0.0, "event_capture": 0.0}
    rate = float(y.loc[g].mean())
    return {
        "rows": int(len(x)),
        "selected": int(g.sum()),
        "coverage": float(g.mean()),
        "base_rate": base,
        "event_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
        "mean_release_advantage": float(x.loc[g, "release_advantage"].mean()),
        "event_capture": float(y.loc[g].sum() / max(1, int(y.sum()))),
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)
    p15, p25 = r55.params(0.15), r55.params(0.25)
    res15, _, t15, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)
    res25, _, _, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p25, shadow=shadow)

    idx = res15.equity.index.intersection(res25.equity.index)
    e15 = res15.equity.reindex(idx).astype(float)
    e25 = res25.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    t15 = t15.reindex(index=idx, columns=close.columns).fillna(0.0)

    r24 = close.pct_change(24, fill_method=None)
    market_abs24 = r24.abs().median(axis=1)
    market_med24 = r24.median(axis=1)
    breadth24 = (r24 > 0).mean(axis=1)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None)
    btc72 = close["BTCUSDT"].pct_change(72, fill_method=None)
    h15_gross = t15.abs().sum(axis=1)
    h15_net = t15.sum(axis=1)
    long_gross = t15.clip(lower=0).sum(axis=1)
    short_gross = (-t15.clip(upper=0)).sum(axis=1)
    dominant_share = pd.concat([long_gross, short_gross], axis=1).max(axis=1) / h15_gross.replace(0.0, np.nan)
    strat_r24 = e15.pct_change(24, fill_method=None)
    strat_dd = 1.0 - e15 / e15.cummax()

    raw_gate = (h15_gross <= GROSS_THRESHOLD).fillna(False)
    daily_idx = idx[::24]
    rows = []
    for t in daily_idx:
        pos = idx.get_loc(t)
        if not isinstance(pos, (int, np.integer)) or pos + 48 >= len(idx):
            continue
        t24 = idx[pos+24]
        t48 = idx[pos+48]
        if not bool(raw_gate.loc[t]) or bool(raw_gate.loc[t24]):
            continue
        h15_w = e15.loc[t48] / e15.loc[t24]
        h25_w = e25.loc[t48] / e25.loc[t24]
        release_adv = float(h15_w / h25_w - 1.0)
        rows.append({
            "t": t24,
            "release_advantage": release_adv,
            "release_material": release_adv > 0.002,
            "btc_r24": float(btc24.loc[t24]),
            "btc_r72": float(btc72.loc[t24]),
            "market_abs24": float(market_abs24.loc[t24]),
            "market_med24": float(market_med24.loc[t24]),
            "breadth24": float(breadth24.loc[t24]),
            "h15_gross": float(h15_gross.loc[t24]),
            "h15_net_abs": float(abs(h15_net.loc[t24])),
            "dominant_share": float(dominant_share.loc[t24]) if pd.notna(dominant_share.loc[t24]) else 0.0,
            "strategy_r24": float(strat_r24.loc[t24]),
            "strategy_dd": float(strat_dd.loc[t24]),
        })

    frame = pd.DataFrame(rows).set_index("t").replace([np.inf, -np.inf], np.nan).dropna().sort_index()
    split = int(len(frame) * 0.60)
    train = frame.iloc[:split]
    hold = frame.iloc[split:]
    features = [c for c in frame.columns if c not in ("release_advantage", "release_material")]

    candidates = []
    for f in features:
        for direction, q in (("low", 0.20), ("high", 0.80)):
            thr = float(train[f].quantile(q))
            tr_gate = train[f] <= thr if direction == "low" else train[f] >= thr
            ho_gate = hold[f] <= thr if direction == "low" else hold[f] >= thr
            tr = gate_stats(train, tr_gate)
            ho = gate_stats(hold, ho_gate)
            candidates.append({
                "feature": f,
                "direction": direction,
                "threshold_train_only": thr,
                "train": tr,
                "holdout": ho,
            })

    eligible = [x for x in candidates if x["train"]["selected"] >= 10 and x["train"]["mean_release_advantage"] > 0.0]
    eligible.sort(key=lambda x: (x["train"]["lift"], x["train"]["mean_release_advantage"], x["train"]["event_capture"]), reverse=True)
    selected = eligible[0] if eligible else None

    temporal = None
    if selected:
        f = selected["feature"]
        thr = selected["threshold_train_only"]
        direction = selected["direction"]
        edges = np.linspace(0, len(frame), 6, dtype=int)
        folds = []
        for i in range(5):
            z = frame.iloc[edges[i]:edges[i+1]]
            g = z[f] <= thr if direction == "low" else z[f] >= thr
            folds.append({
                "fold": i+1,
                "start": z.index[0].isoformat() if len(z) else None,
                "end": z.index[-1].isoformat() if len(z) else None,
                **gate_stats(z, g),
            })
        temporal = {
            "folds": folds,
            "positive_mean_folds": int(sum(1 for x in folds if x["selected"] >= 3 and x["mean_release_advantage"] > 0.0)),
            "positive_lift_folds": int(sum(1 for x in folds if x["selected"] >= 3 and x["lift"] > 1.0)),
        }

    passed = bool(
        selected
        and selected["holdout"]["selected"] >= 8
        and selected["holdout"]["mean_release_advantage"] > 0.0
        and selected["holdout"]["lift"] > 1.10
        and temporal
        and temporal["positive_mean_folds"] >= 4
    )

    out = {
        "study": "V99 R85 selective early-release audit after h15-gross-low clears",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "among daily R73 trigger episodes whose frozen h15-gross-low gate clears at the next daily decision, select on the first 60% only one simple causal feature that identifies when releasing h0.25 back to h0.15 is materially beneficial over the following 24h",
        "clear_event_rows": int(len(frame)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(hold)),
        "selection_policy": "10 generic causal features; q20/q80 thresholds fitted on first 60% only; choose by train lift among gates with positive train mean release advantage; holdout never influences selection",
        "selected_train_only": selected,
        "selected_temporal_stability": temporal,
        "selective_release_signal_pass": passed,
        "top_train_candidates": eligible[:10],
        "disclosure": "Diagnostic only. Future h15/h25 wealth appears only in release labels. Any selected threshold is frozen before holdout and must pass temporal stability before a candidate state machine is tested. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "rows": len(frame), "selected": selected, "temporal": temporal, "passed": passed}, indent=2), flush=True)


if __name__ == "__main__":
    main()
