from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.v99_r3 import _weighted_side_return
import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase4_bear_subregimes as p4
import run_v99_r105_all_regime_structural_audit as audit

REPORT = PROJECT / "reports" / "candidate_v99_r106_phase9_sideaware_hedge_component.json"
SIDE_WINDOW_HOURS = 3  # frozen structural R3 shock horizon; not fitted here

r36 = p1.r98.r36
r86 = p1.r98.r86
r88 = p1.r98.r88
r37 = r86.r37
cap = p1.cap


def side_recent_returns(raw: pd.DataFrame, close: pd.DataFrame):
    held = raw.shift(1).fillna(0.0)
    hourly = close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    _, long_hourly, long_count = _weighted_side_return(hourly, held, "long")
    _, short_hourly, short_count = _weighted_side_return(hourly, held, "short")
    long_recent = long_hourly.rolling(SIDE_WINDOW_HOURS, min_periods=1).sum()
    short_recent = short_hourly.rolling(SIDE_WINDOW_HOURS, min_periods=1).sum()
    return long_recent, short_recent, long_count, short_count


def sideaware_r30_targets(raw: pd.DataFrame, shadow: pd.Series, close: pd.DataFrame, p: dict):
    active = r37.r30_stress_mask(shadow, close["BTCUSDT"], p)
    net = raw.sum(axis=1)
    direction = -np.sign(net).where(net.abs() >= p["min_net"], 0.0)
    long_recent, short_recent, long_count, short_count = side_recent_returns(raw, close)

    suppress_long_hedge = active & direction.gt(0.0) & short_recent.gt(0.0) & short_count.gt(0)
    suppress_short_hedge = active & direction.lt(0.0) & long_recent.gt(0.0) & long_count.gt(0)
    suppress = suppress_long_hedge | suppress_short_hedge
    effective_direction = direction.mask(suppress, 0.0)

    out = raw.copy()
    if "BTCUSDT" not in out.columns:
        raise RuntimeError("BTCUSDT missing from V15 universe")
    hedge_add = active.astype(float) * effective_direction * float(p["hedge_size"])
    out["BTCUSDT"] = out["BTCUSDT"] + hedge_add
    out = cap(out, float(p["gross_cap"]))
    return out, active, {
        "active_fraction": float(active.mean()),
        "long_hedge_suppressed_fraction": float(suppress_long_hedge.mean()),
        "short_hedge_suppressed_fraction": float(suppress_short_hedge.mean()),
        "any_hedge_suppressed_fraction": float(suppress.mean()),
        "suppressed_within_active_fraction": float(suppress.sum() / max(1, active.sum())),
        "mean_long_recent_when_short_hedge_suppressed": float(long_recent.loc[suppress_short_hedge].mean()) if suppress_short_hedge.any() else 0.0,
        "mean_short_recent_when_long_hedge_suppressed": float(short_recent.loc[suppress_long_hedge].mean()) if suppress_long_hedge.any() else 0.0,
    }


def build_sideaware_parent_r73(data, raw, ex, guard, gross, cost):
    core = r36.run(data, raw, ex, cost, gross, guard)
    t15, a15, d15 = sideaware_r30_targets(raw, core.equity, data.close, r86.P15)
    t25, a25, d25 = sideaware_r30_targets(raw, core.equity, data.close, r86.P25)
    protect, pdiag = r86.protection_gate(t15)
    targets = t15.copy()
    targets.loc[protect, :] = t25.loc[protect, :]
    targets = cap(targets, float(r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r86.P15["gross_cap"]), guard)
    return result, targets, protect, {
        **pdiag,
        "sideaware_h15": d15,
        "sideaware_h25": d25,
        "h15_active_fraction": float(a15.mean()),
        "h25_active_fraction": float(a25.mean()),
    }


def build_sideaware_r98(data, raw, ex, guard, gross, cost):
    parent, parent_targets, protect, pdiag = build_sideaware_parent_r73(data, raw, ex, guard, gross, cost)
    gate, gdiag = r88.daily_gate(parent.equity)
    parent_gross = parent_targets.abs().sum(axis=1)
    high = gate & parent_gross.ge(p1.r98.R97_GROSS_THRESHOLD)
    targets = parent_targets.copy()
    if gate.any():
        targets.loc[gate, :] = targets.loc[gate, :] * p1.r98.R88_SCALE
    if high.any():
        targets.loc[high, :] = parent_targets.loc[high, :] * p1.r98.R96_SCALE
    targets = cap(targets, float(r86.P15["gross_cap"]))
    result = r36.run(data, targets, ex, cost, float(r86.P15["gross_cap"]), guard)
    return targets, result, {
        **pdiag,
        **gdiag,
        "qualified_high_fraction": float(high.mean()),
        "protect_overlap_high_fraction": float((high & protect.reindex(high.index).fillna(False)).mean()),
    }


def compact(a: dict) -> dict:
    m = a["global"]
    return {
        "roi_pct": 100.0 * float(m["roi"]),
        "max_dd_pct": -100.0 * float(m["max_drawdown_abs"]),
        "worst_day_pct": -100.0 * float(m["worst_day_abs"]),
        "win_rate_pct": 100.0 * float(m["trade_win_rate"]),
        "winning_trades": int(m["winning_trades"]),
        "profit_factor": float(m["profit_factor"]),
        "positive_days_pct": 100.0 * float(m["positive_day_ratio"]),
        "avg_win_pct": 100.0 * float(m["avg_winning_trade"]),
        "avg_loss_pct": 100.0 * float(m["avg_losing_trade"]),
        "payoff": float(m["payoff_ratio"]),
        "max_losing_streak": int(m["max_consecutive_losing_trades"]),
    }


def segment(equity: pd.Series, mask: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    return p4.segment_metrics(equity, mask, start, end)


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    base_cost = float(ex["base_cost_per_side"])
    severe_cost = float(ex["severe_cost_per_side"])
    super_cost = severe_cost * 1.5
    direction, vol, _ = audit.classify_regimes(data.close)
    substates = p4.bear_high_vol_substates(data.close, direction, vol)
    crash = substates["CRASH_CONTINUATION"]

    original_targets, original_base, _ = p1.build_r98_targets(data, raw, ex, guard, gross, base_cost)
    side_targets, side_base, side_diag = build_sideaware_r98(data, raw, ex, guard, gross, base_cost)

    benchmarks = p1.r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)
    common_start = max([data.close.index[0]] + [x["data"].close.index[0] for x in benchmarks.values()])
    common_end = min([data.close.index[-1]] + [x["data"].close.index[-1] for x in benchmarks.values()])
    train_end = min(p1.TRAIN_END, common_end)
    hold_idx = data.close.index[(data.close.index > p1.TRAIN_END) & (data.close.index <= common_end)]
    hold_start = hold_idx[0] if len(hold_idx) else common_end

    def analyze_pair(cost):
        ot, ores, _ = p1.build_r98_targets(data, raw, ex, guard, gross, cost)
        st, sres, sdiag = build_sideaware_r98(data, raw, ex, guard, gross, cost)
        return {
            "original": audit.analyze_result(ores, data, direction, vol, common_start, common_end),
            "sideaware": audit.analyze_result(sres, data, direction, vol, common_start, common_end),
            "original_holdout": audit.analyze_result(ores, data, direction, vol, hold_start, common_end),
            "sideaware_holdout": audit.analyze_result(sres, data, direction, vol, hold_start, common_end),
            "original_crash": segment(ores.equity, crash, common_start, common_end),
            "sideaware_crash": segment(sres.equity, crash, common_start, common_end),
            "original_crash_holdout": segment(ores.equity, crash, hold_start, common_end),
            "sideaware_crash_holdout": segment(sres.equity, crash, hold_start, common_end),
            "diagnostics": sdiag,
            "target_turnover_l1_delta": float(st.diff().abs().sum(axis=1).sum() - ot.diff().abs().sum(axis=1).sum()),
        }

    base = {
        "original": audit.analyze_result(original_base, data, direction, vol, common_start, common_end),
        "sideaware": audit.analyze_result(side_base, data, direction, vol, common_start, common_end),
        "original_holdout": audit.analyze_result(original_base, data, direction, vol, hold_start, common_end),
        "sideaware_holdout": audit.analyze_result(side_base, data, direction, vol, hold_start, common_end),
        "original_crash": segment(original_base.equity, crash, common_start, common_end),
        "sideaware_crash": segment(side_base.equity, crash, common_start, common_end),
        "original_crash_holdout": segment(original_base.equity, crash, hold_start, common_end),
        "sideaware_crash_holdout": segment(side_base.equity, crash, hold_start, common_end),
        "diagnostics": side_diag,
        "target_turnover_l1_delta": float(side_targets.diff().abs().sum(axis=1).sum() - original_targets.diff().abs().sum(axis=1).sum()),
    }
    severe = analyze_pair(severe_cost)
    super_severe = analyze_pair(super_cost)

    bounds = np.linspace(0, len(data.close.loc[(data.close.index >= common_start) & (data.close.index <= train_end)]), 5, dtype=int)
    train_idx = data.close.index[(data.close.index >= common_start) & (data.close.index <= train_end)]
    folds = []
    for i in range(4):
        lo, hi = int(bounds[i]), int(bounds[i+1]-1)
        if hi <= lo:
            continue
        start, end = train_idx[lo], train_idx[hi]
        o = audit.analyze_result(original_base, data, direction, vol, start, end)["global"]
        s = audit.analyze_result(side_base, data, direction, vol, start, end)["global"]
        folds.append({
            "fold": i+1,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "original_roi": float(o["roi"]),
            "sideaware_roi": float(s["roi"]),
            "wealth_ratio": float((1+s["roi"]) / max(1e-12, 1+o["roi"])),
            "original_dd": float(o["max_drawdown_abs"]),
            "sideaware_dd": float(s["max_drawdown_abs"]),
        })

    def compare_pack(block):
        o = block["original"]["global"]
        s = block["sideaware"]["global"]
        oh = block["original_holdout"]["global"]
        sh = block["sideaware_holdout"]["global"]
        return {
            "full_wealth_ratio": float((1+s["roi"]) / max(1e-12, 1+o["roi"])),
            "holdout_wealth_ratio": float((1+sh["roi"]) / max(1e-12, 1+oh["roi"])),
            "full_dd_win": bool(s["max_drawdown_abs"] <= o["max_drawdown_abs"]),
            "holdout_dd_win": bool(sh["max_drawdown_abs"] <= oh["max_drawdown_abs"]),
            "full_worst_win": bool(s["worst_day_abs"] <= o["worst_day_abs"]),
            "holdout_worst_win": bool(sh["worst_day_abs"] <= oh["worst_day_abs"]),
            "pf_full_delta": float(s["profit_factor"] - o["profit_factor"]),
            "pf_holdout_delta": float(sh["profit_factor"] - oh["profit_factor"]),
        }

    out = {
        "study": "V99 R106 phase 9 — side-aware hedge-component correction",
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "frozen_assets_untouched": {"v16": True, "v99_frozen": True},
        "precommitment": {
            "no_grid_search": True,
            "side_window_hours": SIDE_WINDOW_HOURS,
            "window_source": "existing R3 structural shock_hours principle; not fitted in phase 9",
            "rule": "suppress only additive BTC hedge when it opposes the currently net side and that held side has positive weighted recent return; preserve base BTC alpha target",
            "symmetric_long_short": True,
        },
        "data": {"common_start": common_start.isoformat(), "common_end": common_end.isoformat(), "train_end": train_end.isoformat(), "holdout_start": hold_start.isoformat()},
        "base": base,
        "severe": severe,
        "super_severe": super_severe,
        "folds": folds,
        "comparison": {"base": compare_pack(base), "severe": compare_pack(severe), "super_severe": compare_pack(super_severe)},
        "promotion": {"promoted": False, "reason": "evidence review required"},
        "disclosure": "Historical research and chronological holdout only. No real orders. No profit guarantees.",
        "quarantined_symbols": quarantined,
        "metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2, default=audit.safe_float) + "\n")

    print(json.dumps({
        "base": {"original": compact(base["original"]), "sideaware": compact(base["sideaware"]), "original_holdout": compact(base["original_holdout"]), "sideaware_holdout": compact(base["sideaware_holdout"]), "crash_original": base["original_crash"], "crash_sideaware": base["sideaware_crash"], "crash_holdout_original": base["original_crash_holdout"], "crash_holdout_sideaware": base["sideaware_crash_holdout"]},
        "severe_comparison": out["comparison"]["severe"],
        "super_severe_comparison": out["comparison"]["super_severe"],
        "folds": folds,
        "diagnostics": side_diag,
    }, indent=2, default=audit.safe_float), flush=True)


if __name__ == "__main__":
    main()
