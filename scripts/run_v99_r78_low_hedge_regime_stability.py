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

REPORT = PROJECT / "reports" / "v99_r78_low_hedge_regime_stability.json"

THRESHOLDS = {
    "btc24_down": {"feature": "btc_r24", "direction": "low", "threshold": -0.019039657268342308},
    "btc72_down": {"feature": "btc_r72", "direction": "low", "threshold": -0.03338695841687384},
    "stress_age_high": {"feature": "stress_age_hours", "direction": "high", "threshold": 284.0},
    "cross_vol24_high": {"feature": "cross_vol_24h", "direction": "high", "threshold": 0.04973417292341461},
    "market_vol24_high": {"feature": "market_abs_median_24h", "direction": "high", "threshold": 0.051253990575389194},
}


def forward_relative(eq10: pd.Series, eq15: pd.Series, hours: int) -> pd.Series:
    r10 = eq10.shift(-hours) / eq10 - 1.0
    r15 = eq15.shift(-hours) / eq15 - 1.0
    return (1.0 + r10) / (1.0 + r15) - 1.0


def block_stats(frame: pd.DataFrame, spec: dict) -> dict:
    x = frame[[spec["feature"], "event", "adv72"]].dropna()
    if x.empty:
        return {"rows": 0, "selected": 0, "coverage": 0.0, "base_rate": 0.0, "selected_rate": 0.0, "lift": 0.0, "selected_mean_advantage": 0.0}
    if spec["direction"] == "high":
        mask = x[spec["feature"]] >= spec["threshold"]
    else:
        mask = x[spec["feature"]] <= spec["threshold"]
    base = float(x["event"].mean())
    rate = float(x.loc[mask, "event"].mean()) if mask.any() else 0.0
    return {
        "rows": int(len(x)),
        "selected": int(mask.sum()),
        "coverage": float(mask.mean()),
        "base_rate": base,
        "selected_rate": rate,
        "lift": float(rate / base) if base > 0 else 0.0,
        "selected_mean_advantage": float(x.loc[mask, "adv72"].mean()) if mask.any() else 0.0,
    }


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r55.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    shadow = r55.r36.run(data, raw, ex, cost, gross, guard)
    p10 = r55.params(0.10)
    p15 = r55.params(0.15)
    res10, _, _, _ = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p10, shadow=shadow)
    res15, _, t15, active15 = r55.build_with_shadow(data, raw, ex, guard, gross, cost, p15, shadow=shadow)

    idx = res10.equity.index.intersection(res15.equity.index)
    eq10 = res10.equity.reindex(idx).astype(float)
    eq15 = res15.equity.reindex(idx).astype(float)
    close = data.close.reindex(idx)
    t15 = t15.reindex(index=idx, columns=close.columns).fillna(0.0)
    active = active15.reindex(idx).fillna(False).astype(bool)

    btc = close["BTCUSDT"]
    coin_r24 = close.pct_change(24, fill_method=None)
    f = pd.DataFrame(index=idx)
    f["btc_r24"] = btc.pct_change(24, fill_method=None)
    f["btc_r72"] = btc.pct_change(72, fill_method=None)
    f["stress_age_hours"] = r66.stress_age(active)
    f["cross_vol_24h"] = coin_r24.std(axis=1)
    f["market_abs_median_24h"] = coin_r24.abs().median(axis=1)

    adv72 = forward_relative(eq10, eq15, 72)
    event = adv72 > 0.002
    sample_idx = idx[::24]
    frame = f.reindex(sample_idx).copy()
    frame["adv72"] = adv72.reindex(sample_idx)
    frame["event"] = event.reindex(sample_idx).astype(float)
    frame = frame.dropna(subset=["adv72"])
    frame["event"] = frame["event"].astype(bool)

    times = frame.index
    folds = np.array_split(times, 5)
    results = {}
    for name, spec in THRESHOLDS.items():
        fold_rows = []
        for i, ids in enumerate(folds, 1):
            sub = frame.loc[ids]
            row = block_stats(sub, spec)
            row.update({"fold": i, "start": ids[0].isoformat() if len(ids) else None, "end": ids[-1].isoformat() if len(ids) else None})
            fold_rows.append(row)
        years = []
        for year, sub in frame.groupby(frame.index.year):
            row = block_stats(sub, spec)
            row["year"] = int(year)
            years.append(row)
        full = block_stats(frame, spec)
        results[name] = {
            "spec": spec,
            "full": full,
            "folds": fold_rows,
            "years": years,
            "positive_lift_folds": int(sum(r["lift"] > 1.0 for r in fold_rows)),
            "positive_advantage_folds": int(sum(r["selected_mean_advantage"] > 0.0 for r in fold_rows)),
            "positive_lift_years": int(sum(r["lift"] > 1.0 for r in years)),
            "year_count": int(len(years)),
        }

    ranked = sorted(results.items(), key=lambda kv: (
        kv[1]["positive_lift_folds"],
        kv[1]["positive_advantage_folds"],
        min([r["lift"] for r in kv[1]["folds"]]) if kv[1]["folds"] else 0.0,
        kv[1]["full"]["lift"],
    ), reverse=True)

    out = {
        "study": "V99 R78 temporal stability of R77 h0.10 opportunity regimes",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "stress-test the fixed R77 train-only simple causal gates that predicted material h0.10-vs-h0.15 72h advantage, across five contiguous chronological folds and calendar years without refitting",
        "label": "h0.10 forward-72h wealth advantage over h0.15 > 0.20 percentage points",
        "threshold_source": "R77 first-60% chronological training split ending 2024-01-05",
        "daily_rows": int(len(frame)),
        "results": results,
        "ranking": [name for name, _ in ranked],
        "disclosure": "Diagnostic historical research only. Thresholds are frozen from R77 training. Future relative returns are labels only. No threshold is fitted or selected on these folds. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "ranking": out["ranking"], "results": results}, indent=2), flush=True)


if __name__ == "__main__":
    main()
