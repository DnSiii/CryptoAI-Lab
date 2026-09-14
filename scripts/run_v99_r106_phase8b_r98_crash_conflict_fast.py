from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase8b_r98_crash_conflict.json"
EPS = 1e-12


def net_asset_pnl(result):
    return result.asset_gross.fillna(0.0) - result.asset_fees.fillna(0.0) - result.asset_funding.fillna(0.0)


def pack(result, crash, start, end):
    idx = result.equity.index
    use = crash.reindex(idx).fillna(False) & (idx >= start) & (idx <= end)
    pos = result.open_positions.fillna(0.0).loc[use]
    pnl = net_asset_pnl(result).loc[use]
    fees = result.asset_fees.fillna(0.0).loc[use]
    funding = result.asset_funding.fillna(0.0).loc[use]
    turnover = result.turnover.loc[use]

    long_pnl = pnl.where(pos > EPS, 0.0).sum().sum()
    short_pnl = pnl.where(pos < -EPS, 0.0).sum().sum()
    btc = pos["BTCUSDT"] if "BTCUSDT" in pos.columns else pd.Series(0.0, index=pos.index)
    btc_pnl = pnl["BTCUSDT"] if "BTCUSDT" in pnl.columns else pd.Series(0.0, index=pnl.index)
    ex_cols = [c for c in pos.columns if c != "BTCUSDT"]
    ex_net = pos[ex_cols].sum(axis=1) if ex_cols else pd.Series(0.0, index=pos.index)
    short_pnl_hour = pnl[ex_cols].where(pos[ex_cols] < -EPS, 0.0).sum(axis=1) if ex_cols else pd.Series(0.0, index=pos.index)
    conflict = (ex_net < -0.05) & (btc > 0.02)
    harmful = conflict & (short_pnl_hour > 0.0) & (btc_pnl < 0.0)

    def conflict_pack(mask):
        return {
            "hours": int(mask.sum()),
            "fraction": float(mask.mean()) if len(mask) else 0.0,
            "btc_pnl": float(btc_pnl.loc[mask].sum()) if mask.any() else 0.0,
            "non_btc_short_pnl": float(short_pnl_hour.loc[mask].sum()) if mask.any() else 0.0,
            "mean_btc_position": float(btc.loc[mask].mean()) if mask.any() else 0.0,
            "mean_ex_btc_net": float(ex_net.loc[mask].mean()) if mask.any() else 0.0,
        }

    by_asset = []
    for c in pnl.columns:
        by_asset.append({
            "symbol": c,
            "net_pnl": float(pnl[c].sum()),
            "mean_position": float(pos[c].mean()),
            "mean_abs_position": float(pos[c].abs().mean()),
            "long_fraction": float((pos[c] > EPS).mean()),
            "short_fraction": float((pos[c] < -EPS).mean()),
        })
    by_asset.sort(key=lambda x: x["net_pnl"])

    return {
        "hours": int(use.sum()),
        "long_net_pnl": float(long_pnl),
        "short_net_pnl": float(short_pnl),
        "fees": float(fees.sum().sum()),
        "funding_cost": float(funding.sum().sum()),
        "turnover": float(turnover.sum()),
        "avg_gross": float(pos.abs().sum(axis=1).mean()) if len(pos) else 0.0,
        "avg_net": float(pos.sum(axis=1).mean()) if len(pos) else 0.0,
        "btc_long_against_ex_btc_short": conflict_pack(conflict),
        "profitable_shorts_but_btc_long_loses": conflict_pack(harmful),
        "worst_assets": by_asset[:8],
        "best_assets": list(reversed(by_asset[-8:])),
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    crash = p4.bear_high_vol_substates(data.close, direction, vol)["CRASH_CONTINUATION"]
    _, result, diag = p1.build_r98_targets(data, raw, ex, guard, gross, cost)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= end)]
    hold_start = hold_idx[0] if len(hold_idx) else end

    bounds = np.linspace(0, len(data.close.loc[(data.close.index >= start) & (data.close.index <= train_end)]), 5, dtype=int)
    train_idx = data.close.index[(data.close.index >= start) & (data.close.index <= train_end)]
    folds = {}
    for i in range(4):
        lo, hi = int(bounds[i]), int(bounds[i+1]-1)
        if hi > lo:
            folds[f"fold_{i+1}"] = pack(result, crash, train_idx[lo], train_idx[hi])

    out = {
        "study": "V99 R106 phase 8b focused R98 crash hedge-conflict audit",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "r98_diag": diag,
        "full": pack(result, crash, start, end),
        "train": pack(result, crash, start, train_end),
        "holdout": pack(result, crash, hold_start, end),
        "train_folds": folds,
        "data": {"start": start.isoformat(), "end": end.isoformat(), "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat()},
        "disclosure": "Diagnostic-only causal state attribution. No strategy changes, no parameter fitting, no real orders.",
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
