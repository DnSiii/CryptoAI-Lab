from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import load_rows, scale_portfolio
from run_meta_allocator_search import meta_targets


def build_candidate(data, rows: dict[int, dict], config: dict,
                    component_ids: list[int] | None = None) -> pd.DataFrame:
    component_ids = component_ids or config["component_ids"]
    cost = config["execution"]["base_cost_per_side"]
    components = {index: build_targets(data, StrategySpec(**rows[index]["spec"]))
                  for index in component_ids}
    returns = pd.DataFrame({
        index: screen(data, targets, cost).equity.pct_change(fill_method=None).fillna(0.0)
        for index, targets in components.items()
    })
    meta = config["meta_allocator"]
    base = meta_targets(components, returns, meta["lookback_hours"], meta["top_n"],
                        meta["rebalance_hours"], meta["score_mode"], meta["cash_when_negative"])
    risk = config["risk_overlay"]
    return scale_portfolio(data, base, risk["target_volatility"],
                           risk["maximum_gross_leverage"],
                           risk["volatility_lookback_hours"], risk["rebalance_hours"])


def metric(result) -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    config = json.loads((PROJECT / "config" / "candidate_v13_meta_ensemble.json").read_text())
    rows = {row["index"]: row for row in load_rows()}
    data = load_data(PROJECT)
    targets = build_candidate(data, rows, config)
    base = exact(data, targets, config["execution"]["base_cost_per_side"])
    severe = exact(data, targets, config["execution"]["severe_cost_per_side"])
    delayed_3h = exact(data, targets.shift(2).fillna(0.0),
                       config["execution"]["base_cost_per_side"])
    report = {
        "config": config,
        "components": {str(index): rows[index]["spec"] for index in config["component_ids"]},
        "exact_base": metric(base),
        "exact_severe_cost": metric(severe),
        "exact_delay_3h": metric(delayed_3h),
        "ruin": {"base": base.ruin, "severe": severe.ruin, "delay_3h": delayed_3h.ruin},
    }
    output = PROJECT / "reports" / "candidate_v13_exact.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    targets.loc["2021-01-01":"2026-07-31 23:00"].to_csv(
        PROJECT / "reports" / "candidate_v13_targets.csv", index_label="timestamp")
    base.equity.loc["2021-01-01":"2026-07-31 23:00"].rename("equity").to_csv(
        PROJECT / "reports" / "candidate_v13_equity.csv", index_label="timestamp")
    print(json.dumps(report, indent=2))
