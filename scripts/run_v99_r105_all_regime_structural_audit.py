from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r98_friction_aware_hybrid as r98

REPORT = PROJECT / "reports" / "v99_r105_all_regime_structural_audit.json"
INITIAL_CAPITAL_BRL = 10_000.0
TRAIN_END = r98.TRAIN_END

HIGHER_IS_BETTER = (
    "roi",
    "profit_brl",
    "cagr",
    "trade_win_rate",
    "winning_trades",
    "positive_day_ratio",
    "positive_days",
    "profit_factor",
    "avg_winning_trade",
    "payoff_ratio",
    "rolling_30d_positive_rate",
    "rolling_90d_positive_rate",
    "rolling_90d_p10_return",
)
LOWER_IS_BETTER = (
    "max_drawdown_abs",
    "worst_day_abs",
    "avg_losing_trade_abs",
    "max_consecutive_losing_trades",
    "max_consecutive_negative_days",
    "rolling_90d_dispersion",
)


def safe_float(value: float | int | np.floating | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if np.isfinite(value) else None


def max_streak(flags: list[bool] | np.ndarray | pd.Series) -> int:
    best = current = 0
    for flag in flags:
        if bool(flag):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return int(best)


def rolling_compounded(daily_returns: pd.Series, days: int) -> pd.Series:
    if len(daily_returns) < days:
        return pd.Series(dtype=float)
    logret = np.log1p(daily_returns.clip(lower=-0.999999))
    return np.expm1(logret.rolling(days, min_periods=days).sum()).dropna()


def classify_regimes(close: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """Predeclared causal regime taxonomy; no R105 fit or holdout refit."""
    btc = close["BTCUSDT"].astype(float)
    momentum = btc.pct_change(24 * 45, fill_method=None)
    shock = btc.pct_change(24 * 7, fill_method=None)
    fast = btc.ewm(span=24 * 14, adjust=False, min_periods=24 * 14).mean()
    slow = btc.ewm(span=24 * 90, adjust=False, min_periods=24 * 90).mean()
    asset_return = close.pct_change(24 * 30, fill_method=None)
    breadth = (asset_return > 0.0).where(close.notna()).mean(axis=1)

    bull = (momentum >= 0.08) & (fast > slow) & (breadth >= 0.55)
    bear = (
        (momentum <= -0.08)
        | ((fast < slow) & (breadth <= 0.45))
        | (shock <= -0.10)
    )
    direction = pd.Series("SIDEWAYS", index=close.index, dtype="object")
    direction.loc[bull] = "BULL"
    direction.loc[bear] = "BEAR"  # crash/bear overrides bull if both fire
    valid_direction = momentum.notna() & fast.notna() & slow.notna() & breadth.notna()
    direction = direction.where(valid_direction, "UNKNOWN")

    hourly = btc.pct_change(fill_method=None)
    vol7 = hourly.rolling(24 * 7, min_periods=24 * 5).std()
    vol90 = hourly.rolling(24 * 90, min_periods=24 * 30).std()
    vol_state = pd.Series("LOW_VOLATILITY", index=close.index, dtype="object")
    vol_state.loc[vol7 >= vol90] = "HIGH_VOLATILITY"
    valid_vol = vol7.notna() & vol90.notna()
    vol_state = vol_state.where(valid_vol, "UNKNOWN")

    diagnostics = pd.DataFrame(
        {
            "btc_45d_return": momentum,
            "btc_7d_shock_return": shock,
            "breadth_30d": breadth,
            "vol_7d": vol7,
            "vol_90d": vol90,
            "direction_regime": direction,
            "volatility_regime": vol_state,
        },
        index=close.index,
    )
    return direction, vol_state, diagnostics


def split_gross_on_transition(
    total_gross: float,
    before: float,
    after: float,
    open_price: float,
    previous_close: float,
    close_price: float,
) -> tuple[float, float]:
    if not all(np.isfinite(x) and x > 0 for x in (open_price, previous_close, close_price)):
        denom = abs(before) + abs(after)
        old_fraction = abs(before) / denom if denom > 1e-12 else 0.5
        return total_gross * old_fraction, total_gross * (1.0 - old_fraction)
    overnight_raw = before * (open_price / previous_close - 1.0)
    intraday_raw = after * (close_price / open_price - 1.0)
    raw_sum = overnight_raw + intraday_raw
    if abs(raw_sum) > 1e-12:
        old = total_gross * overnight_raw / raw_sum
        return float(old), float(total_gross - old)
    denom = abs(before) + abs(after)
    old_fraction = abs(before) / denom if denom > 1e-12 else 0.5
    return total_gross * old_fraction, total_gross * (1.0 - old_fraction)


def trade_episodes(
    result,
    data,
    start: pd.Timestamp,
    end: pd.Timestamp,
    direction_regime: pd.Series,
    vol_regime: pd.Series,
) -> tuple[list[dict], int]:
    required = (
        result.open_positions,
        result.asset_gross,
        result.asset_fees,
        result.asset_funding,
        result.asset_orders,
    )
    if any(x is None for x in required):
        return [], 0

    index = result.equity.index
    selected = index[(index >= start) & (index <= end)]
    if not len(selected):
        return [], 0

    active: dict[str, dict | None] = {s: None for s in result.open_positions.columns}
    closed: list[dict] = []
    open_excluded = 0

    def decision_label(ts: pd.Timestamp, series: pd.Series) -> str:
        pos = index.get_loc(ts)
        if isinstance(pos, slice) or isinstance(pos, np.ndarray):
            return "UNKNOWN"
        prior = index[max(0, int(pos) - 1)]
        value = series.reindex(index).get(prior, "UNKNOWN")
        return str(value) if pd.notna(value) else "UNKNOWN"

    def begin(sym: str, ts: pd.Timestamp, sign: int, inherited: bool) -> dict:
        pos = index.get_loc(ts)
        prior = index[max(0, int(pos) - 1)] if not isinstance(pos, slice) else ts
        entry_equity = float(result.equity.loc[prior])
        return {
            "symbol": sym,
            "sign": int(sign),
            "entry": ts,
            "entry_equity": max(entry_equity, 1e-12),
            "pnl": 0.0,
            "inherited": bool(inherited),
            "direction_regime": decision_label(ts, direction_regime),
            "volatility_regime": decision_label(ts, vol_regime),
        }

    def close_trade(sym: str, ts: pd.Timestamp) -> None:
        nonlocal active, closed
        item = active[sym]
        if item is None:
            return
        item["exit"] = ts
        item["pnl_return"] = float(item["pnl"] / item["entry_equity"])
        if not item["inherited"]:
            closed.append(item)
        active[sym] = None

    for ts in selected:
        loc = index.get_loc(ts)
        if isinstance(loc, slice) or isinstance(loc, np.ndarray):
            continue
        prev_ts = index[max(0, int(loc) - 1)]
        for sym in result.open_positions.columns:
            after = float(result.open_positions.at[ts, sym])
            order = float(result.asset_orders.at[ts, sym])
            before = after - order
            old_sign = int(np.sign(before))
            new_sign = int(np.sign(after))
            gross = float(result.asset_gross.at[ts, sym])
            fee = float(result.asset_fees.at[ts, sym])
            funding = float(result.asset_funding.at[ts, sym])

            if old_sign == new_sign:
                if old_sign == 0:
                    continue
                if active[sym] is None:
                    active[sym] = begin(sym, ts, old_sign, inherited=(ts == selected[0]))
                active[sym]["pnl"] += gross - fee - funding
                continue

            open_px = float(data.frames["open"].reindex(index).at[ts, sym]) if sym in data.close.columns else np.nan
            prev_close = float(data.close.reindex(index).at[prev_ts, sym]) if sym in data.close.columns else np.nan
            close_px = float(data.close.reindex(index).at[ts, sym]) if sym in data.close.columns else np.nan
            old_gross, new_gross = split_gross_on_transition(
                gross, before, after, open_px, prev_close, close_px
            )

            if old_sign != 0 and new_sign != 0:
                denom = abs(before) + abs(after)
                fee_old = fee * abs(before) / denom if denom > 1e-12 else fee * 0.5
                fee_new = fee - fee_old
            elif old_sign != 0:
                fee_old, fee_new = fee, 0.0
            else:
                fee_old, fee_new = 0.0, fee

            if old_sign != 0:
                if active[sym] is None:
                    active[sym] = begin(sym, ts, old_sign, inherited=True)
                active[sym]["pnl"] += old_gross - fee_old - funding
                close_trade(sym, ts)

            if new_sign != 0:
                active[sym] = begin(sym, ts, new_sign, inherited=False)
                active[sym]["pnl"] += new_gross - fee_new

    for sym, item in active.items():
        if item is not None and not item["inherited"]:
            open_excluded += 1
    return closed, int(open_excluded)


def trade_metrics(trades: list[dict]) -> dict:
    pnl = np.array([float(x["pnl_return"]) for x in trades], dtype=float)
    if not len(pnl):
        return {
            "closed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "trade_win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_winning_trade": 0.0,
            "avg_losing_trade": 0.0,
            "avg_losing_trade_abs": 0.0,
            "payoff_ratio": 0.0,
            "max_consecutive_losing_trades": 0,
        }
    winners = pnl[pnl > 0]
    losers = pnl[pnl < 0]
    gross_profit = float(winners.sum()) if len(winners) else 0.0
    gross_loss = float(abs(losers.sum())) if len(losers) else 0.0
    avg_win = float(winners.mean()) if len(winners) else 0.0
    avg_loss = float(losers.mean()) if len(losers) else 0.0
    pf = gross_profit / gross_loss if gross_loss > 1e-12 else (999.0 if gross_profit > 0 else 0.0)
    payoff = avg_win / abs(avg_loss) if avg_loss < -1e-12 else (999.0 if avg_win > 0 else 0.0)
    return {
        "closed_trades": int(len(pnl)),
        "winning_trades": int(len(winners)),
        "losing_trades": int(len(losers)),
        "trade_win_rate": float(len(winners) / len(pnl)),
        "profit_factor": float(pf),
        "avg_winning_trade": avg_win,
        "avg_losing_trade": avg_loss,
        "avg_losing_trade_abs": abs(avg_loss),
        "payoff_ratio": float(payoff),
        "max_consecutive_losing_trades": max_streak(pnl < 0),
    }


def path_metrics(result, start: pd.Timestamp, end: pd.Timestamp, trades: list[dict]) -> dict:
    equity = result.equity.loc[start:end].dropna().astype(float)
    if len(equity) < 2:
        return {}
    normalized = equity / equity.iloc[0]
    hourly = normalized.pct_change(fill_method=None).fillna(0.0)
    daily_equity = normalized.resample("1D").last().dropna()
    daily = daily_equity.pct_change(fill_method=None).dropna()
    dd = normalized / normalized.cummax() - 1.0
    elapsed_hours = max((normalized.index[-1] - normalized.index[0]).total_seconds() / 3600.0, 1.0)
    roi = float(normalized.iloc[-1] - 1.0)
    cagr = -1.0 if normalized.iloc[-1] <= 0 else float(normalized.iloc[-1] ** ((365.25 * 24) / elapsed_hours) - 1.0)
    r30 = rolling_compounded(daily, 30)
    r90 = rolling_compounded(daily, 90)
    t = trade_metrics(trades)
    fees = float(result.fees.loc[start:end].sum())
    funding = float(result.funding.loc[start:end].sum())
    turnover = float(result.turnover.loc[start:end].sum())
    return {
        "roi": roi,
        "terminal_multiple": float(normalized.iloc[-1]),
        "profit_brl": float(INITIAL_CAPITAL_BRL * roi),
        "cagr": cagr,
        "max_drawdown": float(dd.min()),
        "max_drawdown_abs": abs(float(dd.min())),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "worst_day_abs": abs(float(daily.min())) if len(daily) else 0.0,
        "positive_day_ratio": float((daily > 0).mean()) if len(daily) else 0.0,
        "positive_days": int((daily > 0).sum()),
        "negative_days": int((daily < 0).sum()),
        "max_consecutive_negative_days": max_streak((daily < 0).to_numpy()),
        "rolling_30d_positive_rate": float((r30 > 0).mean()) if len(r30) else 0.0,
        "rolling_90d_positive_rate": float((r90 > 0).mean()) if len(r90) else 0.0,
        "rolling_90d_median_return": float(r90.median()) if len(r90) else 0.0,
        "rolling_90d_p10_return": float(r90.quantile(0.10)) if len(r90) else 0.0,
        "rolling_90d_dispersion": float(r90.std(ddof=0)) if len(r90) else 0.0,
        "turnover": turnover,
        "fees_multiple": fees,
        "funding_cost_multiple": funding,
        "hours": int(len(hourly)),
        **t,
    }


def regime_path_metrics(
    result,
    mask: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    trades: list[dict],
) -> dict:
    equity = result.equity.loc[start:end].dropna().astype(float)
    if len(equity) < 2:
        return {}
    hourly = equity.pct_change(fill_method=None).fillna(0.0)
    m = mask.reindex(hourly.index).fillna(False).astype(bool)
    selected = hourly.where(m, 0.0)
    active = hourly[m]
    if not int(m.sum()):
        return {"active_hours": 0, **trade_metrics(trades)}
    path = (1.0 + selected.clip(lower=-0.999999)).cumprod()
    dd = path / path.cummax() - 1.0
    per_hour = hourly[m]
    frame = pd.DataFrame({"r": hourly, "active": m})
    active_days = frame[frame["active"]].groupby(frame.index.normalize())["r"].apply(
        lambda x: float(np.prod(1.0 + x.to_numpy()) - 1.0)
    )
    return {
        "roi": float(path.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "max_drawdown_abs": abs(float(dd.min())),
        "worst_day": float(active_days.min()) if len(active_days) else 0.0,
        "worst_day_abs": abs(float(active_days.min())) if len(active_days) else 0.0,
        "positive_day_ratio": float((active_days > 0).mean()) if len(active_days) else 0.0,
        "positive_days": int((active_days > 0).sum()),
        "negative_days": int((active_days < 0).sum()),
        "max_consecutive_negative_days": max_streak((active_days < 0).to_numpy()),
        "active_hours": int(m.sum()),
        "active_days": int(len(active_days)),
        "mean_active_hour": float(per_hour.mean()) if len(per_hour) else 0.0,
        **trade_metrics(trades),
    }


def regime_metrics(
    result,
    trades: list[dict],
    direction: pd.Series,
    vol: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    decision_direction = direction.shift(1)
    decision_vol = vol.shift(1)
    out: dict[str, dict] = {"directional": {}, "volatility": {}, "matrix": {}}
    for state in ("BULL", "BEAR", "SIDEWAYS"):
        tr = [x for x in trades if x["direction_regime"] == state]
        out["directional"][state] = regime_path_metrics(
            result, decision_direction.eq(state), start, end, tr
        )
    for state in ("HIGH_VOLATILITY", "LOW_VOLATILITY"):
        tr = [x for x in trades if x["volatility_regime"] == state]
        out["volatility"][state] = regime_path_metrics(
            result, decision_vol.eq(state), start, end, tr
        )
    for d in ("BULL", "BEAR", "SIDEWAYS"):
        for v in ("HIGH_VOLATILITY", "LOW_VOLATILITY"):
            key = f"{d}__{v}"
            tr = [x for x in trades if x["direction_regime"] == d and x["volatility_regime"] == v]
            out["matrix"][key] = regime_path_metrics(
                result, decision_direction.eq(d) & decision_vol.eq(v), start, end, tr
            )
    return out


def analyze_result(result, data, direction, vol, start, end) -> dict:
    trades, open_excluded = trade_episodes(result, data, start, end, direction, vol)
    return {
        "global": path_metrics(result, start, end, trades),
        "regimes": regime_metrics(result, trades, direction, vol, start, end),
        "trade_diagnostics": {
            "closed_trade_episodes": int(len(trades)),
            "open_trade_episodes_excluded": int(open_excluded),
            "fee_attribution_note": "same-sign rebalances remain one trade; close/open flips split transition fees by pre/post exposure and split the exact asset gross contribution using overnight/intraday signed-return proportions; inherited trades at the analysis boundary are excluded",
        },
    }


def metric_envelope(engine_metrics: dict[str, dict]) -> dict:
    out = {}
    for metric in HIGHER_IS_BETTER:
        values = [(name, m.get(metric)) for name, m in engine_metrics.items()]
        values = [(n, float(v)) for n, v in values if v is not None and np.isfinite(v)]
        if values:
            name, value = max(values, key=lambda x: x[1])
            out[metric] = {"best": value, "engine": name, "direction": "higher"}
    for metric in LOWER_IS_BETTER:
        values = [(name, m.get(metric)) for name, m in engine_metrics.items()]
        values = [(n, float(v)) for n, v in values if v is not None and np.isfinite(v)]
        if values:
            name, value = min(values, key=lambda x: x[1])
            out[metric] = {"best": value, "engine": name, "direction": "lower"}
    return out


def candidate_vs_envelope(candidate: dict, envelope: dict) -> dict:
    out = {}
    for metric, item in envelope.items():
        value = candidate.get(metric)
        if value is None or not np.isfinite(value):
            continue
        best = float(item["best"])
        higher = item["direction"] == "higher"
        passed = float(value) >= best if higher else float(value) <= best
        out[metric] = {
            "candidate": float(value),
            "benchmark_best": best,
            "benchmark_engine": item["engine"],
            "passed": bool(passed),
            "delta": float(value - best),
        }
    return out


def regime_envelopes(engine_analyses: dict[str, dict]) -> tuple[dict, dict]:
    env = {"directional": {}, "volatility": {}, "matrix": {}}
    cmp = {"directional": {}, "volatility": {}, "matrix": {}}
    for bucket in env:
        states = next(iter(engine_analyses.values()))["regimes"][bucket].keys()
        for state in states:
            benchmark = {
                name: analysis["regimes"][bucket][state]
                for name, analysis in engine_analyses.items()
                if name != "r98"
            }
            env[bucket][state] = metric_envelope(benchmark)
            cmp[bucket][state] = candidate_vs_envelope(
                engine_analyses["r98"]["regimes"][bucket][state], env[bucket][state]
            )
    return env, cmp


def analyze_section(results, data_map, direction, vol, start, end) -> dict:
    analyses = {
        name: analyze_result(result, data_map[name], direction, vol, start, end)
        for name, result in results.items()
    }
    benchmark_global = {name: x["global"] for name, x in analyses.items() if name != "r98"}
    global_env = metric_envelope(benchmark_global)
    regime_env, regime_cmp = regime_envelopes(analyses)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "engines": analyses,
        "benchmark_envelope_global": global_env,
        "r98_vs_global_envelope": candidate_vs_envelope(analyses["r98"]["global"], global_env),
        "benchmark_envelope_regimes": regime_env,
        "r98_vs_regime_envelope": regime_cmp,
    }


def exact_benchmark_result(item: dict, cost: float):
    return r98.r36.exact_fast(
        item["data"],
        item["targets"],
        cost_per_side=float(cost),
        **item["kwargs"],
    )


def build_cost_results(mode: str, cfg, data, raw, ex, guard, gross, benchmarks):
    if mode == "base":
        v15_cost = float(ex["base_cost_per_side"])
    elif mode == "severe":
        v15_cost = float(ex["severe_cost_per_side"])
    elif mode == "super_severe_1p5x":
        v15_cost = float(ex["severe_cost_per_side"]) * 1.5
    else:
        raise ValueError(mode)

    current, _, _, _, _ = r98.build_all(data, raw, ex, guard, gross, v15_cost)
    out = {"r98": current}
    for name, item in benchmarks.items():
        execution = item["execution"]
        cost = (
            float(execution["base_cost_per_side"])
            if mode == "base"
            else float(execution["severe_cost_per_side"]) * (1.5 if mode == "super_severe_1p5x" else 1.0)
        )
        out[name] = exact_benchmark_result(item, cost)
    return out


def structural_diagnosis(base_section: dict, holdout_section: dict) -> dict:
    global_cmp = base_section["r98_vs_global_envelope"]
    passed_global = sum(int(v["passed"]) for v in global_cmp.values())
    failed_global = [k for k, v in global_cmp.items() if not v["passed"]]

    directional = base_section["engines"]["r98"]["regimes"]["directional"]
    volatility = base_section["engines"]["r98"]["regimes"]["volatility"]
    positive_directional = {
        k: bool(v.get("roi", 0.0) > 0.0 and v.get("profit_factor", 0.0) > 1.0)
        for k, v in directional.items()
        if v.get("active_hours", 0) >= 24 * 30
    }
    positive_vol = {
        k: bool(v.get("roi", 0.0) > 0.0 and v.get("profit_factor", 0.0) > 1.0)
        for k, v in volatility.items()
        if v.get("active_hours", 0) >= 24 * 30
    }

    hold_cmp = holdout_section["r98_vs_global_envelope"]
    hold_failed = [k for k, v in hold_cmp.items() if not v["passed"]]
    return {
        "r64_status_under_new_standard": "REJECTED",
        "r98_status_under_new_standard": "BASELINE_ONLY_NOT_PROMOTED",
        "global_envelope_dimensions_passed": int(passed_global),
        "global_envelope_dimensions_total": int(len(global_cmp)),
        "global_failed_dimensions": failed_global,
        "holdout_failed_dimensions": hold_failed,
        "directional_regime_positive_roi_and_pf_gt_1": positive_directional,
        "volatility_regime_positive_roi_and_pf_gt_1": positive_vol,
        "all_directional_regimes_positive": bool(positive_directional and all(positive_directional.values())),
        "all_volatility_regimes_positive": bool(positive_vol and all(positive_vol.values())),
        "known_architecture_failures": [
            "R98 remains primarily a V15-derived hedge/risk/exposure router rather than an independent all-regime alpha engine",
            "R37/R55 hedge direction is -sign(net); a BTC crash can add long BTC to a winning net-short book",
            "original V99 stress/chop/damage stack applies portfolio-wide multipliers that can cut the correct side",
            "old promotion gates do not require trade-quality and regime-quality dominance",
        ],
        "rebuild_required": True,
    }


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r98.r36.v15_setup()
    benchmarks = r98.r86.r55.benchmark_items(cfg, data, raw, ex, guard, gross)

    result_sets = {}
    for mode in ("base", "severe", "super_severe_1p5x"):
        result_sets[mode] = build_cost_results(mode, cfg, data, raw, ex, guard, gross, benchmarks)

    data_map = {"r98": data}
    data_map.update({name: item["data"] for name, item in benchmarks.items()})

    all_results = [result for group in result_sets.values() for result in group.values()]
    common_start = max(x.equity.index[0] for x in all_results)
    common_end = min(x.equity.index[-1] for x in all_results)
    holdout_start = max(common_start, TRAIN_END + pd.Timedelta(hours=1))

    direction, vol_state, regime_diag = classify_regimes(data.close)
    regime_coverage = {
        "directional": direction.loc[common_start:common_end].value_counts(normalize=True).to_dict(),
        "volatility": vol_state.loc[common_start:common_end].value_counts(normalize=True).to_dict(),
    }

    base = analyze_section(result_sets["base"], data_map, direction, vol_state, common_start, common_end)
    holdout = analyze_section(result_sets["base"], data_map, direction, vol_state, holdout_start, common_end)
    severe = analyze_section(result_sets["severe"], data_map, direction, vol_state, common_start, common_end)
    super_severe = analyze_section(result_sets["super_severe_1p5x"], data_map, direction, vol_state, common_start, common_end)

    out = {
        "study": "V99 R105 all-regime structural audit",
        "status": "DIAGNOSTIC_BASELINE_ONLY_DO_NOT_PROMOTE_DO_NOT_REWRITE_FROZEN",
        "mission": "replace the old V99 overlay-only evaluation with a metric-envelope and all-regime audit before any structural rebuild candidate is allowed",
        "immutable": {
            "v16_frozen_modified": False,
            "v99_frozen_modified": False,
            "research_branch_only": True,
        },
        "regime_definition": {
            "directional": "V16-derived causal 45d BTC momentum + 14d/90d EMA + 30d breadth; 7d -10% shock forces BEAR; remainder SIDEWAYS",
            "volatility": "HIGH when trailing 7d BTC hourly volatility >= trailing 90d BTC hourly volatility; otherwise LOW; both use only closed history",
            "decision_alignment": "hour/trade outcome is attributed to the regime known at the previous close",
            "no_r105_threshold_fit": True,
            "coverage": regime_coverage,
        },
        "metric_policy": {
            "initial_capital_brl": INITIAL_CAPITAL_BRL,
            "higher_is_better": list(HIGHER_IS_BETTER),
            "lower_is_better": list(LOWER_IS_BETTER),
            "benchmark_envelope": "best raw value among V13/V14/V15/V16 for each metric independently",
            "profit_factor_basis": "closed trade-episode return contributions after modeled fees and funding",
            "trade_episode_policy": "same-sign scaling remains one trade; flips close one episode and open another; inherited/open boundary trades are excluded",
        },
        "base": base,
        "holdout": holdout,
        "severe_cost": severe,
        "super_severe_1p5x": super_severe,
        "diagnosis": structural_diagnosis(base, holdout),
        "next_architecture": {
            "alpha_sleeves": [
                "symmetric directional trend",
                "high-volatility breakout/impulse",
                "sideways market-neutral reversal/mean-reversion",
                "funding carry/positioning",
            ],
            "router": "causal regime allocator with independently validated sleeve P&L",
            "risk": "side-aware and P&L-aware; protect misaligned losing side without automatically amputating aligned winning side",
            "portfolio": "sleeve-aware risk budgets, correlation/overlap diagnostics, hard gross cap",
            "promotion": "global + holdout + regime + trade quality + severe costs + adversarial calendar/tail tests",
        },
        "r64_new_standard_verdict": "REJECTED",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
        "disclosure": "Historical research diagnostic only. R105 changes no frozen engine and promotes no trading candidate. It establishes the all-regime benchmark envelope that the structural rebuild must attack.",
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")

    summary = {
        "study": out["study"],
        "common_start": common_start.isoformat(),
        "common_end": common_end.isoformat(),
        "r64": out["r64_new_standard_verdict"],
        "r98": out["diagnosis"],
        "r98_global": base["engines"]["r98"]["global"],
        "benchmark_global_envelope": base["benchmark_envelope_global"],
        "r98_directional_regimes": base["engines"]["r98"]["regimes"]["directional"],
        "r98_volatility_regimes": base["engines"]["r98"]["regimes"]["volatility"],
    }
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
