from __future__ import annotations

import glob
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
from build_walk_forward import scale_portfolio
from run_meta_allocator_search import meta_targets


SLEEVES = {
    "regime": (1431, 1637, 1515),
    "funding": (898, 550, 721),
    "momentum": (206, 921, 362),
}


def load_expanded_rows() -> dict[int, dict]:
    rows = {}
    for pattern in ("reports/expanded_coarse_*.json", "reports/expanded_regime_*.json"):
        for path in glob.glob(str(PROJECT / pattern)):
            for row in json.loads(Path(path).read_text())["rows"]:
                rows[row["index"]] = row
    if len(rows) != 1800:
        raise ValueError(f"esperados 1800 candidatos expandidos, encontrados {len(rows)}")
    return rows


def build_sleeves(data, rows, cost):
    targets = {}
    returns = {}
    for name, ids in SLEEVES.items():
        parts = [build_targets(data, StrategySpec(**rows[index]["spec"])) for index in ids]
        target = sum(parts) / len(parts)
        targets[name] = target
        returns[name] = screen(data, target, cost).equity.pct_change(fill_method=None).fillna(0.0)
    return targets, pd.DataFrame(returns)


def metric(result):
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    rows = load_expanded_rows()
    config = json.loads((PROJECT / "config" / "candidate_v13_multihorizon.json").read_text())
    cost = config["execution"]["base_cost_per_side"]
    universes = {
        "liquid10": load_data(PROJECT, "research.json"),
        "expanded16": load_data(PROJECT, "research_expanded.json"),
    }
    built = {name: build_sleeves(data, rows, cost) for name, data in universes.items()}

    stage_one = []
    for number, values in enumerate(itertools.product(
        (30, 45, 60, 90, 120, 150, 180, 240, 300, 365),
        (1, 2, 3), (24, 48, 72), ("return", "sharpe"), (False, True),
    ), 1):
        days, top_n, rebalance, mode, cash = values
        metrics = {}
        for universe_name, data in universes.items():
            sleeve_targets, sleeve_returns = built[universe_name]
            base = meta_targets(sleeve_targets, sleeve_returns, days * 24, top_n,
                                rebalance, mode, cash)
            targets = scale_portfolio(data, base, 0.3, 1.0, 1440, 24)
            metrics[universe_name] = metric(screen(data, targets, cost))
        stage_one.append({
            "params": {"days": days, "top_n": top_n, "rebalance": rebalance,
                       "mode": mode, "cash": cash},
            "metrics": metrics,
            "worst_cagr": min(item["cagr"] for item in metrics.values()),
            "worst_drawdown": min(item["max_drawdown"] for item in metrics.values()),
            "worst_year": min(min(item["annual_returns"].values()) for item in metrics.values()),
        })
        if number % 100 == 0:
            print(f"stage_one {number}", flush=True)
    viable = [row for row in stage_one if row["worst_drawdown"] >= -0.45]
    finalists = sorted(viable, key=lambda row: (row["worst_year"], row["worst_cagr"]),
                       reverse=True)[:12]
    stage_two = []
    for finalist in finalists:
        params = finalist["params"]
        bases = {}
        for universe_name, data in universes.items():
            sleeve_targets, sleeve_returns = built[universe_name]
            bases[universe_name] = meta_targets(
                sleeve_targets, sleeve_returns, params["days"] * 24,
                params["top_n"], params["rebalance"], params["mode"], params["cash"])
        for target_vol, max_gross in itertools.product(
            (0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7),
            (1.0, 1.25, 1.5, 1.75, 2.0),
        ):
            metrics = {}
            for universe_name, data in universes.items():
                targets = scale_portfolio(data, bases[universe_name], target_vol,
                                          max_gross, 1440, 24)
                metrics[universe_name] = metric(screen(data, targets, cost))
            stage_two.append({
                "params": {**params, "target_vol": target_vol, "max_gross": max_gross},
                "metrics": metrics,
                "worst_cagr": min(item["cagr"] for item in metrics.values()),
                "worst_drawdown": min(item["max_drawdown"] for item in metrics.values()),
                "worst_year": min(min(item["annual_returns"].values()) for item in metrics.values()),
            })
        print(f"stage_two {len(stage_two)}/{len(finalists) * 35}", flush=True)
    output = PROJECT / "reports" / "dual_universe_ensemble_search.json"
    output.write_text(json.dumps({"sleeves": SLEEVES, "stage_one": stage_one,
                                  "stage_two": stage_two}, indent=2) + "\n")
    passing = [row for row in stage_two if row["worst_cagr"] >= 0.5
               and row["worst_drawdown"] >= -0.35 and row["worst_year"] > 0]
    print(json.dumps({"tested": len(stage_one) + len(stage_two), "passing": len(passing),
                      "best": sorted(stage_two, key=lambda row: (
                          row["worst_year"], row["worst_cagr"]), reverse=True)[:20]}, indent=2))
