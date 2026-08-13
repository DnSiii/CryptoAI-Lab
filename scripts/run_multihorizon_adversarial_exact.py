from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact
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
    targets = build_candidate(data, rows, config)
    scenarios = {}

    scenarios["extreme_cost"] = metric(exact(
        data, targets, config["execution"]["extreme_cost_per_side"]))
    print("extreme_cost", scenarios["extreme_cost"]["cagr"], flush=True)

    scenarios["delay_6h"] = metric(exact(
        data, targets.shift(5).fillna(0.0), config["execution"]["base_cost_per_side"]))
    print("delay_6h", scenarios["delay_6h"]["cagr"], flush=True)

    doubled_funding = FuturesData(data.frames, data.funding * 2.0, data.symbols)
    doubled_targets = build_candidate(doubled_funding, rows, config)
    scenarios["double_funding"] = metric(exact(
        doubled_funding, doubled_targets, config["execution"]["base_cost_per_side"]))
    print("double_funding", scenarios["double_funding"]["cagr"], flush=True)

    phase8_targets = build_candidate(data, rows, config, phase=8)
    scenarios["phase_8"] = metric(exact(
        data, phase8_targets, config["execution"]["base_cost_per_side"]))
    print("phase_8", scenarios["phase_8"]["cagr"], flush=True)

    output = PROJECT / "reports" / "candidate_v13_multihorizon_adversarial_exact.json"
    output.write_text(json.dumps({"scenarios": scenarios}, indent=2) + "\n")
