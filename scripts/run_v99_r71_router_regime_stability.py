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

REPORT = PROJECT / "reports" / "v99_r71_router_regime_stability.json"
VOL24_Q80 = 0.051253990575389194
BTC24_Q20 = -0.019039657268342308
H15_GROSS_Q20 = 0.4478403629219058
BTC72_Q20 = -0.03338695841687384


def block_stats(gate: pd.Series, label: pd.Series, advantage: pd.Series, idx: pd.Index) -> dict:
    x = pd.concat([
        gate.reindex(idx).rename("gate"),
        label.reindex(idx).rename("label"),
        advantage.reindex(idx).rename("adv"),
    ], axis=1).dropna()
    if x.empty:
        return {"rows": 0, "selected": 0, "coverage": 0.0, "base_rate": 0.0, "selected_rate": 0.0, "lift": 0.0, "selected_mean_advantage": 0.0}
    g = x["gate"].astype(bool)
    y = x["label"].astype(bool)
    base = float(y.mean())
    rate = float(y.loc[g].mean()) if g.any() else 0.0
    mean_adv = float(x.loc[g, "adv"].mean()) if g.any() else 0.0
    return {
        "rows": int(len(x)), "selected": int(g.sum()), "coverage": float(g.mean()),
        "base_rate": base, "selected_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
        "selected_mean_advantage": mean_adv,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)
    p15, p25 = r55.params(0.15), r55.params(0.25)
    res15, _, t15, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)
    res25, _, _, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p25, shadow=shadow)

    idx = res15.equity.index.intersection(res25.equity.index)
    eq15 = res15.equity.reindex(idx).astype(float)
    eq25 = res25.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    t15 = t15.reindex(index=idx, columns=close.columns).fillna(0.0)

    r24 = close.pct_change(24, fill_method=None)
    market_abs = r24.abs().median(axis=1)
    btc24 = close["BTCUSDT"].pct_change(24, fill_method=None)
    btc72 = close["BTCUSDT"].pct_change(72, fill_method=None)
    h15_gross = t15.abs().sum(axis=1)

    gates = {
        "market_vol24_high": market_abs >= VOL24_Q80,
        "btc24_down": btc24 <= BTC24_Q20,
        "btc72_down": btc72 <= BTC72_Q20,
        "h15_gross_low": h15_gross <= H15_GROSS_Q20,
    }
    votes = sum(g.astype(int) for g in gates.values())
    gates["two_of_four"] = votes >= 2

    f25 = eq25.shift(-72) / eq25 - 1.0
    f15 = eq15.shift(-72) / eq15 - 1.0
    advantage = (1.0 + f25) / (1.0 + f15) - 1.0
    label = advantage > 0.002

    sample_idx = idx[::24]
    valid = advantage.reindex(sample_idx).notna()
    sample_idx = sample_idx[valid]

    fold_edges = np.linspace(0, len(sample_idx), 6, dtype=int)
    folds = []
    for i in range(5):
        fi = sample_idx[fold_edges[i]:fold_edges[i+1]]
        folds.append({"name": f"fold_{i+1}", "start": fi[0].isoformat() if len(fi) else None, "end": fi[-1].isoformat() if len(fi) else None, "index": fi})

    result = {}
    for name, gate in gates.items():
        fold_rows = []
        for f in folds:
            s = block_stats(gate, label, advantage, f["index"])
            fold_rows.append({"name": f["name"], "start": f["start"], "end": f["end"], **s})
        years = []
        for year in sorted(set(sample_idx.year)):
            yi = sample_idx[sample_idx.year == year]
            if len(yi) < 30:
                continue
            years.append({"year": int(year), **block_stats(gate, label, advantage, yi)})
        full = block_stats(gate, label, advantage, sample_idx)
        positive_fold_lifts = sum(1 for x in fold_rows if x["lift"] > 1.0)
        positive_year_lifts = sum(1 for x in years if x["lift"] > 1.0)
        result[name] = {
            "full": full,
            "folds": fold_rows,
            "years": years,
            "positive_lift_folds": int(positive_fold_lifts),
            "fold_count": int(len(fold_rows)),
            "positive_lift_years": int(positive_year_lifts),
            "year_count": int(len(years)),
            "stable_4_of_5_folds": bool(positive_fold_lifts >= 4),
            "all_fold_mean_advantage_positive": bool(all(x["selected_mean_advantage"] > 0.0 for x in fold_rows if x["selected"] > 0)),
        }

    out = {
        "study": "V99 R71 R66-router regime temporal stability audit",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "stress-test the exact frozen R66 h0.25-vs-h0.15 regime thresholds across five contiguous chronological folds and calendar years without any refitting",
        "thresholds": {
            "market_abs_median_24h_q80": VOL24_Q80,
            "btc24_q20": BTC24_Q20,
            "h15_gross_q20": H15_GROSS_Q20,
            "btc72_q20": BTC72_Q20,
        },
        "label": "h0.25 forward-72h wealth advantage over h0.15 > 0.20 percentage points",
        "daily_sample_rows": int(len(sample_idx)),
        "results": result,
        "disclosure": "Historical diagnostic only. All thresholds are frozen from R66 first-60% training. No fold/year is used to fit or alter a threshold. Future returns appear only in labels, never features. Frozen V99 and paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "summary": {k: {"full": v["full"], "positive_lift_folds": v["positive_lift_folds"], "positive_lift_years": v["positive_lift_years"]} for k,v in result.items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
