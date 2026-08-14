from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import FuturesData, load_data
from cryptoai_v13.metrics import slice_summary
from build_walk_forward import load_rows
from run_candidate_v13_multihorizon import build_candidate


def metric(result):
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    config = json.loads((PROJECT / "config" / "candidate_v13_multihorizon.json").read_text())
    rows = {row["index"]: row for row in load_rows()}
    data = load_data(PROJECT)
    cost = config["execution"]["base_cost_per_side"]
    base_targets = build_candidate(data, rows, config)
    results = []
    for removed in data.symbols:
        if removed == "BTCUSDT":
            targets = base_targets.copy()
            targets[removed] = 0.0
            result = screen(data, targets, cost)
            method = "BTC kept as regime feature but prohibited as a position"
        else:
            kept = tuple(symbol for symbol in data.symbols if symbol != removed)
            subset = FuturesData(
                {field: frame.loc[:, kept] for field, frame in data.frames.items()},
                data.funding.loc[:, kept], kept)
            targets = build_candidate(subset, rows, config)
            result = screen(subset, targets, cost)
            method = "full signal, rank, volatility and allocation recomputation"
        results.append({"removed": removed, "method": method, "metric": metric(result)})
        print(removed, results[-1]["metric"]["cagr"], flush=True)
    output = PROJECT / "reports" / "candidate_v13_multihorizon_universe_stress.json"
    output.write_text(json.dumps({"results": results}, indent=2) + "\n")
