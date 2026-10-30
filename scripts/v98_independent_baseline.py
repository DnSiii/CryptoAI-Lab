from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

# Reuse only neutral infrastructure: canonical data loader, PIT liquidity universe,
# and the execution simulator. No V13/V14/V15/V16/V99 alpha logic is imported.
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data

CONFIG_PATH = PROJECT / "config" / "v98_independent.json"
REPORT_PATH = PROJECT / "reports" / "v98_independent_baseline.json"
POSITIONS_PATH = PROJECT / "reports" / "v98_independent_baseline_positions.csv"


def _rank01(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True, method="average")


def _winsorize_cross_section(frame: pd.DataFrame, lower: float = 0.10,
                             upper: float = 0.90) -> pd.DataFrame:
    lo = frame.quantile(lower, axis=1)
    hi = frame.quantile(upper, axis=1)
    return frame.clip(lower=lo, upper=hi, axis=0)


def build_targets(data, membership: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Independent V98 architecture.

    Economic design:
    - cross-sectional medium/slow relative strength for persistent trends;
    - residual momentum vs BTC to avoid simply buying market beta;
    - inverse-volatility allocation to reduce single-name domination;
    - breadth/BTC regime routing with asymmetric long/short behavior;
    - daily rebalance to control turnover.

    Every feature at row t is explicitly shifted by one hour, so the target
    labelled t only uses information available at t-1 or earlier.
    """
    c = cfg["architecture"]
    close = data.close
    valid = membership & close.notna()

    # Information boundary: all feature inputs are known by t-1.
    lagged = close.shift(1)
    ret_fast = lagged.pct_change(c["momentum_fast_hours"], fill_method=None)
    ret_med = lagged.pct_change(c["momentum_medium_hours"], fill_method=None)
    ret_slow = lagged.pct_change(c["momentum_slow_hours"], fill_method=None)

    # BTC beta and residual return are estimated only from historical hourly returns.
    hourly = lagged.pct_change(fill_method=None)
    btc = hourly["BTCUSDT"]
    beta = hourly.rolling(c["residual_beta_lookback_hours"], min_periods=720).cov(btc).div(
        btc.rolling(c["residual_beta_lookback_hours"], min_periods=720).var(), axis=0
    )
    btc_med = lagged["BTCUSDT"].pct_change(c["momentum_medium_hours"], fill_method=None)
    residual_med = ret_med.sub(beta.mul(btc_med, axis=0))

    # Blend rank-based signals rather than raw returns to avoid domination by volatile coins.
    rs = 0.25 * _rank01(ret_fast) + 0.45 * _rank01(ret_med) + 0.30 * _rank01(ret_slow)
    residual_rank = _rank01(_winsorize_cross_section(residual_med))
    score = (0.65 * rs + 0.35 * residual_rank).where(valid)

    vol = hourly.rolling(c["volatility_lookback_hours"], min_periods=360).std() * np.sqrt(365.25 * 24)
    inv_vol = (1.0 / vol.replace(0.0, np.nan)).clip(upper=20.0).where(valid)

    btc_trend = lagged["BTCUSDT"].pct_change(c["trend_hours"], fill_method=None)
    asset_trend = lagged.pct_change(c["trend_hours"], fill_method=None)
    breadth = (asset_trend.gt(0.0) & valid).sum(axis=1).div(valid.sum(axis=1).replace(0, np.nan))

    risk_on = (btc_trend > 0.0) & (breadth >= c["breadth_threshold"])
    risk_off = (btc_trend < 0.0) & (breadth <= (1.0 - c["breadth_threshold"] + 0.10))

    long_rank = score.rank(axis=1, ascending=False, method="first")
    short_rank = score.rank(axis=1, ascending=True, method="first")

    long_mask = (long_rank <= c["long_count"]) & asset_trend.gt(0.0) & valid
    short_mask = (short_rank <= c["short_count"]) & asset_trend.lt(0.0) & valid

    long_raw = inv_vol.where(long_mask, 0.0)
    short_raw = inv_vol.where(short_mask, 0.0)
    long_w = long_raw.div(long_raw.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    short_w = short_raw.div(short_raw.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    # Asymmetry is deliberate: risk-on emphasizes longs; risk-off emphasizes shorts;
    # neutral state remains balanced rather than forcing directional market exposure.
    targets = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    targets.loc[risk_on] = (
        0.90 * long_w.loc[risk_on] - 0.35 * short_w.loc[risk_on]
    ) * c["risk_on_gross"]
    targets.loc[risk_off] = (
        0.25 * long_w.loc[risk_off] - 0.75 * short_w.loc[risk_off]
    ) * c["risk_off_gross"]
    neutral = ~(risk_on | risk_off)
    targets.loc[neutral] = (
        0.50 * long_w.loc[neutral] - 0.50 * short_w.loc[neutral]
    ) * c["neutral_gross"]

    gross = targets.abs().sum(axis=1)
    scale = (c["gross_cap"] / gross.replace(0, np.nan)).clip(upper=1.0).fillna(0.0)
    targets = targets.mul(scale, axis=0)

    # Fixed daily rebalance. Between events the requested target is unchanged.
    event = pd.Series(np.arange(len(targets)) % c["rebalance_hours"] == 0, index=targets.index)
    targets = targets.where(event, np.nan).ffill().fillna(0.0)
    return targets


def _daily_returns(equity: pd.Series) -> pd.Series:
    daily = equity.resample("1D").last().dropna()
    return daily.pct_change(fill_method=None).dropna()


def metrics(result, start: str, end: str) -> dict:
    equity = result.equity.loc[start:end].dropna()
    positions = result.positions.loc[start:end]
    turnover = result.turnover.loc[start:end]
    if len(equity) < 2:
        return {"error": "insufficient_data"}
    total = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    years = (equity.index[-1] - equity.index[0]).total_seconds() / (365.25 * 86400)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[0] > 0 else np.nan
    dd = equity.div(equity.cummax()).sub(1.0)
    daily = _daily_returns(equity)
    wins = daily[daily > 0]
    losses = daily[daily < 0]
    profit_factor = float(wins.sum() / abs(losses.sum())) if abs(losses.sum()) > 0 else np.inf
    payoff = float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) and losses.mean() != 0 else np.nan
    return {
        "total_return": total,
        "cagr": cagr,
        "max_drawdown": float(dd.min()),
        "worst_day": float(daily.min()) if len(daily) else np.nan,
        "profit_factor_daily": profit_factor,
        "payoff_daily": payoff,
        "win_rate_daily": float((daily > 0).mean()) if len(daily) else np.nan,
        "positive_days": int((daily > 0).sum()),
        "negative_days": int((daily < 0).sum()),
        "days": int(len(daily)),
        "turnover_sum": float(turnover.sum()),
        "avg_gross": float(positions.abs().sum(axis=1).mean()),
        "max_gross": float(positions.abs().sum(axis=1).max()),
        "ruin": bool(result.ruin),
    }


def evaluate_scenario(data, targets, cost: float, debit_mult: float, credit_mult: float):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        gross_guard_cap=1.50,
        funding_debit_multiplier=debit_mult,
        funding_credit_multiplier=credit_mult,
    )


def regime_metrics(result, data, start: str, end: str) -> dict:
    # Ex-post descriptive regimes only; never used to choose parameters.
    btc = data.close["BTCUSDT"].shift(1)
    trend90 = btc.pct_change(24 * 90, fill_method=None)
    vol30 = btc.pct_change(fill_method=None).rolling(24 * 30, min_periods=24 * 15).std()
    vol_median = vol30.loc[:"2025-12-31"].median()
    labels = pd.Series("sideways", index=btc.index, dtype=object)
    labels[trend90 > 0.15] = "bull"
    labels[trend90 < -0.15] = "bear"
    labels[vol30 > vol_median * 1.5] = labels[vol30 > vol_median * 1.5] + "_highvol"
    out = {}
    eq = result.equity
    for label in sorted(labels.dropna().unique()):
        mask = (labels == label) & (labels.index >= pd.Timestamp(start)) & (labels.index <= pd.Timestamp(end))
        idx = labels.index[mask]
        if len(idx) < 48:
            continue
        hourly = eq.pct_change(fill_method=None).reindex(idx).dropna()
        out[label] = {
            "hours": int(len(hourly)),
            "return_sum_approx": float(hourly.sum()),
            "positive_hour_ratio": float((hourly > 0).mean()),
        }
    return out


def concentration_metrics(result, start: str, end: str) -> dict:
    pos = result.positions.loc[start:end].abs()
    gross = pos.sum(axis=1).replace(0, np.nan)
    shares = pos.div(gross, axis=0)
    return {
        "mean_top1_weight_share": float(shares.max(axis=1).mean()),
        "p95_top1_weight_share": float(shares.max(axis=1).quantile(0.95)),
        "mean_active_assets": float((pos > 1e-10).sum(axis=1).mean()),
    }


def main() -> None:
    cfg = json.loads(CONFIG_PATH.read_text())
    data = load_data(PROJECT, cfg["data_config"])
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(f"data validation failed: {validation['errors'][:5]}")

    c = cfg["architecture"]
    liquid, membership = point_in_time_liquid_view(
        data,
        top_n=c["liquidity_top_n"],
        lookback_hours=c["liquidity_lookback_hours"],
        minimum_history_hours=c["minimum_history_hours"],
    )
    targets = build_targets(liquid, membership, cfg)

    scenarios = {}
    results = {}
    for name in ("base", "severe", "supersevere"):
        stress = cfg["funding_stress"][name]
        result = evaluate_scenario(
            liquid,
            targets,
            cfg["costs"][f"{name}_per_side"],
            stress["debit_multiplier"],
            stress["credit_multiplier"],
        )
        results[name] = result
        scenarios[name] = {
            "research": metrics(result, cfg["research_start"], cfg["training_end"]),
            "holdout": metrics(result, cfg["holdout_start"], cfg["holdout_end"]),
        }

    base = results["base"]
    folds = {
        fold["name"]: metrics(base, fold["start"], fold["end"])
        for fold in cfg["folds"]
    }

    report = {
        "engine": "V98 Independent",
        "version": "baseline_zero_001",
        "status": "candidate_not_promoted",
        "selection_policy": {
            "holdout_used_for_selection": False,
            "v99_used_for_selection": False,
            "parameter_search": "none; one predeclared economically motivated architecture",
            "information_lag": "all alpha inputs shifted one hour before target timestamp; execution occurs later via simulator",
        },
        "architecture": cfg["architecture"],
        "data_validation": {"error_count": len(validation["errors"]), "symbols": list(data.symbols)},
        "scenarios": scenarios,
        "folds": folds,
        "regimes_train": regime_metrics(base, liquid, cfg["research_start"], cfg["training_end"]),
        "regimes_holdout": regime_metrics(base, liquid, cfg["holdout_start"], cfg["holdout_end"]),
        "concentration_train": concentration_metrics(base, cfg["research_start"], cfg["training_end"]),
        "concentration_holdout": concentration_metrics(base, cfg["holdout_start"], cfg["holdout_end"]),
        "next_step": "diagnose failure modes on training/folds only before any architecture revision; do not inspect holdout for parameter selection",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=True) + "\n")
    targets.to_csv(POSITIONS_PATH, index_label="timestamp")
    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
