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

REPORT = PROJECT / "reports" / "v99_r77_low_hedge_opportunity_audit.json"


def forward_relative(eq10: pd.Series, eq15: pd.Series, hours: int) -> pd.Series:
    r10 = eq10.shift(-hours) / eq10 - 1.0
    r15 = eq15.shift(-hours) / eq15 - 1.0
    return (1.0 + r10) / (1.0 + r15) - 1.0


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)

    p10 = r55.params(0.10)
    p15 = r55.params(0.15)
    res10, _, t10, active10 = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p10, shadow=shadow)
    res15, _, t15, active15 = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)

    idx = res10.equity.index.intersection(res15.equity.index)
    eq10 = res10.equity.reindex(idx).astype(float)
    eq15 = res15.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    rawx = raw.reindex(index=idx, columns=close.columns).fillna(0.0)
    t15 = t15.reindex(index=idx, columns=close.columns).fillna(0.0)
    active = active15.reindex(idx).fillna(False).astype(bool)

    btc = close["BTCUSDT"]
    coin_r24 = close.pct_change(24, fill_method=None)
    coin_r72 = close.pct_change(72, fill_method=None)
    long_gross = rawx.clip(lower=0.0).sum(axis=1)
    short_gross = (-rawx.clip(upper=0.0)).sum(axis=1)
    raw_net = rawx.sum(axis=1)
    t15_net = t15.sum(axis=1)
    rel = eq10 / eq15
    dd15 = eq15 / eq15.cummax() - 1.0

    f = pd.DataFrame(index=idx)
    f["dd_abs"] = (-dd15).clip(lower=0.0)
    f["strategy_r6"] = eq15.pct_change(6, fill_method=None)
    f["strategy_r24"] = eq15.pct_change(24, fill_method=None)
    f["strategy_r72"] = eq15.pct_change(72, fill_method=None)
    f["btc_r6"] = btc.pct_change(6, fill_method=None)
    f["btc_r24"] = btc.pct_change(24, fill_method=None)
    f["btc_r72"] = btc.pct_change(72, fill_method=None)
    f["breadth_positive_24h"] = (coin_r24 > 0).mean(axis=1)
    f["breadth_positive_72h"] = (coin_r72 > 0).mean(axis=1)
    f["market_abs_median_24h"] = coin_r24.abs().median(axis=1)
    f["cross_vol_24h"] = coin_r24.std(axis=1)
    f["raw_gross"] = rawx.abs().sum(axis=1)
    f["raw_net_abs"] = raw_net.abs()
    f["raw_dominant"] = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    f["h15_gross"] = t15.abs().sum(axis=1)
    f["h15_net_abs"] = t15_net.abs()
    f["net_btc_alignment24"] = np.sign(raw_net) * f["btc_r24"]
    f["net_btc_alignment72"] = np.sign(raw_net) * f["btc_r72"]
    f["stress_active"] = active.astype(float)
    f["stress_age_hours"] = r66.stress_age(active)
    f["h10_relative_24h"] = rel.pct_change(24, fill_method=None)
    f["h10_relative_72h"] = rel.pct_change(72, fill_method=None)
    f["h10_relative_168h"] = rel.pct_change(168, fill_method=None)

    adv24 = forward_relative(eq10, eq15, 24)
    adv72 = forward_relative(eq10, eq15, 72)
    labels = {
        "h10_win_24h": adv24 > 0,
        "h10_win_72h": adv72 > 0,
        "h10_material_win_72h_20bp": adv72 > 0.002,
    }

    sample_idx = idx[::24]
    f = f.reindex(sample_idx)
    labels = {k: v.reindex(sample_idx) for k, v in labels.items()}
    adv = {"24h": adv24.reindex(sample_idx), "72h": adv72.reindex(sample_idx)}
    valid = f.notna().sum(axis=1) >= max(1, len(f.columns) // 2)
    sample_idx = f.index[valid]
    f = f.loc[sample_idx]
    labels = {k: v.loc[sample_idx] for k, v in labels.items()}
    adv = {k: v.loc[sample_idx] for k, v in adv.items()}

    split = int(len(sample_idx) * 0.60)
    train_idx = sample_idx[:split]
    hold_idx = sample_idx[split:]
    rankings = {}
    for label_name, y in labels.items():
        rows = []
        for name in f.columns:
            tr = pd.concat([f.loc[train_idx, name], y.loc[train_idx]], axis=1).dropna()
            ho = pd.concat([f.loc[hold_idx, name], y.loc[hold_idx]], axis=1).dropna()
            if len(tr) < 40 or len(ho) < 20:
                continue
            atr = r66.auc(tr.iloc[:,0], tr.iloc[:,1])
            aho = r66.auc(ho.iloc[:,0], ho.iloc[:,1])
            direction = "high" if atr >= 0.5 else "low"
            q = 0.80 if direction == "high" else 0.20
            threshold = float(tr.iloc[:,0].quantile(q))
            gtr = r66.gated_stats(tr.iloc[:,0], tr.iloc[:,1], threshold, direction)
            gho = r66.gated_stats(ho.iloc[:,0], ho.iloc[:,1], threshold, direction)
            rows.append({
                "feature": name,
                "direction": direction,
                "train_auc": float(atr),
                "holdout_auc": float(aho),
                "threshold_train_only": threshold,
                "train_gate": gtr,
                "holdout_gate": gho,
                "stable_strength": float(min(max(atr,1-atr), max(aho,1-aho))),
            })
        rows.sort(key=lambda z:(min(z["train_gate"]["lift"],z["holdout_gate"]["lift"]), z["stable_strength"], z["holdout_gate"]["coverage"]), reverse=True)
        rankings[label_name] = rows

    out = {
        "study": "V99 R77 low-hedge opportunity audit: h0.10 vs h0.15",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "identify causal regimes where the lower h0.10 hedge outperforms h0.15 over the next 24h/72h, using a chronological 60/40 split, so a future tri-state router may use h0.10 for opportunity, h0.15 neutral and h0.25 protection",
        "variants": {"h10": p10, "h15": p15},
        "h10_summary": r55.r36.stats(eq10),
        "h15_summary": r55.r36.stats(eq15),
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
        "disclosure": "Diagnostic historical research only. Future h0.10-vs-h0.15 relative return is used only as a label. All features and thresholds are causal/train-derived; holdout is untouched by fitting. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "top": {k:v[:8] for k,v in rankings.items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
