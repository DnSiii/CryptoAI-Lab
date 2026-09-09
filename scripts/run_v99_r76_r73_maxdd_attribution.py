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
import run_v99_r60_h15_maxdd_forensics as r60
import run_v99_r67_dynamic_hedge_router as r67
import run_v99_r73_gross_low_72h_persistence as r73
import run_v99_r75_hedged_recovery_alpha as r75

REPORT = PROJECT / "reports" / "v99_r76_r73_maxdd_attribution.json"
r36 = r67.r36
r37 = r67.r37
cap = r67.cap
P15 = r67.P15


def exposure_frame(targets: pd.DataFrame) -> pd.DataFrame:
    lg = targets.clip(lower=0.0).sum(axis=1)
    sg = (-targets.clip(upper=0.0)).sum(axis=1)
    return pd.DataFrame({
        "long_gross": lg,
        "short_gross": sg,
        "gross": lg + sg,
        "dominant": pd.concat([lg, sg], axis=1).max(axis=1),
        "net": targets.sum(axis=1),
        "net_abs": targets.sum(axis=1).abs(),
    })


def first_cross(dd: pd.Series, peak, trough, level: float):
    s = dd.loc[peak:trough]
    hits = s[s <= -level]
    return hits.index[0] if len(hits) else None


def gate_series(data, raw, ex, guard, gross, cost):
    core = r36.run(data, raw, ex, cost, gross, guard)
    t15_uncapped, _ = r37.r30_targets(raw, core.equity, data.close, P15)
    t15 = cap(t15_uncapped, float(P15["gross_cap"]))
    persistent, pdiag = r73.persistent_gate_series(data, t15, {"name": "h15_gross_low", "rule": "gross"})
    raw_gross_low = t15.abs().sum(axis=1) <= r67.H15_GROSS_Q20
    return persistent, raw_gross_low, pdiag


def episode(result, data, targets, persistent, raw_gate, peak, trough, recovery, depth):
    eq = result.equity.astype(float)
    dd = eq / eq.cummax() - 1.0
    pnl = (result.asset_gross - result.asset_fees - result.asset_funding).fillna(0.0)
    seg = pnl.loc[peak:trough]
    contrib = seg.sum().sort_values()
    pos = result.open_positions.loc[peak:trough]
    exp = exposure_frame(targets).loc[peak:trough]
    btc = data.close["BTCUSDT"].loc[peak:trough]
    r24 = data.close.pct_change(24, fill_method=None).loc[peak:trough]
    sign = np.sign(targets.loc[peak:trough])
    directional24 = sign * r24.reindex_like(sign)

    losses = []
    for sym, val in contrib.head(12).items():
        p = pos[sym]
        d = directional24[sym]
        losses.append({
            "symbol": sym,
            "net_pnl_contribution": float(val),
            "mean_weight": float(p.mean()),
            "mean_abs_weight": float(p.abs().mean()),
            "max_abs_weight": float(p.abs().max()),
            "mean_directional_24h": float(d.mean()),
            "adverse_24h_fraction": float((d < 0).mean()),
        })

    crossings = {}
    full_exp = exposure_frame(targets)
    btc_series = data.close["BTCUSDT"]
    for level in (0.05, 0.08, 0.12, 0.20):
        t = first_cross(dd, peak, trough, level)
        if t is None:
            crossings[f"{int(level*100)}pct"] = None
            continue
        crossings[f"{int(level*100)}pct"] = {
            "timestamp": t.isoformat(),
            "hours_to_trough": int((trough - t) / pd.Timedelta(hours=1)),
            "gross": float(full_exp.loc[t, "gross"]),
            "dominant": float(full_exp.loc[t, "dominant"]),
            "net": float(full_exp.loc[t, "net"]),
            "btc_r24": float(btc_series.pct_change(24, fill_method=None).loc[t]),
            "btc_r72": float(btc_series.pct_change(72, fill_method=None).loc[t]),
            "raw_gross_low_gate": bool(raw_gate.reindex([t]).fillna(False).iloc[0]),
            "persistent_h25_gate": bool(persistent.reindex([t]).fillna(False).iloc[0]),
        }

    return {
        "peak": peak.isoformat(),
        "trough": trough.isoformat(),
        "recovery_or_end": recovery.isoformat(),
        "drawdown": float(depth),
        "hours_peak_to_trough": int((trough - peak) / pd.Timedelta(hours=1)),
        "btc_return_peak_to_trough": float(btc.iloc[-1] / btc.iloc[0] - 1.0) if len(btc) > 1 else 0.0,
        "gross_mean": float(exp["gross"].mean()),
        "dominant_mean": float(exp["dominant"].mean()),
        "net_mean": float(exp["net"].mean()),
        "persistent_h25_fraction": float(persistent.loc[peak:trough].mean()),
        "raw_gross_low_fraction": float(raw_gate.loc[peak:trough].mean()),
        "turnover_sum": float(result.turnover.loc[peak:trough].sum()),
        "fees_sum": float(result.fees.loc[peak:trough].sum()),
        "funding_sum": float(result.funding.loc[peak:trough].sum()),
        "top_loss_contributors": losses,
        "crossings": crossings,
    }


def worst_days(result, data, targets, persistent, raw_gate, n=15):
    eq = result.equity.astype(float)
    dr = eq.resample("1D").last().pct_change(fill_method=None).dropna()
    pnl = (result.asset_gross - result.asset_fees - result.asset_funding).fillna(0.0)
    exp = exposure_frame(targets)
    rows = []
    for day, ret in dr.nsmallest(n).items():
        end = day + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
        c = pnl.loc[day:end].sum().sort_values()
        rows.append({
            "date": str(day.date()),
            "return": float(ret),
            "btc_return": float(data.close["BTCUSDT"].loc[day:end].iloc[-1] / data.close["BTCUSDT"].loc[day:end].iloc[0] - 1.0),
            "gross_mean": float(exp["gross"].loc[day:end].mean()),
            "dominant_mean": float(exp["dominant"].loc[day:end].mean()),
            "net_mean": float(exp["net"].loc[day:end].mean()),
            "persistent_h25_fraction": float(persistent.loc[day:end].mean()),
            "raw_gross_low_fraction": float(raw_gate.loc[day:end].mean()),
            "top_losses": [{"symbol": s, "net_pnl_contribution": float(v)} for s, v in c.head(8).items()],
        })
    return rows


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, targets, diag = r75.build_variant(data, raw, ex, guard, gross, cost, False)
    persistent, raw_gate, pdiag = gate_series(data, raw, ex, guard, gross, cost)
    eq = parent.equity.astype(float)
    dd = eq / eq.cummax() - 1.0
    daily = eq.resample("1D").last().pct_change(fill_method=None).dropna()

    episodes = [episode(parent, data, targets, persistent, raw_gate, *ep) for ep in r60.nonoverlap_episodes(eq, 8)]
    out = {
        "study": "V99 R76 R73 max-drawdown attribution",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": "attribute the R73 parent's largest drawdowns and worst days to specific positions/exposure states, and measure whether the h15-gross-low stronger-hedge router was active early enough before each trough",
        "parent_summary": {
            "return": float(eq.iloc[-1] / eq.iloc[0] - 1.0),
            "max_drawdown": float(dd.min()),
            "worst_day": float(daily.min()),
            "best_day": float(daily.max()),
            "positive_days": float((daily > 0).mean()),
        },
        "parent_diagnostics": diag,
        "persistent_gate_diagnostics": pdiag,
        "drawdown_episodes": episodes,
        "worst_days": worst_days(parent, data, targets, persistent, raw_gate),
        "disclosure": "Diagnostic only. Asset contribution uses modeled asset gross PnL less allocated fees/funding from the exact R73 replay. No future data is used in exposure/gate snapshots. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "parent_summary": out["parent_summary"], "maxdd": episodes[0] if episodes else None, "worst_days": out["worst_days"][:5]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
