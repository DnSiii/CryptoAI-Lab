from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import load_rows, scale_portfolio
from run_meta_allocator_search import meta_targets


def evaluate(result) -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    rows = {row["index"]: row for row in load_rows()}
    config = json.loads((PROJECT / "config" / "candidate_v13_meta_ensemble.json").read_text())
    data = load_data(PROJECT)
    ids = config["component_ids"]
    cost = config["execution"]["base_cost_per_side"]
    components = {index: build_targets(data, StrategySpec(**rows[index]["spec"])) for index in ids}
    returns = pd.DataFrame({index: screen(data, targets, cost).equity.pct_change(fill_method=None).fillna(0.0)
                            for index, targets in components.items()})
    neighborhood = []
    grid = itertools.product(
        (24 * 120, 24 * 150, 24 * 180, 24 * 210, 24 * 240, 24 * 270, 24 * 365),
        (2, 3, 4), (12, 24, 48, 72), ("return", "sharpe"), (False, True),
    )
    for number, (lookback, top_n, rebalance, mode, cash) in enumerate(grid, 1):
        base = meta_targets(components, returns, lookback, top_n, rebalance, mode, cash)
        targets = scale_portfolio(data, base, 0.4, 1.5, 24 * 60, 24)
        metric = evaluate(screen(data, targets, cost))
        neighborhood.append({"params": {"lookback": lookback, "top_n": top_n,
                                         "rebalance": rebalance, "mode": mode, "cash": cash},
                             "metric": metric})
        if number % 100 == 0:
            print(f"neighborhood {number}", flush=True)

    phases = []
    for phase in range(24):
        meta = config["meta_allocator"]
        base = meta_targets(components, returns, meta["lookback_hours"], meta["top_n"],
                            meta["rebalance_hours"], meta["score_mode"],
                            meta["cash_when_negative"], phase=phase)
        risk = config["risk_overlay"]
        targets = scale_portfolio(data, base, risk["target_volatility"],
                                  risk["maximum_gross_leverage"],
                                  risk["volatility_lookback_hours"], risk["rebalance_hours"],
                                  phase=phase)
        phases.append({"phase": phase, "metric": evaluate(screen(data, targets, cost))})

    removals = []
    for removed in ids:
        kept = [index for index in ids if index != removed]
        subset = {index: components[index] for index in kept}
        subset_returns = returns[kept]
        meta = config["meta_allocator"]
        base = meta_targets(subset, subset_returns, meta["lookback_hours"],
                            min(meta["top_n"], len(kept)), meta["rebalance_hours"],
                            meta["score_mode"], meta["cash_when_negative"])
        risk = config["risk_overlay"]
        targets = scale_portfolio(data, base, risk["target_volatility"],
                                  risk["maximum_gross_leverage"], risk["volatility_lookback_hours"],
                                  risk["rebalance_hours"])
        removals.append({"removed_component": removed,
                         "metric": evaluate(screen(data, targets, cost))})

    output = PROJECT / "reports" / "candidate_v13_robustness_screen.json"
    payload = {"neighborhood": neighborhood, "phases": phases,
               "leave_one_component_out": removals}
    output.write_text(json.dumps(payload, indent=2) + "\n")
    viable = [row for row in neighborhood if row["metric"]["cagr"] >= 0.5
              and row["metric"]["max_drawdown"] >= -0.35]
    print(json.dumps({
        "neighborhood_count": len(neighborhood),
        "neighborhood_passing_gate": len(viable),
        "phase_cagr_range": [min(row["metric"]["cagr"] for row in phases),
                             max(row["metric"]["cagr"] for row in phases)],
        "phase_worst_drawdown": min(row["metric"]["max_drawdown"] for row in phases),
        "removals": removals,
    }, indent=2))
