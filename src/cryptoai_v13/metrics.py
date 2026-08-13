from __future__ import annotations

import numpy as np
import pandas as pd


HOURS_PER_YEAR = 365.25 * 24


def summarize(equity: pd.Series, turnover: pd.Series | None = None,
              exposure: pd.Series | None = None, ruin: bool = False) -> dict:
    equity = equity.dropna()
    if len(equity) < 2:
        return {"return": 0.0, "cagr": 0.0, "max_drawdown": 0.0, "sharpe": 0.0,
                "ruin": ruin, "hours": int(len(equity))}
    returns = equity.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    elapsed_hours = max((equity.index[-1] - equity.index[0]).total_seconds() / 3600, 1.0)
    total = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    cagr = -1.0 if equity.iloc[-1] <= 0 else float((equity.iloc[-1] / equity.iloc[0]) ** (HOURS_PER_YEAR / elapsed_hours) - 1.0)
    drawdown = equity.div(equity.cummax()).sub(1.0)
    std = float(returns.std(ddof=0))
    sharpe = float(returns.mean() / std * np.sqrt(HOURS_PER_YEAR)) if std > 0 else 0.0
    downside = returns.clip(upper=0)
    downside_std = float(np.sqrt((downside ** 2).mean()))
    sortino = float(returns.mean() / downside_std * np.sqrt(HOURS_PER_YEAR)) if downside_std > 0 else 0.0
    monthly = equity.resample("ME").last().pct_change().dropna()
    annual = equity.resample("YE").last().pct_change()
    if len(annual):
        first_year = equity.index[0].year
        first_end = equity.loc[equity.index.year == first_year]
        if len(first_end):
            annual.iloc[0] = first_end.iloc[-1] / first_end.iloc[0] - 1.0
    result = {
        "return": total,
        "cagr": cagr,
        "max_drawdown": float(drawdown.min()),
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": float(cagr / abs(drawdown.min())) if drawdown.min() < 0 else 0.0,
        "positive_month_ratio": float((monthly > 0).mean()) if len(monthly) else 0.0,
        "median_month": float(monthly.median()) if len(monthly) else 0.0,
        "worst_month": float(monthly.min()) if len(monthly) else 0.0,
        "ruin": bool(ruin),
        "hours": int(len(equity)),
        "annual_returns": {str(ts.year): float(value) for ts, value in annual.items() if pd.notna(value)},
    }
    if turnover is not None:
        aligned = turnover.reindex(equity.index).fillna(0.0)
        result["turnover"] = float(aligned.sum())
        result["position_decisions_per_month"] = float((aligned > 1e-8).sum() / max(elapsed_hours / (24 * 30.4375), 1e-9))
    if exposure is not None:
        aligned = exposure.reindex(equity.index).fillna(0.0)
        result["avg_gross_exposure"] = float(aligned.mean())
        result["max_gross_exposure"] = float(aligned.max())
        result["cash_hour_ratio"] = float((aligned < 1e-8).mean())
    return result


def slice_summary(equity: pd.Series, turnover: pd.Series, exposure: pd.Series,
                  start: str, end: str) -> dict:
    selected = equity.loc[start:end]
    if len(selected) < 2:
        return summarize(selected)
    selected = selected / selected.iloc[0]
    return summarize(selected, turnover.loc[selected.index], exposure.loc[selected.index])
