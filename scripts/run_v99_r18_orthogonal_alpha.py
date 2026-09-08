from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from paper_once_v15 import build_v15

REPORT_PATH = PROJECT / "reports" / "candidate_v99_r18_orthogonal_alpha.json"
HORIZONS = (7, 30, 90, 180, 365)


def summary(equity: pd.Series) -> dict:
    e = equity.dropna().astype(float)
    if len(e) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "best_day": 0.0,
                "worst_day": 0.0, "positive_days": 0.0}
    norm = e / float(e.iloc[0])
    dd = norm / norm.cummax() - 1.0
    daily = norm.resample("1D").last().pct_change(fill_method=None).dropna()
    return {
        "return": float(norm.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "positive_days": float((daily > 0.0).mean()) if len(daily) else 0.0,
    }


def horizon_summary(equity: pd.Series, days: int) -> dict:
    end = equity.index[-1]
    return summary(equity.loc[equity.index >= end - pd.Timedelta(days=int(days))])


def slice_data(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    return FuturesData(
        frames={name: frame.loc[start:end].copy() for name, frame in data.frames.items()},
        funding=data.funding.loc[start:end].copy(),
        symbols=data.symbols,
    )


def run_exact(data, targets, execution, guard, gross_guard_cap, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_guard_cap,
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def isolated(data, targets, execution, guard, gross_guard_cap, cost, days):
    end = data.close.index[-1]
    start = end - pd.Timedelta(days=int(days))
    d = slice_data(data, start, end)
    t = targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    return summary(run_exact(d, t, execution, guard, gross_guard_cap, cost).equity)


def hourly_vol(close: pd.DataFrame, lookback: int = 168) -> pd.DataFrame:
    return close.pct_change(fill_method=None).rolling(
        lookback, min_periods=max(24, lookback // 2)
    ).std() * np.sqrt(365.25 * 24)


def normalize_selected(raw: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
    inv = raw.div(vol.replace(0.0, np.nan))
    gross = inv.abs().sum(axis=1).replace(0.0, np.nan)
    return inv.div(gross, axis=0).fillna(0.0)


def select_rank(mask: pd.DataFrame, score: pd.DataFrame, top_n: int,
                ascending: bool = False) -> pd.DataFrame:
    ranked = score.where(mask).rank(axis=1, ascending=ascending, method="first")
    return mask & (ranked <= top_n)


def breakout_sleeve(data: FuturesData, lookback: int, threshold: float,
                    volume_multiple: float, top_n: int) -> pd.DataFrame:
    close = data.close
    high, low = data.frames["high"], data.frames["low"]
    qv = data.frames["quote_volume"]
    ret = close.div(close.shift(lookback)).sub(1.0)
    upper = high.shift(1).rolling(lookback, min_periods=lookback).max()
    lower = low.shift(1).rolling(lookback, min_periods=lookback).min()
    recent_vol = qv.rolling(12, min_periods=6).mean()
    baseline_vol = qv.shift(12).rolling(168, min_periods=72).median()
    vol_ratio = recent_vol.div(baseline_vol.replace(0.0, np.nan))
    ema = close.ewm(span=336, adjust=False, min_periods=336).mean()
    available = close.shift(max(lookback, 336)).notna()
    long_mask = available & (close > upper) & (ret >= threshold) & (vol_ratio >= volume_multiple) & (close > ema)
    short_mask = available & (close < lower) & (ret <= -threshold) & (vol_ratio >= volume_multiple) & (close < ema)
    strength = ret.abs().mul(np.log1p(vol_ratio.clip(lower=0.0)))
    longs = select_rank(long_mask, strength, top_n, ascending=False)
    shorts = select_rank(short_mask, strength, top_n, ascending=False)
    raw = longs.astype(float).sub(shorts.astype(float))
    return normalize_selected(raw, hourly_vol(close, 168))


def crash_short_sleeve(data: FuturesData, short_trigger: float, medium_trigger: float,
                       breadth_trigger: float, top_n: int) -> pd.DataFrame:
    close = data.close
    r24 = close.pct_change(24, fill_method=None)
    r72 = close.pct_change(72, fill_method=None)
    btc24 = r24["BTCUSDT"]
    btc72 = r72["BTCUSDT"]
    breadth = (r24 > 0.0).mean(axis=1)
    stress = ((btc24 <= short_trigger) | (btc72 <= medium_trigger)) & (breadth <= breadth_trigger)
    trend = close.div(close.ewm(span=168, adjust=False, min_periods=168).mean()).sub(1.0)
    eligible = trend < 0.0
    weakness = r24.rank(axis=1, ascending=True, method="first")
    selected = eligible & (weakness <= top_n)
    raw = selected.astype(float).mul(-1.0).mul(stress.astype(float), axis=0)
    return normalize_selected(raw, hourly_vol(close, 72))


def funding_sleeve(data: FuturesData, lookback: int, top_n: int,
                   minimum_abs_funding: float) -> pd.DataFrame:
    close = data.close
    # Funding at t is not assumed known until after it is published; shift one
    # hourly row before rolling/selection.
    known = data.funding.replace(0.0, np.nan).ffill().shift(1)
    avg = known.rolling(lookback, min_periods=max(8, lookback // 3)).mean()
    trend = close.div(close.ewm(span=168, adjust=False, min_periods=168).mean()).sub(1.0)
    long_rank = avg.rank(axis=1, ascending=True, method="first")
    short_rank = avg.rank(axis=1, ascending=False, method="first")
    longs = (long_rank <= top_n) & (avg <= -minimum_abs_funding) & (trend > -0.08)
    shorts = (short_rank <= top_n) & (avg >= minimum_abs_funding) & (trend < 0.08)
    raw = longs.astype(float).sub(shorts.astype(float))
    return normalize_selected(raw, hourly_vol(close, 168))


def mix_sleeves(parts: list[tuple[pd.DataFrame, float]]) -> pd.DataFrame:
    out = sum((frame.mul(weight) for frame, weight in parts), start=parts[0][0] * 0.0)
    gross = out.abs().sum(axis=1).replace(0.0, np.nan)
    return out.div(gross.clip(lower=1.0), axis=0).fillna(0.0)


def main() -> None:
    candidate, data, v15_targets, v15_result, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text())
    finalist = json.loads((PROJECT / "config" / v14["frozen_core_config"]).read_text())
    base = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
    execution = base["execution"]
    guard = v14["circuit_breaker"]

    sleeves = {
        "breakout_fast": breakout_sleeve(data, 24, 0.015, 1.5, 2),
        "breakout_selective": breakout_sleeve(data, 48, 0.02, 2.0, 2),
        "crash_moderate": crash_short_sleeve(data, -0.025, -0.05, 0.38, 3),
        "crash_severe": crash_short_sleeve(data, -0.04, -0.07, 0.30, 2),
        "funding_fast": funding_sleeve(data, 24, 2, 0.00002),
        "funding_slow": funding_sleeve(data, 72, 2, 0.000015),
    }
    mixtures = {
        "breakout_fast": sleeves["breakout_fast"],
        "breakout_selective": sleeves["breakout_selective"],
        "crash_moderate": sleeves["crash_moderate"],
        "crash_severe": sleeves["crash_severe"],
        "funding_fast": sleeves["funding_fast"],
        "funding_slow": sleeves["funding_slow"],
        "breakout_crash": mix_sleeves([(sleeves["breakout_fast"], 0.70), (sleeves["crash_moderate"], 0.30)]),
        "breakout_funding": mix_sleeves([(sleeves["breakout_selective"], 0.70), (sleeves["funding_slow"], 0.30)]),
        "three_sleeve": mix_sleeves([(sleeves["breakout_fast"], 0.60), (sleeves["crash_moderate"], 0.25), (sleeves["funding_slow"], 0.15)]),
    }

    v15_full = summary(v15_result.equity)
    v15_trailing = {str(d): horizon_summary(v15_result.equity, d) for d in HORIZONS}
    v15_isolated = {
        str(d): isolated(data, v15_targets, execution, guard,
                         v14["allocation"]["gross_drift_guard_cap"],
                         execution["base_cost_per_side"], d)
        for d in HORIZONS
    }
    v15_severe = summary(run_exact(
        data, v15_targets, execution, guard,
        v14["allocation"]["gross_drift_guard_cap"],
        execution["severe_cost_per_side"]
    ).equity)

    rows = []
    target_cache = {}
    for name, sleeve in mixtures.items():
        for overlay in (0.15, 0.30):
            for portfolio_cap in (1.80, 1.95):
                budget = OpportunityBudget(overlay, portfolio_cap)
                try:
                    combined, allocated = additive_opportunity_targets(v15_targets, sleeve, budget)
                except ValueError:
                    continue
                key = f"{name}_o{overlay:.2f}_p{portfolio_cap:.2f}"
                target_cache[key] = combined
                result = run_exact(
                    data, combined, execution, guard,
                    portfolio_cap + 0.15, execution["base_cost_per_side"]
                )
                s = summary(result.equity)
                trailing = {str(d): horizon_summary(result.equity, d) for d in HORIZONS}
                wealth_ratio = (1.0 + s["return"]) / max(1e-12, 1.0 + v15_full["return"])
                dd_ratio = abs(s["max_drawdown"]) / max(abs(v15_full["max_drawdown"]), 1e-12)
                wins = sum(trailing[str(d)]["return"] >= v15_trailing[str(d)]["return"] for d in HORIZONS)
                worst_ratio = abs(s["worst_day"]) / max(abs(v15_full["worst_day"]), 1e-12)
                score = (
                    4.0 * np.log(max(wealth_ratio, 1e-12))
                    + 0.18 * wins
                    - 2.0 * max(0.0, dd_ratio - 1.0)
                    - 1.5 * max(0.0, worst_ratio - 1.0)
                )
                rows.append({
                    "key": key,
                    "mixture": name,
                    "overlay_gross": overlay,
                    "portfolio_cap": portfolio_cap,
                    "active_fraction": float((allocated.abs().sum(axis=1) > 1e-12).mean()),
                    "average_allocated_overlay_gross": float(allocated.abs().sum(axis=1).mean()),
                    "summary": s,
                    "trailing": trailing,
                    "wealth_ratio_to_v15": float(wealth_ratio),
                    "drawdown_ratio_to_v15": float(dd_ratio),
                    "worst_day_ratio_to_v15": float(worst_ratio),
                    "trailing_horizon_wins_vs_v15": int(wins),
                    "score": float(score),
                })

    ranking = sorted(rows, key=lambda r: r["score"], reverse=True)
    finalists = []
    for row in ranking[:8]:
        targets = target_cache[row["key"]]
        iso = {
            str(d): isolated(data, targets, execution, guard,
                             row["portfolio_cap"] + 0.15,
                             execution["base_cost_per_side"], d)
            for d in HORIZONS
        }
        severe = summary(run_exact(
            data, targets, execution, guard,
            row["portfolio_cap"] + 0.15,
            execution["severe_cost_per_side"]
        ).equity)
        wins = {str(d): bool(iso[str(d)]["return"] >= v15_isolated[str(d)]["return"]) for d in HORIZONS}
        dd_ok = {str(d): bool(abs(iso[str(d)]["max_drawdown"]) <= 1.05 * abs(v15_isolated[str(d)]["max_drawdown"]) + 1e-12) for d in HORIZONS}
        severe_wealth_ratio = (1.0 + severe["return"]) / max(1e-12, 1.0 + v15_severe["return"])
        gate = bool(
            all(wins.values())
            and all(dd_ok.values())
            and row["wealth_ratio_to_v15"] >= 1.05
            and row["drawdown_ratio_to_v15"] <= 1.05
            and row["worst_day_ratio_to_v15"] <= 1.05
            and severe_wealth_ratio >= 1.0
        )
        finalists.append({
            **row,
            "isolated": iso,
            "isolated_wins_vs_v15": wins,
            "isolated_drawdown_ok": dd_ok,
            "severe_cost": severe,
            "severe_wealth_ratio_to_v15": float(severe_wealth_ratio),
            "superior_gate_passed": gate,
        })

    finalists.sort(key=lambda r: (
        r["superior_gate_passed"],
        sum(r["isolated_wins_vs_v15"].values()),
        r["wealth_ratio_to_v15"],
        -r["drawdown_ratio_to_v15"],
    ), reverse=True)

    selected = finalists[0] if finalists else None
    report = {
        "study": "V99 R18 orthogonal alpha sleeves on V15 core",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "create alpha that V15 does not already own, then beat V15 across isolated horizons without materially worsening drawdown or worst-day damage",
        "selection_disclosure": "Historical research screen, not a pristine holdout. Any apparent winner must pass a separate anti-overfit gate and then start a new independent paper boundary.",
        "data_latest": data.close.index[-1].isoformat(),
        "v15": {"summary": v15_full, "trailing": v15_trailing, "isolated": v15_isolated, "severe_cost": v15_severe},
        "sleeve_activity": {name: float((frame.abs().sum(axis=1) > 1e-12).mean()) for name, frame in sleeves.items()},
        "grid_size": len(rows),
        "selected": selected,
        "finalists": finalists,
        "screening_ranking": ranking,
        "promotion_rule": {
            "beat_v15_isolated_7_30_90_180_365": True,
            "full_wealth_ratio_minimum": 1.05,
            "max_drawdown_ratio_maximum": 1.05,
            "worst_day_ratio_maximum": 1.05,
            "severe_cost_must_beat_v15": True,
            "next_if_passed": "run R19 anti-overfit/random-window/calendar-year gate; only then consider a new frozen V99 paper revision",
        },
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "study": report["study"],
        "grid_size": report["grid_size"],
        "v15": v15_full,
        "selected": selected,
    }, indent=2))


if __name__ == "__main__":
    main()
