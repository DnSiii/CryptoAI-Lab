from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import load_rows, scale_portfolio


COMPONENT_IDS = (362, 673, 1428, 1434, 1745)


def meta_targets(component_targets: dict[int, pd.DataFrame], component_returns: pd.DataFrame,
                 lookback: int, top_n: int, rebalance: int, score_mode: str,
                 cash_when_negative: bool, phase: int = 0) -> pd.DataFrame:
    if score_mode == "return":
        score = np.log1p(component_returns.clip(lower=-0.99)).rolling(
            lookback, min_periods=lookback // 2).sum()
    elif score_mode == "sharpe":
        mean = component_returns.rolling(lookback, min_periods=lookback // 2).mean()
        std = component_returns.rolling(lookback, min_periods=lookback // 2).std().replace(0.0, np.nan)
        score = mean.div(std)
    else:
        raise ValueError(score_mode)
    # t's closed return may choose the target decided at t; execution remains t+1.
    rank = score.rank(axis=1, ascending=False, method="first")
    selected = rank <= top_n
    if cash_when_negative:
        selected &= score > 0.0
    weights = selected.astype(float)
    weights = weights.div(weights.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0)
    event = pd.Series((np.arange(len(weights)) - phase) % rebalance == 0, index=weights.index)
    weights = weights.where(event, np.nan).ffill().fillna(0.0)
    result = sum(component_targets[index].mul(weights[index], axis=0)
                 for index in component_targets)
    return result


if __name__ == "__main__":
    rows = {row["index"]: row for row in load_rows()}
    data = load_data(PROJECT)
    config = json.loads((PROJECT / "config" / "research.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    components = {index: build_targets(data, StrategySpec(**rows[index]["spec"]))
                  for index in COMPONENT_IDS}
    component_returns = pd.DataFrame({
        index: screen(data, targets, cost).equity.pct_change(fill_method=None).fillna(0.0)
        for index, targets in components.items()
    })
    stage_one = []
    meta_grid = itertools.product(
        (24 * 7, 24 * 14, 24 * 30, 24 * 60, 24 * 90, 24 * 180),
        (1, 2, 3), (24, 72, 168), ("return", "sharpe"), (False, True),
    )
    for number, values in enumerate(meta_grid, 1):
        lookback, top_n, rebalance, mode, cash = values
        base = meta_targets(components, component_returns, lookback, top_n, rebalance, mode, cash)
        targets = scale_portfolio(data, base, 0.4, 1.0, lookback=24 * 60, rebalance=24)
        result = screen(data, targets, cost)
        metric = slice_summary(result.equity, result.turnover, result.gross_exposure,
                               "2021-01-01", "2026-07-31 23:00")
        annual = metric["annual_returns"]
        stage_one.append({
            "params": {"lookback": lookback, "top_n": top_n, "rebalance": rebalance,
                       "score_mode": mode, "cash_when_negative": cash},
            "metric": metric,
            "worst_year": min(annual.values()) if annual else -1.0,
        })
        if number % 50 == 0:
            print(number, flush=True)

    robust = [row for row in stage_one if row["metric"]["max_drawdown"] >= -0.4]
    finalists = sorted(robust, key=lambda row: (row["worst_year"], row["metric"]["cagr"]),
                       reverse=True)[:24]
    rows_out = []
    for finalist in finalists:
        params = finalist["params"]
        base = meta_targets(components, component_returns, params["lookback"], params["top_n"],
                            params["rebalance"], params["score_mode"], params["cash_when_negative"])
        for target_vol, max_gross in itertools.product(
                (0.25, 0.3, 0.4, 0.5, 0.6, 0.8), (0.75, 1.0, 1.25, 1.5, 2.0)):
            targets = scale_portfolio(data, base, target_vol, max_gross,
                                      lookback=24 * 60, rebalance=24)
            result = screen(data, targets, cost)
            metric = slice_summary(result.equity, result.turnover, result.gross_exposure,
                                   "2021-01-01", "2026-07-31 23:00")
            annual = metric["annual_returns"]
            rows_out.append({
                "params": {**params, "target_vol": target_vol, "max_gross": max_gross},
                "metric": metric,
                "worst_year": min(annual.values()) if annual else -1.0,
            })
    output = PROJECT / "reports" / "meta_allocator_search.json"
    output.write_text(json.dumps({"component_ids": COMPONENT_IDS,
                                  "stage_one_configurations": len(stage_one),
                                  "finalist_meta_rules": len(finalists),
                                  "overlay_configurations": len(rows_out),
                                  "stage_one": stage_one, "rows": rows_out}, indent=2) + "\n")
    viable = [row for row in rows_out if row["metric"]["max_drawdown"] >= -0.35]
    best = sorted(viable, key=lambda row: (row["worst_year"], row["metric"]["cagr"]), reverse=True)[:10]
    print(json.dumps(best, indent=2))
