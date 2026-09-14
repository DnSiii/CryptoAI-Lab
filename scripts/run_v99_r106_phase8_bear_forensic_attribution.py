from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase3_dispersion_breakout as p3
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r106_phase5_segregated_sleeve_risk as p5
import run_v99_r106_phase6_incremental_alpha_router as p6
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase8_bear_forensic_attribution.json"
TRAIN_FOLDS = 4
EPS = 1e-12


def safe(x):
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, pd.Timestamp):
        return x.isoformat()
    return x


def build_f6(data, raw, ex, guard, gross, cost, direction, vol):
    r98_targets, r98_result, _ = p1.build_r98_targets(data, raw, ex, guard, gross, cost)
    sleeves = p1.fixed_sleeves(data)
    dispersion, _ = p3.bear_dispersion_targets(data, direction)
    breakout, _ = p3.breakout_targets(data)
    sleeves = {**sleeves, "bear_dispersion": dispersion, "breakout": breakout}
    train_start = data.close.index[0]
    train_end = min(p1.TRAIN_END, data.close.index[-1])
    routing, diagnostics = p6.incremental_router(
        data, r98_targets, r98_result, sleeves, ex, guard, cost,
        direction, vol, train_start, train_end,
    )
    native_targets = p1.route_native(sleeves, direction, vol, routing)
    native_result = p1.run_targets(data, native_targets, ex, guard, cost, p1.GROSS_CAP)
    core_effective, _ = p5.effective_targets(r98_targets, r98_result, guard)
    native_effective, _ = p5.effective_targets(native_targets, native_result, guard)
    combined, _, headroom = p5.combine_with_headroom(
        core_effective, native_effective, p1.HYBRID_ALPHA_SCALE, p1.GROSS_CAP
    )
    f6_result = p5.run_no_dd_guard(data, combined, ex, cost, p1.GROSS_CAP)
    return r98_targets, r98_result, combined, f6_result, routing, diagnostics, headroom


def net_asset_pnl(result) -> pd.DataFrame:
    gross = result.asset_gross.fillna(0.0)
    fees = result.asset_fees.fillna(0.0)
    funding = result.asset_funding.fillna(0.0)
    return gross - fees - funding


def side_summary(result, mask: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    idx = result.equity.index
    use = mask.reindex(idx).fillna(False) & (idx >= start) & (idx <= end)
    pnl = net_asset_pnl(result).loc[use]
    gross_pnl = result.asset_gross.fillna(0.0).loc[use]
    pos = result.open_positions.fillna(0.0).loc[use]
    fees = result.asset_fees.fillna(0.0).loc[use]
    funding = result.asset_funding.fillna(0.0).loc[use]
    orders = result.asset_orders.fillna(0.0).loc[use]
    order_notional = result.asset_order_notional.fillna(0.0).loc[use]

    long_mask = pos > EPS
    short_mask = pos < -EPS
    flat_mask = ~(long_mask | short_mask)

    def summarize_side(sm: pd.DataFrame) -> dict:
        vals = pnl.where(sm, 0.0)
        gross_vals = gross_pnl.where(sm, 0.0)
        fee_vals = fees.where(sm, 0.0)
        funding_vals = funding.where(sm, 0.0)
        arr = vals.to_numpy(dtype=float)
        gains = float(arr[arr > 0].sum()) if arr.size else 0.0
        losses = float(-arr[arr < 0].sum()) if arr.size else 0.0
        return {
            "net_pnl": float(vals.to_numpy(dtype=float).sum()),
            "gross_pnl": float(gross_vals.to_numpy(dtype=float).sum()),
            "fees": float(fee_vals.to_numpy(dtype=float).sum()),
            "funding_cost": float(funding_vals.to_numpy(dtype=float).sum()),
            "profit_factor_contribution": float(gains / losses) if losses > EPS else (999.0 if gains > 0 else 0.0),
            "winning_asset_hours": int((vals > 0).to_numpy().sum()),
            "losing_asset_hours": int((vals < 0).to_numpy().sum()),
            "mean_abs_position": float(pos.where(sm, 0.0).abs().to_numpy(dtype=float).mean()) if len(pos) else 0.0,
        }

    prev_pos = result.open_positions.shift(1).fillna(0.0).loc[use]
    new_entry = (prev_pos.abs() <= EPS) & (pos.abs() > EPS) & (orders.abs() > EPS)
    flip = (np.sign(prev_pos) != np.sign(pos)) & (prev_pos.abs() > EPS) & (pos.abs() > EPS) & (orders.abs() > EPS)

    return {
        "hours": int(use.sum()),
        "long": summarize_side(long_mask),
        "short": summarize_side(short_mask),
        "flat_or_transition": summarize_side(flat_mask),
        "turnover": float(result.turnover.loc[use].sum()),
        "fees_total": float(result.fees.loc[use].sum()),
        "funding_total": float(result.funding.loc[use].sum()),
        "order_count": int((orders.abs() > EPS).to_numpy().sum()),
        "order_notional_abs": float(order_notional.abs().to_numpy(dtype=float).sum()),
        "new_entries": int(new_entry.to_numpy().sum()),
        "flips": int(flip.to_numpy().sum()),
        "avg_gross": float(result.gross_exposure.loc[use].mean()) if use.any() else 0.0,
        "avg_net": float(pos.sum(axis=1).mean()) if len(pos) else 0.0,
        "net_short_hour_fraction": float((pos.sum(axis=1) < -0.05).mean()) if len(pos) else 0.0,
        "net_long_hour_fraction": float((pos.sum(axis=1) > 0.05).mean()) if len(pos) else 0.0,
    }


def asset_summary(result, mask: pd.Series, start: pd.Timestamp, end: pd.Timestamp, top_n: int = 12) -> dict:
    idx = result.equity.index
    use = mask.reindex(idx).fillna(False) & (idx >= start) & (idx <= end)
    pnl = net_asset_pnl(result).loc[use]
    pos = result.open_positions.fillna(0.0).loc[use]
    fees = result.asset_fees.fillna(0.0).loc[use]
    funding = result.asset_funding.fillna(0.0).loc[use]
    orders = result.asset_orders.fillna(0.0).loc[use]
    rows = []
    for symbol in pnl.columns:
        s = pnl[symbol]
        rows.append({
            "symbol": symbol,
            "net_pnl": float(s.sum()),
            "gross_pnl": float(result.asset_gross.fillna(0.0).loc[use, symbol].sum()),
            "fees": float(fees[symbol].sum()),
            "funding_cost": float(funding[symbol].sum()),
            "mean_abs_position": float(pos[symbol].abs().mean()) if len(pos) else 0.0,
            "long_fraction": float((pos[symbol] > EPS).mean()) if len(pos) else 0.0,
            "short_fraction": float((pos[symbol] < -EPS).mean()) if len(pos) else 0.0,
            "orders": int((orders[symbol].abs() > EPS).sum()),
        })
    rows.sort(key=lambda x: x["net_pnl"])
    return {
        "worst": rows[:top_n],
        "best": list(reversed(rows[-top_n:])),
    }


def btc_conflict_summary(result, mask: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    idx = result.equity.index
    use = mask.reindex(idx).fillna(False) & (idx >= start) & (idx <= end)
    pos = result.open_positions.fillna(0.0).loc[use]
    pnl = net_asset_pnl(result).loc[use]
    if "BTCUSDT" not in pos.columns:
        return {"available": False}
    ex_btc_net = pos.drop(columns=["BTCUSDT"]).sum(axis=1)
    btc = pos["BTCUSDT"]
    conflict = (ex_btc_net < -0.05) & (btc > 0.02)
    reverse_conflict = (ex_btc_net > 0.05) & (btc < -0.02)
    other_pnl = pnl.drop(columns=["BTCUSDT"]).sum(axis=1)
    btc_pnl = pnl["BTCUSDT"]
    short_assets = pos.drop(columns=["BTCUSDT"]) < -EPS
    short_pnl = pnl.drop(columns=["BTCUSDT"]).where(short_assets, 0.0).sum(axis=1)
    profitable_short_conflict = conflict & (short_pnl > 0.0) & (btc_pnl < 0.0)

    def pack(m: pd.Series) -> dict:
        return {
            "hours": int(m.sum()),
            "fraction_of_segment": float(m.mean()) if len(m) else 0.0,
            "btc_net_pnl": float(btc_pnl.loc[m].sum()) if m.any() else 0.0,
            "other_assets_net_pnl": float(other_pnl.loc[m].sum()) if m.any() else 0.0,
            "short_assets_net_pnl": float(short_pnl.loc[m].sum()) if m.any() else 0.0,
            "mean_ex_btc_net": float(ex_btc_net.loc[m].mean()) if m.any() else 0.0,
            "mean_btc_position": float(btc.loc[m].mean()) if m.any() else 0.0,
        }

    return {
        "available": True,
        "long_btc_against_net_short": pack(conflict),
        "short_btc_against_net_long": pack(reverse_conflict),
        "profitable_shorts_but_btc_long_loses": pack(profitable_short_conflict),
    }


def fold_bounds(index: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp):
    idx = index[(index >= start) & (index <= end)]
    cuts = np.linspace(0, len(idx), TRAIN_FOLDS + 1, dtype=int)
    out = []
    for i in range(TRAIN_FOLDS):
        lo = int(cuts[i])
        hi = int(cuts[i + 1] - 1)
        if hi > lo:
            out.append((idx[lo], idx[hi]))
    return out


def mechanism_consistency(result, crash: pd.Series, train_start: pd.Timestamp, train_end: pd.Timestamp, hold_start: pd.Timestamp, common_end: pd.Timestamp) -> dict:
    segments = {
        "train": (train_start, train_end),
        "holdout": (hold_start, common_end),
    }
    for i, (lo, hi) in enumerate(fold_bounds(result.equity.index, train_start, train_end), 1):
        segments[f"train_fold_{i}"] = (lo, hi)
    out = {}
    for name, (lo, hi) in segments.items():
        out[name] = {
            "side": side_summary(result, crash, lo, hi),
            "btc_conflict": btc_conflict_summary(result, crash, lo, hi),
            "assets": asset_summary(result, crash, lo, hi, top_n=6),
        }
    return out


def main() -> None:
    cfg, data, raw, ex, guard, gross, quarantined, metadata = p1.r98.r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    direction, vol, _ = audit.classify_regimes(data.close)
    substates = p4.bear_high_vol_substates(data.close, direction, vol)
    crash = substates["CRASH_CONTINUATION"]
    squeeze = substates["BEAR_SQUEEZE"]
    mixed = substates["MIXED"]

    r98_targets, r98_result, f6_targets, f6_result, routing, diagnostics, headroom = build_f6(
        data, raw, ex, guard, gross, base_cost, direction, vol
    )

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_start = common_start
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    def segment_pack(result, mask):
        return {
            "full": side_summary(result, mask, common_start, common_end),
            "train": side_summary(result, mask, train_start, train_end),
            "holdout": side_summary(result, mask, hold_start, common_end),
        }

    out = {
        "study": "V99 R106 phase 8 — BEAR high-vol forensic attribution",
        "status": "DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "question": "What actually causes the BEAR+HIGH_VOL crash-continuation losses in R98/F6: long side, short side, BTC hedge conflict, asset concentration, or churn?",
        "precommitment": {
            "no_strategy_change": True,
            "no_grid_search": True,
            "crash_state_reuses_phase4_causal_definition": True,
            "net_asset_pnl": "asset_gross - asset_fees - asset_funding",
            "btc_conflict": "ex-BTC net short while BTC position is long during crash continuation",
        },
        "data": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "train_end": train_end.isoformat(),
            "holdout_start": hold_start.isoformat(),
            "quarantined_symbols": quarantined,
            "metadata": metadata,
        },
        "f6_routing": routing,
        "f6_routing_diagnostics": diagnostics,
        "f6_headroom": headroom,
        "substate_hours": {k: int(v.loc[(v.index >= common_start) & (v.index <= common_end)].sum()) for k, v in substates.items()},
        "r98": {
            "crash_continuation": segment_pack(r98_result, crash),
            "bear_squeeze": segment_pack(r98_result, squeeze),
            "mixed": segment_pack(r98_result, mixed),
            "crash_assets": asset_summary(r98_result, crash, common_start, common_end),
            "crash_btc_conflict": btc_conflict_summary(r98_result, crash, common_start, common_end),
            "consistency": mechanism_consistency(r98_result, crash, train_start, train_end, hold_start, common_end),
        },
        "f6": {
            "crash_continuation": segment_pack(f6_result, crash),
            "bear_squeeze": segment_pack(f6_result, squeeze),
            "mixed": segment_pack(f6_result, mixed),
            "crash_assets": asset_summary(f6_result, crash, common_start, common_end),
            "crash_btc_conflict": btc_conflict_summary(f6_result, crash, common_start, common_end),
            "consistency": mechanism_consistency(f6_result, crash, train_start, train_end, hold_start, common_end),
        },
        "disclosure": "Diagnostic historical/chronological holdout attribution only. No strategy parameters are selected and no real orders are enabled.",
    }
    REPORT.write_text(json.dumps(out, indent=2, default=safe) + "\n")

    def concise(engine: dict) -> dict:
        crash_full = engine["crash_continuation"]["full"]
        conflict = engine["crash_btc_conflict"]
        return {
            "crash_hours": crash_full["hours"],
            "long_net_pnl": crash_full["long"]["net_pnl"],
            "short_net_pnl": crash_full["short"]["net_pnl"],
            "fees_total": crash_full["fees_total"],
            "turnover": crash_full["turnover"],
            "new_entries": crash_full["new_entries"],
            "flips": crash_full["flips"],
            "btc_long_against_net_short": conflict.get("long_btc_against_net_short", {}),
            "profitable_shorts_btc_loss": conflict.get("profitable_shorts_but_btc_long_loses", {}),
            "worst_assets": engine["crash_assets"]["worst"][:8],
            "best_assets": engine["crash_assets"]["best"][:8],
        }

    print(json.dumps({
        "substate_hours": out["substate_hours"],
        "r98": concise(out["r98"]),
        "f6": concise(out["f6"]),
        "r98_train_holdout": {
            "train": out["r98"]["consistency"]["train"],
            "holdout": out["r98"]["consistency"]["holdout"],
        },
    }, indent=2, default=safe), flush=True)


if __name__ == "__main__":
    main()
