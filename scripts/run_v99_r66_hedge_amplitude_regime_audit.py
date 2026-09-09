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

REPORT = PROJECT / "reports" / "v99_r66_hedge_amplitude_regime_audit.json"


def auc(values: pd.Series, labels: pd.Series) -> float:
    x = pd.concat([values.rename("x"), labels.rename("y")], axis=1).dropna()
    if x.empty:
        return 0.5
    y = x["y"].astype(bool)
    n1 = int(y.sum()); n0 = int((~y).sum())
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = x["x"].rank(method="average")
    u = float(ranks[y].sum()) - n1 * (n1 + 1) / 2.0
    return float(u / (n1 * n0))


def gated_stats(values: pd.Series, labels: pd.Series, threshold: float, direction: str) -> dict:
    x = pd.concat([values.rename("x"), labels.rename("y")], axis=1).dropna()
    if x.empty:
        return {"rows": 0, "coverage": 0.0, "event_rate": 0.0, "lift": 0.0}
    mask = x["x"] >= threshold if direction == "high" else x["x"] <= threshold
    base = float(x["y"].astype(bool).mean())
    rate = float(x.loc[mask, "y"].astype(bool).mean()) if mask.any() else 0.0
    return {
        "rows": int(len(x)),
        "selected_rows": int(mask.sum()),
        "coverage": float(mask.mean()),
        "base_event_rate": base,
        "event_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
    }


def stress_age(active: pd.Series) -> pd.Series:
    a = active.fillna(False).astype(bool)
    starts = a & ~a.shift(1, fill_value=False)
    group = starts.cumsum()
    age = a.groupby(group).cumcount() + 1
    return age.where(a, 0).astype(float)


def forward_relative(eq25: pd.Series, eq15: pd.Series, hours: int) -> pd.Series:
    r25 = eq25.shift(-hours) / eq25 - 1.0
    r15 = eq15.shift(-hours) / eq15 - 1.0
    return (1.0 + r25) / (1.0 + r15) - 1.0


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)

    p15 = r55.params(0.15); p25 = r55.params(0.25)
    res15, _, t15, active15 = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)
    res25, _, t25, active25 = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p25, shadow=shadow)

    idx = res15.equity.index.intersection(res25.equity.index)
    eq15 = res15.equity.reindex(idx).astype(float)
    eq25 = res25.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    rawx = raw.reindex(index=idx, columns=close.columns).fillna(0.0)
    t15 = t15.reindex(index=idx, columns=close.columns).fillna(0.0)
    active = active15.reindex(idx).fillna(False).astype(bool)

    btc = close["BTCUSDT"]
    coin_r24 = close.pct_change(24, fill_method=None)
    long_gross = rawx.clip(lower=0.0).sum(axis=1)
    short_gross = (-rawx.clip(upper=0.0)).sum(axis=1)
    raw_net = rawx.sum(axis=1)
    t15_net = t15.sum(axis=1)
    rel = eq25 / eq15
    dd15 = eq15 / eq15.cummax() - 1.0

    features = pd.DataFrame(index=idx)
    features["dd_abs"] = (-dd15).clip(lower=0.0)
    features["strategy_r6"] = eq15.pct_change(6, fill_method=None)
    features["strategy_r24"] = eq15.pct_change(24, fill_method=None)
    features["strategy_r72"] = eq15.pct_change(72, fill_method=None)
    features["btc_r6"] = btc.pct_change(6, fill_method=None)
    features["btc_r24"] = btc.pct_change(24, fill_method=None)
    features["btc_r72"] = btc.pct_change(72, fill_method=None)
    features["breadth_negative_24h"] = (coin_r24 < 0.0).mean(axis=1)
    features["market_abs_median_24h"] = coin_r24.abs().median(axis=1)
    features["cross_vol_24h"] = coin_r24.std(axis=1)
    features["raw_gross"] = rawx.abs().sum(axis=1)
    features["raw_net_abs"] = raw_net.abs()
    features["raw_dominant"] = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    features["h15_gross"] = t15.abs().sum(axis=1)
    features["h15_net_abs"] = t15_net.abs()
    features["net_btc_alignment24"] = np.sign(raw_net) * features["btc_r24"]
    features["net_btc_alignment72"] = np.sign(raw_net) * features["btc_r72"]
    features["stress_active"] = active.astype(float)
    features["stress_age_hours"] = stress_age(active)
    features["h25_relative_24h"] = rel.pct_change(24, fill_method=None)
    features["h25_relative_72h"] = rel.pct_change(72, fill_method=None)
    features["h25_relative_168h"] = rel.pct_change(168, fill_method=None)

    advantage24 = forward_relative(eq25, eq15, 24)
    advantage72 = forward_relative(eq25, eq15, 72)
    labels = {
        "h25_win_24h": advantage24 > 0.0,
        "h25_win_72h": advantage72 > 0.0,
        "h25_material_win_72h_20bp": advantage72 > 0.002,
    }

    # One observation per day to reduce overlap and serial duplication.
    sample_idx = idx[::24]
    features = features.reindex(sample_idx)
    labels = {k: v.reindex(sample_idx) for k, v in labels.items()}
    adv = {"24h": advantage24.reindex(sample_idx), "72h": advantage72.reindex(sample_idx)}

    valid = features.notna().sum(axis=1) >= max(1, len(features.columns) // 2)
    sample_idx = features.index[valid]
    features = features.loc[sample_idx]
    labels = {k: v.loc[sample_idx] for k, v in labels.items()}
    adv = {k: v.loc[sample_idx] for k, v in adv.items()}

    split = int(len(sample_idx) * 0.60)
    train_idx = sample_idx[:split]
    hold_idx = sample_idx[split:]

    rankings = {}
    for label_name, y in labels.items():
        base_train = float(y.loc[train_idx].dropna().mean())
        base_hold = float(y.loc[hold_idx].dropna().mean())
        rows = []
        for name in features.columns:
            tr = pd.concat([features.loc[train_idx, name], y.loc[train_idx]], axis=1).dropna()
            ho = pd.concat([features.loc[hold_idx, name], y.loc[hold_idx]], axis=1).dropna()
            if len(tr) < 40 or len(ho) < 20:
                continue
            a_tr = auc(tr.iloc[:, 0], tr.iloc[:, 1])
            a_ho = auc(ho.iloc[:, 0], ho.iloc[:, 1])
            direction = "high" if a_tr >= 0.5 else "low"
            q = 0.80 if direction == "high" else 0.20
            threshold = float(tr.iloc[:, 0].quantile(q))
            gtr = gated_stats(tr.iloc[:, 0], tr.iloc[:, 1], threshold, direction)
            gho = gated_stats(ho.iloc[:, 0], ho.iloc[:, 1], threshold, direction)
            rows.append({
                "feature": name,
                "direction": direction,
                "train_auc": float(a_tr),
                "holdout_auc": float(a_ho),
                "train_strength": float(max(a_tr, 1.0 - a_tr)),
                "holdout_strength": float(max(a_ho, 1.0 - a_ho)),
                "stable_strength": float(min(max(a_tr, 1.0 - a_tr), max(a_ho, 1.0 - a_ho))),
                "train_q80_or_q20_threshold": threshold,
                "train_gate": gtr,
                "holdout_gate": gho,
            })
        rows.sort(key=lambda z: (
            min(z["train_gate"]["lift"], z["holdout_gate"]["lift"]),
            z["stable_strength"],
            z["holdout_gate"]["coverage"],
        ), reverse=True)
        rankings[label_name] = {
            "base_event_rate_train": base_train,
            "base_event_rate_holdout": base_hold,
            "features": rows,
        }

    out = {
        "study": "V99 R66 hedge-amplitude regime audit: h0.25 vs h0.15",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "identify causal regimes in which the stronger R55 h0.25 hedge outperforms h0.15 over the next 24h/72h, "
            "using a fixed chronological 60/40 split, so a future router can seek h0.15 one-year upside and h0.25 historical/severe robustness"
        ),
        "variants": {"h15": p15, "h25": p25},
        "h15_summary": r55.r36.stats(eq15),
        "h25_summary": r55.r36.stats(eq25),
        "daily_sample_rows": int(len(sample_idx)),
        "train_rows": int(len(train_idx)),
        "holdout_rows": int(len(hold_idx)),
        "train_end": train_idx[-1].isoformat() if len(train_idx) else None,
        "future_advantage": {
            "24h_train_median": float(adv["24h"].loc[train_idx].median()),
            "24h_holdout_median": float(adv["24h"].loc[hold_idx].median()),
            "72h_train_median": float(adv["72h"].loc[train_idx].median()),
            "72h_holdout_median": float(adv["72h"].loc[hold_idx].median()),
        },
        "rankings": rankings,
        "disclosure": (
            "Diagnostic historical research only. Future h0.25-vs-h0.15 relative return is used only as a label. All features and train-derived thresholds use information available at each observation; holdout is chronological and untouched by threshold fitting."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    top = {k: v["features"][:8] for k, v in rankings.items()}
    print(json.dumps({"study": out["study"], "top": top}, indent=2), flush=True)


if __name__ == "__main__":
    main()
