from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r59_h15_mild_crash as r59

r36 = r59.r36
r37 = r59.r37
REPORT = PROJECT / "reports" / "v99_r60_h15_maxdd_forensics.json"
PARENT = r59.PARENT

Q90_RULES = (
    {"name": "early_dominant_q90", "lo": 0.05, "hi": 0.12, "feature": "dominant", "threshold": 1.201942535993832},
    {"name": "mid_gross_q90", "lo": 0.08, "hi": 0.18, "feature": "gross", "threshold": 1.35},
    {"name": "deep_gross_q90", "lo": 0.12, "hi": 0.24, "feature": "gross", "threshold": 1.425},
)


def exposure_frame(targets: pd.DataFrame) -> pd.DataFrame:
    long_gross = targets.clip(lower=0.0).sum(axis=1)
    short_gross = (-targets.clip(upper=0.0)).sum(axis=1)
    gross = long_gross + short_gross
    dominant = pd.concat([long_gross, short_gross], axis=1).max(axis=1)
    net = targets.sum(axis=1)
    out = pd.DataFrame({
        "long_gross": long_gross,
        "short_gross": short_gross,
        "gross": gross,
        "dominant": dominant,
        "net": net,
        "net_abs": net.abs(),
    })
    return out


def first_true(series: pd.Series, start, end):
    s = series.loc[start:end]
    hits = s[s.fillna(False).astype(bool)]
    return hits.index[0] if len(hits) else None


def nonoverlap_episodes(eq: pd.Series, n: int = 8):
    peak = eq.cummax()
    dd = eq / peak - 1.0
    work = dd.copy()
    rows = []
    for _ in range(n):
        if work.empty or float(work.min()) >= 0.0:
            break
        trough = work.idxmin()
        pidx = eq.loc[:trough].idxmax()
        recovery = eq.loc[trough:]
        recovered = recovery[recovery >= eq.loc[pidx]]
        ridx = recovered.index[0] if len(recovered) else eq.index[-1]
        rows.append((pidx, trough, ridx, float(dd.loc[trough])))
        work = work.drop(work.loc[pidx:ridx].index, errors="ignore")
    return rows


def crossing_snapshot(dd: pd.Series, exp: pd.DataFrame, medium: pd.Series, deep: pd.Series, peak, trough, level: float):
    s = dd.loc[peak:trough]
    hits = s[s <= -level]
    if hits.empty:
        return None
    t = hits.index[0]
    e = exp.loc[t]
    depth = float(-dd.loc[t])
    rules = {}
    for r in Q90_RULES:
        state = depth >= r["lo"] and depth < r["hi"]
        value = float(e[r["feature"]])
        rules[r["name"]] = {
            "active": bool(state and value >= r["threshold"]),
            "value": value,
            "threshold": r["threshold"],
        }
    return {
        "timestamp": t.isoformat(),
        "dd": float(dd.loc[t]),
        "hours_to_trough": int((trough - t) / pd.Timedelta(hours=1)),
        "target_exposure": {k: float(e[k]) for k in exp.columns},
        "medium_crash_active": bool(medium.reindex([t]).fillna(False).iloc[0]),
        "deep_crash_active": bool(deep.reindex([t]).fillna(False).iloc[0]),
        "q90_rules": rules,
    }


def episode_row(result, data, targets, exp, medium, deep, peak, trough, recovery, depth, top_n=10):
    eq = result.equity.astype(float)
    dd = eq / eq.cummax() - 1.0
    pnl = (result.asset_gross - result.asset_fees - result.asset_funding).fillna(0.0)
    seg = pnl.loc[peak:trough]
    contrib = seg.sum().sort_values()
    openpos = result.open_positions.loc[peak:trough]
    btc = data.close["BTCUSDT"].loc[peak:trough]

    loss = []
    for sym, val in contrib.head(top_n).items():
        p = openpos[sym]
        loss.append({
            "symbol": sym,
            "net_pnl_contribution": float(val),
            "mean_weight": float(p.mean()),
            "mean_abs_weight": float(p.abs().mean()),
            "max_abs_weight": float(p.abs().max()),
            "long_fraction": float((p > 1e-12).mean()),
            "short_fraction": float((p < -1e-12).mean()),
        })

    gain = []
    for sym, val in contrib.tail(min(top_n, len(contrib))).sort_values(ascending=False).items():
        p = openpos[sym]
        gain.append({
            "symbol": sym,
            "net_pnl_contribution": float(val),
            "mean_weight": float(p.mean()),
            "mean_abs_weight": float(p.abs().mean()),
        })

    q90_flags = pd.Series(False, index=exp.index)
    per_rule = {}
    depth_series = (-dd).clip(lower=0.0)
    for r in Q90_RULES:
        gate = (
            (depth_series >= r["lo"]) & (depth_series < r["hi"])
            & (exp[r["feature"]] >= r["threshold"])
        )
        q90_flags = q90_flags | gate
        first = first_true(gate, peak, trough)
        per_rule[r["name"]] = {
            "first_activation": first.isoformat() if first is not None else None,
            "hours_before_trough": int((trough - first) / pd.Timedelta(hours=1)) if first is not None else None,
            "active_fraction_peak_to_trough": float(gate.loc[peak:trough].mean()),
        }

    first_q90 = first_true(q90_flags, peak, trough)
    first_medium = first_true(medium, peak, trough)
    first_deep = first_true(deep, peak, trough)

    pre_start = max(eq.index[0], peak - pd.Timedelta(hours=168))
    pre = exp.loc[pre_start:peak]
    during = exp.loc[peak:trough]

    return {
        "peak": peak.isoformat(),
        "trough": trough.isoformat(),
        "recovery_or_end": recovery.isoformat(),
        "drawdown": depth,
        "hours_peak_to_trough": int((trough - peak) / pd.Timedelta(hours=1)),
        "hours_to_recovery_or_end": int((recovery - trough) / pd.Timedelta(hours=1)),
        "equity_peak": float(eq.loc[peak]),
        "equity_trough": float(eq.loc[trough]),
        "btc_return_peak_to_trough": float(btc.iloc[-1] / btc.iloc[0] - 1.0) if len(btc) > 1 else 0.0,
        "target_exposure_pre_peak_7d": {k: float(pre[k].mean()) for k in exp.columns},
        "target_exposure_peak_to_trough_mean": {k: float(during[k].mean()) for k in exp.columns},
        "target_exposure_peak_to_trough_max": {k: float(during[k].max()) for k in exp.columns},
        "turnover_sum": float(result.turnover.loc[peak:trough].sum()),
        "fees_sum": float(result.fees.loc[peak:trough].sum()),
        "funding_sum": float(result.funding.loc[peak:trough].sum()),
        "top_loss_contributors": loss,
        "top_gain_contributors": gain,
        "crossings": {
            "5pct": crossing_snapshot(dd, exp, medium, deep, peak, trough, 0.05),
            "8pct": crossing_snapshot(dd, exp, medium, deep, peak, trough, 0.08),
            "12pct": crossing_snapshot(dd, exp, medium, deep, peak, trough, 0.12),
            "20pct": crossing_snapshot(dd, exp, medium, deep, peak, trough, 0.20),
        },
        "first_q90_any": first_q90.isoformat() if first_q90 is not None else None,
        "q90_hours_before_trough": int((trough - first_q90) / pd.Timedelta(hours=1)) if first_q90 is not None else None,
        "first_medium_crash": first_medium.isoformat() if first_medium is not None else None,
        "medium_hours_before_trough": int((trough - first_medium) / pd.Timedelta(hours=1)) if first_medium is not None else None,
        "first_deep_crash": first_deep.isoformat() if first_deep is not None else None,
        "deep_hours_before_trough": int((trough - first_deep) / pd.Timedelta(hours=1)) if first_deep is not None else None,
        "q90_rule_timing": per_rule,
    }


def worst_days(result, data, n=15):
    eq = result.equity.astype(float)
    dr = eq.resample("1D").last().pct_change(fill_method=None).dropna()
    pnl = (result.asset_gross - result.asset_fees - result.asset_funding).fillna(0.0)
    out = []
    for day, ret in dr.nsmallest(n).items():
        start = day
        end = day + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
        seg = pnl.loc[start:end]
        c = seg.sum().sort_values()
        pos = result.open_positions.loc[start:end]
        btc = data.close["BTCUSDT"].loc[start:end]
        out.append({
            "date": str(day.date()),
            "return": float(ret),
            "btc_return": float(btc.iloc[-1] / btc.iloc[0] - 1.0) if len(btc) > 1 else 0.0,
            "gross_mean": float(result.gross_exposure.loc[start:end].mean()),
            "net_exposure_mean": float(pos.sum(axis=1).mean()),
            "turnover": float(result.turnover.loc[start:end].sum()),
            "fees": float(result.fees.loc[start:end].sum()),
            "funding": float(result.funding.loc[start:end].sum()),
            "top_loss_contributors": [
                {"symbol": s, "net_pnl_contribution": float(v), "mean_weight": float(pos[s].mean())}
                for s, v in c.head(8).items()
            ],
        })
    return out


def main():
    cand, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    parent, shadow, targets, hedge_active = r59.build_parent(data, raw, ex, guard, gross, cost)
    exp = exposure_frame(targets)
    eq = parent.equity.astype(float)
    dd = eq / eq.cummax() - 1.0

    medium, medium_diag = r37.crash_signal(eq, data.close["BTCUSDT"].reindex(eq.index), r59.CRASH_PRESETS[0])
    deep, deep_diag = r37.crash_signal(eq, data.close["BTCUSDT"].reindex(eq.index), r59.CRASH_PRESETS[1])

    episodes = [
        episode_row(parent, data, targets, exp, medium, deep, *ep)
        for ep in nonoverlap_episodes(eq)
    ]
    daily = eq.resample("1D").last().pct_change(fill_method=None).dropna()
    out = {
        "study": "V99 R60 hedge-0.15 max-drawdown forensics",
        "status": "DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION",
        "objective": (
            "attribute the hedge-0.15 parent's largest drawdowns and worst days, and measure how early the fixed "
            "R57 q90 continuation rules and exact R37 medium/deep crash signals appeared before each trough"
        ),
        "parent_fixed": PARENT,
        "parent_summary": {
            "return": float(eq.iloc[-1] / eq.iloc[0] - 1.0),
            "max_drawdown": float(dd.min()),
            "worst_day": float(daily.min()),
            "best_day": float(daily.max()),
            "positive_days": float((daily > 0.0).mean()),
        },
        "parent_hedge_active_fraction": float(hedge_active.mean()),
        "q90_rules": list(Q90_RULES),
        "medium_crash_diagnostics": medium_diag,
        "deep_crash_diagnostics": deep_diag,
        "drawdown_episodes": episodes,
        "worst_days": worst_days(parent, data),
        "disclosure": (
            "Diagnostic only. PnL attribution uses realized modeled asset gross PnL less fees/funding. Signal timing "
            "uses only information available through each timestamp; no historical loss is edited by this report."
        ),
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "study": out["study"],
        "parent_summary": out["parent_summary"],
        "max_dd_episode": episodes[0] if episodes else None,
        "worst_days": out["worst_days"][:5],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
